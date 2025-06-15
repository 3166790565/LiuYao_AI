#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档检索脚本
功能：从构建好的数据库中进行智能检索，支持多种检索方法
"""

import os
import pickle
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from collections import defaultdict, OrderedDict, Counter
import re
import gc
import psutil
import time
import math

# 基础文本处理
from jieba import analyse

# 传统机器学习
# 学习排序相关功能已移除

# 向量化搜索相关
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    print("警告: sentence-transformers 或 faiss 未安装，向量化搜索功能不可用")
    print("安装命令: pip install sentence-transformers faiss-cpu")

# 导入DocumentChunk类
from src.build_database import DocumentChunk

class SimpleBM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        # 使用numpy数组减少内存占用
        self.doc_len = np.array([len(doc) for doc in corpus], dtype=np.uint16)
        self.avgdl = float(np.mean(self.doc_len))
        self.doc_freqs = []
        self.idf = {}
        self.doc_count = len(corpus)
        
        # 内存优化的词频计算
        word_doc_count = {}
        for doc_idx, doc in enumerate(corpus):
            # 使用Counter提高效率，然后转换为普通dict节省内存
            frequencies = dict(Counter(doc))
            # 只保留频率大于1的词，减少内存占用
            frequencies = {word: freq for word, freq in frequencies.items() if freq > 0}
            self.doc_freqs.append(frequencies)
            
            # 统计包含每个词的文档数
            for word in frequencies:
                word_doc_count[word] = word_doc_count.get(word, 0) + 1
            
        # 内存优化的IDF计算
        for word, containing_docs in word_doc_count.items():
            # 使用float32减少内存占用
            idf_value = math.log((self.doc_count - containing_docs + 0.5) / (containing_docs + 0.5) + 1.0)
            self.idf[word] = np.float32(idf_value)
    
    def get_scores(self, query):
        scores = []
        for i, doc in enumerate(self.corpus):
            # 添加边界检查
            if i >= len(self.doc_freqs) or i >= len(self.doc_len):
                scores.append(0.0)
                continue
                
            score = 0
            doc_len = self.doc_len[i]
            for word in query:
                if word in self.doc_freqs[i]:
                    freq = self.doc_freqs[i][word]
                    idf = self.idf.get(word, 0)
                    score += idf * (freq * (self.k1 + 1)) / (freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
            scores.append(score)
        return scores


def chinese_tokenizer(text):
    """中文分词器"""
    return list(jieba.cut(text))


class DocumentSearcher:
    """文档检索器"""
    
    def __init__(self, database_path: str = 'rag_database.pkl', auto_update: bool = True):
        """初始化文档搜索器
        
        Args:
            database_path: 数据库文件路径
            auto_update: 是否启用自动增量更新
        """
        self.database_path = database_path
        self.index_cache_path = database_path.replace('.pkl', '_indexes.pkl')
        self.auto_update = auto_update
        self.chunks = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.bm25_model = None
        self.database_info = {}
        
        # 增量更新相关
        self._last_check_time = 0
        self._check_interval = 30  # 检查间隔（秒）
        self._database_mtime = 0
        
        # 内存优化的查询缓存
        self.query_cache = OrderedDict()
        self.cache_size = 300  # 减少缓存大小以节省内存
        self._cache_compression = True  # 启用缓存压缩
        
        # 添加优化索引
        self._keyword_index = {}
        self._content_tokens_cache = {}
        
        # 向量化搜索相关
        self.vector_model = None
        self.vector_index = None
        self.vector_embeddings = None
        self.vector_cache_path = database_path.replace('.pkl', '_vectors.pkl')
        
        # Learning to Rank功能已完全移除
        
        # 初始化jieba
        jieba.initialize()
        
        # 加载数据库
        self.load_database()
        
        # 加载或构建优化索引
        self._load_or_build_indexes()
        
        # 初始化向量化搜索
        if VECTOR_SEARCH_AVAILABLE:
            self._init_vector_search()
        
    
    def _load_or_build_indexes(self):
        """加载或构建优化索引"""
        # 检查索引缓存是否存在且比数据库新
        if (os.path.exists(self.index_cache_path) and 
            os.path.getmtime(self.index_cache_path) >= os.path.getmtime(self.database_path)):
            
            print("正在加载已缓存的优化索引...")
            start_time = time.time()
            
            try:
                with open(self.index_cache_path, 'rb') as f:
                    index_data = pickle.load(f)
                
                self._keyword_index = index_data['keyword_index']
                self._content_tokens_cache = index_data['content_tokens_cache']
                
                load_time = time.time() - start_time
                print(f"索引加载完成:")
                print(f"  - 索引词汇数: {len(self._keyword_index)}")
                print(f"  - 加载时间: {load_time:.2f}秒")
                print(f"  - 缓存tokens数: {len(self._content_tokens_cache)}")
                return
                
            except Exception as e:
                print(f"索引缓存加载失败: {e}，将重新构建索引")
        
        # 构建新索引
        self._build_optimized_indexes()
        
        # 保存索引到缓存
        self._save_indexes()
    
    def _build_optimized_indexes(self):
        """构建优化的索引结构 - 内存优化版本"""
        print("正在构建内存优化索引...")
        start_time = time.time()
        
        # 获取初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 使用更紧凑的数据结构
        self._keyword_index = {}  # 直接使用dict，避免defaultdict开销
        self._content_tokens_cache = {}  # 使用紧凑的tokens缓存
        
        # 预分配词汇表，减少重复计算
        vocab_set = set()
        
        batch_size = 1000  # 批处理大小
        for i in range(0, len(self.chunks), batch_size):
            batch_chunks = self.chunks[i:i+batch_size]
            
            for j, chunk in enumerate(batch_chunks):
                chunk_idx = i + j
                
                # 缓存内容tokens - 使用frozenset减少内存
                content_tokens = frozenset(chinese_tokenizer(chunk.content))
                self._content_tokens_cache[chunk_idx] = content_tokens
                
                # 合并关键词和内容tokens - 使用frozenset
                all_tokens = frozenset(chunk.keywords) | content_tokens
                vocab_set.update(all_tokens)
                
                # 构建倒排索引 - 使用frozenset替代set
                for token in all_tokens:
                    if token not in self._keyword_index:
                        self._keyword_index[token] = frozenset()
                    # 临时转换为set进行添加，然后转回frozenset
                    temp_set = set(self._keyword_index[token])
                    temp_set.add(chunk_idx)
                    self._keyword_index[token] = frozenset(temp_set)
            
            # 每处理一批后进行垃圾回收
            if i % (batch_size * 5) == 0:
                gc.collect()
        
        # 优化索引结构 - 将小的frozenset转换为tuple以节省更多内存
        optimized_index = {}
        for token, chunk_ids in self._keyword_index.items():
            if len(chunk_ids) <= 3:  # 小集合使用tuple
                optimized_index[token] = tuple(sorted(chunk_ids))
            else:  # 大集合保持frozenset
                optimized_index[token] = chunk_ids
        self._keyword_index = optimized_index
        
        # 最终垃圾回收
        gc.collect()
        
        # 计算性能指标
        build_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"内存优化索引构建完成:")
        print(f"  - 索引词汇数: {len(self._keyword_index)}")
        print(f"  - 构建时间: {build_time:.2f}秒")
        print(f"  - 内存增加: {memory_increase:.1f}MB")
        print(f"  - 内存优化: 使用frozenset和tuple减少内存占用")
    
    def _save_indexes(self):
        """保存索引到缓存文件"""
        try:
            print("正在保存索引缓存...")
            start_time = time.time()
            
            # 转换defaultdict为普通dict以便序列化
            keyword_index_dict = {k: v for k, v in self._keyword_index.items()}
            
            index_data = {
                'keyword_index': keyword_index_dict,
                'content_tokens_cache': self._content_tokens_cache,
                'created_at': time.time(),
                'database_path': self.database_path
            }
            
            with open(self.index_cache_path, 'wb') as f:
                pickle.dump(index_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            save_time = time.time() - start_time
            file_size = os.path.getsize(self.index_cache_path) / 1024 / 1024  # MB
            
            print(f"索引缓存保存完成:")
            print(f"  - 保存时间: {save_time:.2f}秒")
            print(f"  - 文件大小: {file_size:.1f}MB")
            print(f"  - 缓存路径: {self.index_cache_path}")
            
        except Exception as e:
            print(f"索引缓存保存失败: {e}")
    
    def rebuild_indexes(self):
        """强制重建索引（用于调试或更新）"""
        print("强制重建索引...")
        
        # 删除旧的缓存文件
        if os.path.exists(self.index_cache_path):
            os.remove(self.index_cache_path)
            print(f"已删除旧索引缓存: {self.index_cache_path}")
        
        # 重新构建
        self._build_optimized_indexes()
        self._save_indexes()
    
    def _check_database_update(self) -> bool:
        """检查数据库是否需要更新
        
        Returns:
            bool: 是否需要重新加载数据库
        """
        if not self.auto_update:
            return False
        
        current_time = time.time()
        
        # 检查时间间隔
        if current_time - self._last_check_time < self._check_interval:
            return False
        
        self._last_check_time = current_time
        
        # 检查数据库文件修改时间
        if os.path.exists(self.database_path):
            current_mtime = os.path.getmtime(self.database_path)
            if current_mtime > self._database_mtime:
                print(f"检测到数据库更新，重新加载...")
                return True
        
        return False
    
    def _trigger_incremental_update(self) -> bool:
        """触发增量更新
        
        Returns:
            bool: 是否成功更新
        """
        try:
            # 动态导入避免循环依赖
            from src.incremental_update import IncrementalUpdater
            
            print("触发增量更新...")
            updater = IncrementalUpdater(self.database_path)
            
            # 检查是否有变化
            status = updater.get_update_status()
            if status['has_changes']:
                success = updater.update_database_incremental()
                if success:
                    print("增量更新完成")
                    return True
                else:
                    print("增量更新失败")
            else:
                print("没有检测到文件变化")
            
            return False
            
        except Exception as e:
            print(f"增量更新失败: {e}")
            return False
    
    def reload_database(self):
        """重新加载数据库"""
        print("重新加载数据库...")
        
        # 清理缓存
        self.query_cache.clear()
        self._keyword_index.clear()
        self._content_tokens_cache.clear()
        
        # 重新加载
        self.load_database()
        self._load_or_build_indexes()
        
        # 重新初始化向量搜索
        if VECTOR_SEARCH_AVAILABLE:
            self._init_vector_search()
        
        print("数据库重新加载完成")
    
    def load_database(self):
        """加载数据库 - 优化版本"""
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.database_path}")
        
        print("正在加载RAG数据库...")
        import time
        start_time = time.time()
        
        try:
            # 记录数据库修改时间
            self._database_mtime = os.path.getmtime(self.database_path)
            
            with open(self.database_path, 'rb') as f:
                database = pickle.load(f)
            
            self.chunks = database['chunks']
            
            # 检查是否需要重建TF-IDF和BM25模型
            if 'tfidf_vectorizer' in database and 'tfidf_matrix' in database:
                self.tfidf_vectorizer = database['tfidf_vectorizer']
                self.tfidf_matrix = database['tfidf_matrix']
            else:
                # 构建内存优化的TF-IDF矩阵
                print("构建内存优化的TF-IDF矩阵...")
                documents = [chunk.content for chunk in self.chunks]
                # 使用更严格的参数减少特征数量
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,  # 限制最大特征数
                    min_df=2,  # 增加最小文档频率
                    max_df=0.8,  # 降低最大文档频率
                    ngram_range=(1, 2),
                    stop_words=None
                )
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
                # 转换为更紧凑的CSR格式并消除零元素
                tfidf_matrix.eliminate_zeros()
                self.tfidf_matrix = tfidf_matrix.tocsr()
            
            if 'bm25_model' in database:
                self.bm25_model = database['bm25_model']
            else:
                # 构建内存优化的BM25模型
                print("构建内存优化的BM25模型...")
                tokenized_docs = [chinese_tokenizer(chunk.content) for chunk in self.chunks]
                self.bm25_model = SimpleBM25(tokenized_docs)
            
            # 保存数据库信息
            self.database_info = {
                'created_at': database.get('created_at', 'Unknown'),
                'updated_at': database.get('updated_at', database.get('created_at', 'Unknown')),
                'total_chunks': database.get('total_chunks', len(self.chunks)),
                'source_files': database.get('source_files', [])
            }
            
            load_time = time.time() - start_time
            print(f"数据库加载完成，共{len(self.chunks)}个文档块，耗时{load_time:.2f}秒")
            
        except Exception as e:
            print(f"数据库加载失败: {e}")
            raise
    
    def expand_query(self, query: str) -> List[str]:
        """查询扩展 - 优化版本，减少不必要的计算"""
        if len(query) < 2:  # 查询太短，不进行扩展
            return [query]
            
        expanded_queries = [query]  # 包含原始查询
        
        # 精简的六爻核心同义词词典
        synonyms = {
            '财运': ['财富', '金钱'],
            '事业': ['工作', '职业'],
            '感情': ['爱情', '婚姻'],
            '健康': ['身体', '疾病'],
            '学业': ['考试', '学习'],
            '出行': ['旅行', '远行'],
            '世爻': ['自己'],
            '应爻': ['对方'],
            '用神': ['所求之神']
        }
        
        # 只对包含关键词的查询进行扩展
        for word, syns in synonyms.items():
            if word in query:
                # 只取第一个同义词，减少计算量
                expanded_queries.append(query.replace(word, syns[0]))
                break  # 只扩展第一个匹配的词
        
        return expanded_queries[:3]  # 最多3个扩展查询，减少计算量
    
    def tfidf_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """TF-IDF检索 - 优化版本"""
        try:
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # 使用稀疏矩阵的点积计算，比cosine_similarity更快
            similarities = (query_vector * self.tfidf_matrix.T).toarray().flatten()
            
            # 只保留非零相似度的索引，避免排序所有元素
            nonzero_indices = np.nonzero(similarities)[0]
            if len(nonzero_indices) == 0:
                return []
            
            # 只对非零元素排序
            nonzero_similarities = similarities[nonzero_indices]
            sorted_indices = np.argsort(nonzero_similarities)[::-1][:top_k]
            
            results = [(nonzero_indices[idx], nonzero_similarities[idx]) 
                      for idx in sorted_indices 
                      if 0 <= nonzero_indices[idx] < len(self.chunks)]
            
            return results
        except Exception as e:
            print(f"TF-IDF搜索出错: {e}")
            return []
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """BM25检索 - 优化版本"""
        try:
            query_tokens = chinese_tokenizer(query)
            if not query_tokens:
                return []
            
            scores = self.bm25_model.get_scores(query_tokens)
            
            # 只保留正分数的索引
            positive_indices = np.where(scores > 0)[0]
            if len(positive_indices) == 0:
                return []
            
            # 只对正分数排序
            positive_scores = scores[positive_indices]
            sorted_indices = np.argsort(positive_scores)[::-1][:top_k]
            
            results = [(positive_indices[idx], positive_scores[idx]) 
                      for idx in sorted_indices 
                      if 0 <= positive_indices[idx] < len(self.chunks)]
            
            return results
        except Exception as e:
            print(f"BM25搜索出错: {e}")
            return []
    
    def keyword_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """关键词匹配检索 - 内存优化版本使用紧凑索引"""
        query_keywords = frozenset(chinese_tokenizer(query))  # 使用frozenset
        if not query_keywords:
            return []
        
        # 使用倒排索引快速找到候选文档 - 适配新数据结构
        candidate_chunks = set()
        for keyword in query_keywords:
            if keyword in self._keyword_index:
                chunk_ids = self._keyword_index[keyword]
                # 适配tuple和frozenset两种数据结构
                if isinstance(chunk_ids, tuple):
                    candidate_chunks.update(chunk_ids)
                else:  # frozenset
                    candidate_chunks.update(chunk_ids)
        
        if not candidate_chunks:
            return []
        
        results = []
        for i in candidate_chunks:
            if i >= len(self.chunks):  # 边界检查
                continue
                
            chunk = self.chunks[i]
            
            # 使用缓存的tokens - 适配frozenset
            content_tokens = self._content_tokens_cache.get(i, frozenset())
            chunk_keywords = frozenset(chunk.keywords) if chunk.keywords else frozenset()
            all_chunk_keywords = chunk_keywords | content_tokens  # 使用|操作符
            
            # 计算交集
            intersection = query_keywords & all_chunk_keywords  # 使用&操作符
            if intersection:
                # 计算匹配分数
                score = len(intersection) / len(query_keywords)
                # 加权：关键词匹配更重要
                keyword_match = query_keywords & chunk_keywords
                if keyword_match:
                    score += len(keyword_match) * 0.5
                
                results.append((i, score))
        
        # 排序并返回top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def hybrid_search(self, query: str, top_k: int = 10, 
                     tfidf_weight: float = 0.3, 
                     bm25_weight: float = 0.4, 
                     keyword_weight: float = 0.3) -> List[Tuple[int, float]]:
        """混合检索 - 优化版本"""
        # 限制中间结果数量以提升性能
        intermediate_k = min(top_k * 2, 30)
        
        # 获取各种检索结果
        tfidf_results = dict(self.tfidf_search(query, intermediate_k))
        bm25_results = dict(self.bm25_search(query, intermediate_k))
        keyword_results = dict(self.keyword_search(query, intermediate_k))
        
        # 合并结果 - 只处理有分数的索引
        all_indices = set()
        if tfidf_results:
            all_indices.update(tfidf_results.keys())
        if bm25_results:
            all_indices.update(bm25_results.keys())
        if keyword_results:
            all_indices.update(keyword_results.keys())
        
        if not all_indices:
            return []
        
        # 预计算归一化因子
        max_tfidf = max(tfidf_results.values()) if tfidf_results else 1.0
        max_bm25 = max(bm25_results.values()) if bm25_results else 1.0
        max_keyword = max(keyword_results.values()) if keyword_results else 1.0
        
        hybrid_scores = {}
        for idx in all_indices:
            # 归一化分数
            tfidf_score = tfidf_results.get(idx, 0) / max_tfidf if max_tfidf > 0 else 0
            bm25_score = bm25_results.get(idx, 0) / max_bm25 if max_bm25 > 0 else 0
            keyword_score = keyword_results.get(idx, 0) / max_keyword if max_keyword > 0 else 0
            
            # 计算混合分数
            hybrid_score = (
                tfidf_weight * tfidf_score +
                bm25_weight * bm25_score +
                keyword_weight * keyword_score
            )
            
            if hybrid_score > 0:  # 只保留有分数的结果
                hybrid_scores[idx] = hybrid_score
        
        # 排序并返回top_k
        sorted_results = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def search(self, query: str, 
              search_method: str = 'hybrid',
              top_k: int = 5,
              similarity_threshold: float = 0.01,
              use_query_expansion: bool = True) -> List[Dict]:
        """主搜索接口 - 优化版本"""
        
        # 检查数据库是否需要更新
        if self._check_database_update():
            # 尝试增量更新
            if self._trigger_incremental_update():
                self.reload_database()
        
        # 输入验证和早期退出
        if not query or not query.strip():
            return []
        
        query = query.strip()
        
        # 生成缓存键
        cache_key = f"{query}_{search_method}_{top_k}_{similarity_threshold}_{use_query_expansion}"
        
        # 检查缓存
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # 查询扩展 - 只在必要时进行
        queries = [query]
        if use_query_expansion and len(query) > 2:
            expanded = self.expand_query(query)
            if len(expanded) > 1:  # 只有真正扩展了才使用
                queries = expanded
        
        all_results = {}
        
        # 对每个查询执行搜索
        for q in queries:
            if search_method == 'tfidf':
                results = self.tfidf_search(q, min(top_k * 2, 20))  # 限制中间结果数量
            elif search_method == 'bm25':
                results = self.bm25_search(q, min(top_k * 2, 20))
            elif search_method == 'keyword':
                results = self.keyword_search(q, min(top_k * 2, 20))
            elif search_method == 'hybrid':
                results = self.hybrid_search(q, min(top_k * 2, 20))
            elif search_method == 'vector':
                results = self.vector_search(q, min(top_k * 2, 20))
            elif search_method == 'semantic_hybrid':
                results = self.semantic_hybrid_search(q, min(top_k * 2, 20))
            else:
                raise ValueError(f"不支持的搜索方法: {search_method}")
            
            # 合并结果，添加边界检查
            for idx, score in results:
                # 确保索引在有效范围内
                if 0 <= idx < len(self.chunks):
                    if idx in all_results:
                        all_results[idx] = max(all_results[idx], score)
                    else:
                        all_results[idx] = score
            
            # 早期退出：如果已经有足够的高质量结果
            if len(all_results) >= top_k * 3:
                break
        
        # 过滤低分结果
        filtered_results = [(idx, score) for idx, score in all_results.items() 
                          if score >= similarity_threshold]
        
        # 排序
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        # 格式化输出
        formatted_results = []
        for idx, score in filtered_results[:top_k]:
            # 添加边界检查，防止索引越界
            if idx < 0 or idx >= len(self.chunks):
                continue
                
            chunk = self.chunks[idx]
            result = {
                'chunk_id': idx,
                'content': chunk.content,
                'source_file': chunk.source_file,
                'similarity_score': score,
                'keywords': chunk.keywords[:3] if chunk.keywords else [],  # 进一步减少关键词数量
                'metadata': {}
            }
            formatted_results.append(result)
        
        # Learning to Rank功能已移除，直接使用原始排序结果
        
        # 内存优化的缓存管理
        if len(self.query_cache) >= self.cache_size:
            # 删除最旧的30%缓存，减少频繁清理
            keys_to_remove = list(self.query_cache.keys())[:self.cache_size // 3]
            for key in keys_to_remove:
                del self.query_cache[key]
        
        # 压缩缓存：只保存必要信息
        if self._cache_compression:
            compressed_results = []
            for result in formatted_results:
                compressed_result = {
                    'chunk_id': result['chunk_id'],
                    'content': result['content'][:200] + '...' if len(result['content']) > 200 else result['content'],  # 截断长内容
                    'source_file': result['source_file'],
                    'similarity_score': round(result['similarity_score'], 4),  # 减少精度
                    'keywords': result['keywords'][:2]  # 只保留前2个关键词
                }
                compressed_results.append(compressed_result)
            self.query_cache[cache_key] = compressed_results
        else:
            self.query_cache[cache_key] = formatted_results
        
        return formatted_results
    
    def get_memory_usage(self):
        """获取当前内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # 物理内存
            'vms_mb': memory_info.vms / 1024 / 1024,  # 虚拟内存
            'percent': process.memory_percent()  # 内存使用百分比
        }
    
    def _init_vector_search(self):
        """初始化向量化搜索"""
        try:
            print("正在初始化向量化搜索...")
            
            # 使用中文优化的sentence-transformer模型
            model_name = 'paraphrase-multilingual-MiniLM-L12-v2'  # 支持中文的轻量级模型
            self.vector_model = SentenceTransformer(model_name)
            
            # 检查是否有缓存的向量
            if os.path.exists(self.vector_cache_path):
                print("正在加载缓存的向量索引...")
                self._load_vector_cache()
            else:
                print("正在构建向量索引...")
                self._build_vector_index()
                
            print(f"向量化搜索初始化完成，索引大小: {len(self.chunks)}")
            
        except Exception as e:
            print(f"向量化搜索初始化失败: {e}")
            self.vector_model = None
            self.vector_index = None
    
    def _build_vector_index(self):
        """构建向量索引"""
        if not self.chunks:
            return
            
        print(f"正在为 {len(self.chunks)} 个文档块生成向量...")
        start_time = time.time()
        
        # 准备文本数据
        texts = [chunk.content for chunk in self.chunks]
        
        # 批量生成向量，避免内存溢出
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.vector_model.encode(batch_texts, 
                                                       convert_to_numpy=True,
                                                       show_progress_bar=True)
            embeddings.append(batch_embeddings)
            
        # 合并所有向量
        self.vector_embeddings = np.vstack(embeddings).astype(np.float32)
        
        # 构建FAISS索引
        dimension = self.vector_embeddings.shape[1]
        self.vector_index = faiss.IndexFlatIP(dimension)  # 使用内积相似度
        
        # 标准化向量以使用余弦相似度
        faiss.normalize_L2(self.vector_embeddings)
        self.vector_index.add(self.vector_embeddings)
        
        build_time = time.time() - start_time
        print(f"向量索引构建完成，耗时: {build_time:.2f}秒")
        
        # 保存向量缓存
        self._save_vector_cache()
    
    def _save_vector_cache(self):
        """保存向量缓存"""
        try:
            cache_data = {
                'embeddings': self.vector_embeddings,
                'model_name': self.vector_model.get_sentence_embedding_dimension(),
                'chunk_count': len(self.chunks)
            }
            
            with open(self.vector_cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"向量缓存已保存到: {self.vector_cache_path}")
            
        except Exception as e:
            print(f"保存向量缓存失败: {e}")
    
    def _load_vector_cache(self):
        """加载向量缓存"""
        try:
            with open(self.vector_cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 验证缓存是否匹配当前数据
            if cache_data['chunk_count'] != len(self.chunks):
                print("向量缓存与当前数据不匹配，重新构建索引")
                self._build_vector_index()
                return
            
            self.vector_embeddings = cache_data['embeddings']
            
            # 重建FAISS索引
            dimension = self.vector_embeddings.shape[1]
            self.vector_index = faiss.IndexFlatIP(dimension)
            self.vector_index.add(self.vector_embeddings)
            
            print("向量缓存加载成功")
            
        except Exception as e:
            print(f"加载向量缓存失败: {e}，重新构建索引")
            self._build_vector_index()
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """向量化语义搜索"""
        if not self.vector_model or not self.vector_index:
            return []
        
        try:
            # 生成查询向量
            query_embedding = self.vector_model.encode([query], convert_to_numpy=True)
            query_embedding = query_embedding.astype(np.float32)
            
            # 标准化查询向量
            faiss.normalize_L2(query_embedding)
            
            # 搜索最相似的向量
            scores, indices = self.vector_index.search(query_embedding, top_k)
            
            # 返回结果
            results = []
            for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
                if idx != -1:  # FAISS返回-1表示无效索引
                    results.append((int(idx), float(score)))
            
            return results
             
        except Exception as e:
            print(f"向量搜索失败: {e}")
            return []
    
    def semantic_hybrid_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """语义混合搜索：结合向量搜索和传统搜索"""
        # 如果向量搜索不可用，回退到传统混合搜索
        if not self.vector_model or not self.vector_index:
            return self.hybrid_search(query, top_k)
        
        try:
            # 获取向量搜索结果
            vector_results = self.vector_search(query, top_k * 2)
            vector_scores = {idx: score for idx, score in vector_results}
            
            # 获取传统混合搜索结果
            hybrid_results = self.hybrid_search(query, top_k * 2)
            hybrid_scores = {idx: score for idx, score in hybrid_results}
            
            # 合并和重新评分
            combined_scores = {}
            all_indices = set(vector_scores.keys()) | set(hybrid_scores.keys())
            
            for idx in all_indices:
                # 标准化分数到0-1范围
                vector_score = vector_scores.get(idx, 0.0)
                hybrid_score = hybrid_scores.get(idx, 0.0)
                
                # 向量搜索权重0.6，传统搜索权重0.4
                # 向量搜索更适合语义理解，传统搜索更适合关键词匹配
                combined_score = 0.6 * vector_score + 0.4 * hybrid_score
                
                if combined_score > 0:
                    combined_scores[idx] = combined_score
            
            # 排序并返回结果
            sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_results[:top_k]
            
        except Exception as e:
            print(f"语义混合搜索失败: {e}，回退到传统混合搜索")
            return self.hybrid_search(query, top_k)
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {
            'total_chunks': len(self.chunks),
            'source_files': self.database_info['source_files'],
            'created_at': self.database_info['created_at']
        }
        
        # 按来源文档统计
        source_stats = {}
        for chunk in self.chunks:
            source = chunk.source_file
            if source not in source_stats:
                source_stats[source] = {
                    'chunk_count': 0,
                    'total_length': 0,
                    'avg_keywords': 0
                }
            
            source_stats[source]['chunk_count'] += 1
            source_stats[source]['total_length'] += len(chunk.content)
            if chunk.keywords:
                source_stats[source]['avg_keywords'] += len(chunk.keywords)
        
        # 计算平均值
        for source, stat in source_stats.items():
            if stat['chunk_count'] > 0:
                stat['avg_length'] = stat['total_length'] // stat['chunk_count']
                stat['avg_keywords'] = stat['avg_keywords'] // stat['chunk_count']
        
        stats['source_stats'] = source_stats
        return stats
    
    # Learning to Rank相关方法已移除
    
    # Learning to Rank相关方法已全部移除


def main():
    """主函数 - 交互式检索"""
    database_path = "rag_database.pkl"
    
    try:
        # 初始化检索器
        searcher = DocumentSearcher(database_path)
        
        # 显示数据库信息
        stats = searcher.get_database_stats()
        print("\n=== 数据库信息 ===")
        print(f"创建时间: {stats['created_at']}")
        print(f"文档块总数: {stats['total_chunks']}")
        print(f"来源文档: {len(stats['source_files'])} 个")
        
        print("\n=== 各文档统计 ===")
        for source, stat in stats['source_stats'].items():
            print(f"{source}:")
            print(f"  - 文档块数: {stat['chunk_count']}")
            print(f"  - 平均长度: {stat['avg_length']} 字符")
            print(f"  - 平均关键词: {stat['avg_keywords']} 个")
        
        # 根据向量搜索可用性设置默认方法
        if VECTOR_SEARCH_AVAILABLE and searcher.vector_model:
            default_method = 'semantic_hybrid'
            method_desc = "SEMANTIC_HYBRID方法"
        else:
            default_method = 'hybrid'
            method_desc = "HYBRID方法"
        
        print(f"\n=== 六爻知识检索系统 ({method_desc}) ===")
        print("输入查询内容，输入 'quit' 或 'exit' 退出")
        
        # 根据向量搜索可用性显示不同的方法列表
        if VECTOR_SEARCH_AVAILABLE and searcher.vector_model:
            print("支持的搜索方法: tfidf, bm25, keyword, hybrid, vector, semantic_hybrid")
            print("  - semantic_hybrid: 语义+传统混合搜索 (默认推荐)")
            print("  - vector: 纯向量语义搜索")
        else:
            print("支持的搜索方法: tfidf, bm25, keyword, hybrid")
            print("  注意: 向量搜索功能不可用，请安装 sentence-transformers 和 faiss-cpu")
        
        print("输入 'method:方法名' 可切换搜索方法，如 'method:semantic_hybrid'")
        print("输入 'help' 或 '帮助' 查看详细使用说明")
        print("=" * 60)
        
        current_method = default_method
        
        while True:
            try:
                user_input = input(f"\n[{current_method}] 请输入您的问题: ").strip()
                
                # 检查退出条件
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("感谢使用！")
                    break
                
                # 检查方法切换
                if user_input.startswith('method:'):
                    new_method = user_input.split(':', 1)[1].strip().lower()
                    
                    # 基础方法
                    valid_methods = ['tfidf', 'bm25', 'keyword', 'hybrid']
                    
                    # 如果向量搜索可用，添加向量方法
                    if VECTOR_SEARCH_AVAILABLE and searcher.vector_model:
                        valid_methods.extend(['vector', 'semantic_hybrid'])
                    
                    if new_method in valid_methods:
                        current_method = new_method
                        print(f"已切换到 {current_method} 方法")
                        
                        # 为向量方法提供额外说明
                        if new_method == 'vector':
                            print("  使用纯向量语义搜索，适合理解查询意图")
                        elif new_method == 'semantic_hybrid':
                            print("  使用语义+传统混合搜索，平衡语义理解和关键词匹配")
                    else:
                        available_methods = ', '.join(valid_methods)
                        print(f"不支持的方法，可用方法: {available_methods}")
                    continue
                
                elif user_input.startswith('方法'):
                    # 切换搜索方法
                    parts = user_input.split()
                    if len(parts) > 1:
                        new_method = parts[1].lower()
                        valid_methods = ['tfidf', 'bm25', 'hybrid']
                        if VECTOR_SEARCH_AVAILABLE:
                            valid_methods.extend(['vector', 'semantic_hybrid'])
                        
                        if new_method in valid_methods:
                            current_method = new_method
                            print(f"\n已切换到 {current_method} 搜索方法")
                            
                            # 显示方法描述
                            if current_method == 'vector':
                                print("向量搜索：使用语义相似度进行搜索，适合概念性查询")
                            elif current_method == 'semantic_hybrid':
                                print("语义混合搜索：结合关键词匹配和语义相似度，平衡精确性和语义理解")
                        else:
                            print(f"\n无效的搜索方法。可用方法: {', '.join(valid_methods)}")
                    else:
                        valid_methods = ['tfidf', 'bm25', 'hybrid']
                        if VECTOR_SEARCH_AVAILABLE:
                            valid_methods.extend(['vector', 'semantic_hybrid'])
                        print(f"\n当前搜索方法: {current_method}")
                        print(f"可用方法: {', '.join(valid_methods)}")
                        print("使用格式: 方法 <方法名>")
                    continue
                
                elif user_input.lower() in ['help', '帮助', 'h']:
                    print("\n=== 使用帮助 ===")
                    print("1. 直接输入查询内容进行搜索")
                    print("2. 输入 '方法 <方法名>' 切换搜索方法")
                    print("3. 输入 'info' 查看数据库信息")
                    print("4. 输入 'clear' 清空缓存")
                    print("5. 输入 '更新' 或 'update' 手动检查文档更新")
                    print("6. 输入 'quit' 或 'exit' 退出程序")
                    print("7. 输入 'help' 显示此帮助信息")
                    
                    valid_methods = ['tfidf', 'bm25', 'hybrid']
                    if VECTOR_SEARCH_AVAILABLE:
                        valid_methods.extend(['vector', 'semantic_hybrid'])
                    print(f"\n可用搜索方法: {', '.join(valid_methods)}")
                    
                    if VECTOR_SEARCH_AVAILABLE:
                        print("\n向量搜索方法说明:")
                        print("- vector: 纯向量搜索，基于语义相似度")
                        print("- semantic_hybrid: 语义混合搜索，结合关键词和语义")
                    
                    if searcher.auto_update:
                        print(f"\n实时更新: 已启用 (检查间隔: {searcher._check_interval}秒)")
                    else:
                        print("\n实时更新: 已禁用")
                    
                    if LTR_AVAILABLE:
                        print("\n=== 学习排序命令 ===")
                        print("- ltr:info - 查看学习排序模型信息")
                        print("- ltr:train [model_type] - 训练模型 (random_forest/gradient_boosting/linear)")
                        print("- ltr:sample - 添加训练样本")
                    continue
                
                elif user_input.lower() in ['更新', 'update']:
                    # 手动触发增量更新
                    print("\n正在检查文档更新...")
                    if searcher._trigger_incremental_update():
                        searcher.reload_database()
                        print("数据库更新完成")
                    else:
                        print("没有检测到文档变化")
                    continue
                
                # Learning to Rank命令已移除
                
                if not user_input:
                    print("请输入有效的查询内容")
                    continue
                
                print(f"\n正在使用 {current_method.upper()} 方法搜索: {user_input}")
                print("-" * 50)
                
                # 执行搜索
                results = searcher.search(
                    query=user_input,
                    search_method=current_method,
                    top_k=3,
                    similarity_threshold=0.01,
                    use_query_expansion=True
                )
                
                if not results:
                    print("未找到相关内容，请尝试其他关键词")
                    continue
                
                # 显示搜索结果
                for i, result in enumerate(results, 1):
                    print(f"\n【结果 {i}】")
                    print(f"来源文档: {result['source_file']}")
                    print(f"相似度: {result['similarity_score']:.4f}")
                    print(f"内容: {result['content'][:200]}{'...' if len(result['content']) > 200 else ''}")
                    if result['keywords']:
                        print(f"关键词: {', '.join(result['keywords'])}")
                    print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n程序被用户中断")
                break
            except Exception as e:
                import traceback
                print(f"搜索过程中出现错误: {e}")
                print("详细错误信息:")
                traceback.print_exc()
                continue
    
    except FileNotFoundError:
        print(f"错误: 数据库文件 {database_path} 不存在")
        print("请先运行 src/build_database.py 构建数据库")
    except Exception as e:
        print(f"系统初始化错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()