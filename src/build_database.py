#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建RAG数据库脚本
功能：扫描docx文件夹中的所有文档，构建统一的检索数据库
"""

import math
import os
import pickle
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

# 基础文本处理
import jieba
import numpy as np
from jieba import analyse
# 传统机器学习
from sklearn.feature_extraction.text import TfidfVectorizer


def chinese_tokenizer(text):
    """中文分词器"""
    return list(jieba.cut(text))


@dataclass
class DocumentChunk:
    """文档块数据结构"""
    id: str
    content: str
    source_file: str  # 来源文档文件名
    metadata: Dict
    tfidf_vector: np.ndarray = None
    keywords: List[str] = None


class SimpleBM25:
    """简化的BM25实现"""
    
    def __init__(self, k1=1.2, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.avgdl = 0
    
    def fit(self, corpus):
        """训练BM25模型"""
        self.corpus = corpus
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0
        
        # 计算词频
        df = {}
        for doc in corpus:
            for word in set(doc):
                df[word] = df.get(word, 0) + 1
        
        # 计算IDF
        for word, freq in df.items():
            self.idf[word] = math.log((len(corpus) - freq + 0.5) / (freq + 0.5))
    
    def get_scores(self, query):
        """计算查询的BM25分数"""
        scores = []
        for i, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_len[i]
            
            for word in query:
                if word in doc:
                    tf = doc.count(word)
                    idf = self.idf.get(word, 0)
                    score += idf * (tf * (self.k1 + 1)) / (
                        tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                    )
            
            scores.append(score)
        
        return np.array(scores)


class DatabaseBuilder:
    """数据库构建器"""
    
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化jieba
        jieba.initialize()
        
        print("数据库构建器初始化完成")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """从文件提取文本"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 处理.txt文件
        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        return f.read()
                except Exception as e:
                    print(f"读取txt文件失败 {file_path}: {e}")
                    return ""
            except Exception as e:
                print(f"读取txt文件失败 {file_path}: {e}")
                return ""
        
        # 处理Word文档
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            print("python-docx未安装，尝试其他方法")
        except Exception as e:
            print(f"docx读取失败 {file_path}: {e}")
        
        try:
            import docx2txt
            return docx2txt.process(file_path)
        except ImportError:
            print("docx2txt未安装")
        except Exception as e:
            print(f"docx2txt读取失败 {file_path}: {e}")
        
        print(f"无法读取文档 {file_path}")
        return ""
    
    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\u4e00-\u9fff\w\s。，！？；：]', '', text)
        text = text.strip()
        return text

    def chunk_text(self, text: str) -> List[str]:
        """文本分块"""
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                sub_sentences = re.split(r'[，、；：]', sentence)
                sub_sentences = [s.strip() for s in sub_sentences if s.strip()]
                
                for sub_sentence in sub_sentences:
                    if len(current_chunk) + len(sub_sentence) <= self.chunk_size:
                        current_chunk += sub_sentence + "，"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        if len(sub_sentence) > self.chunk_size:
                            for i in range(0, len(sub_sentence), self.chunk_size):
                                chunk_part = sub_sentence[i:i+self.chunk_size]
                                chunks.append(chunk_part)
                            current_chunk = ""
                        else:
                            current_chunk = sub_sentence + "，"
            else:
                if len(current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        try:
            keywords = analyse.extract_tags(text, topK=top_k, withWeight=False)
            return keywords
        except Exception:
            words = list(jieba.cut(text))
            word_freq = Counter(words)
            stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '上', '也', '很'}
            filtered_words = [(word, freq) for word, freq in word_freq.items() 
                            if len(word) > 1 and word not in stopwords]
            return [word for word, _ in sorted(filtered_words, key=lambda x: x[1], reverse=True)[:top_k]]
    
    def scan_documents(self, docx_folder: str) -> List[DocumentChunk]:
        """扫描文档文件夹，处理所有文档"""
        all_chunks = []
        chunk_id_counter = 0
        
        # 支持的文件扩展名
        supported_extensions = ['.docx', '.txt', '.csv']
        
        # 扫描文件夹
        for filename in os.listdir(docx_folder):
            file_path = os.path.join(docx_folder, filename)
            
            # 检查是否为支持的文件类型
            if not os.path.isfile(file_path):
                continue
            
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in supported_extensions:
                print(f"跳过不支持的文件类型: {filename}")
                continue
            
            print(f"\n正在处理文档: {filename}")
            
            # 提取文本
            text = self.extract_text_from_file(file_path)
            if not text:
                print(f"无法从 {filename} 提取文本，跳过")
                continue
            
            # 预处理文本
            text = self.preprocess_text(text)
            
            # 分块
            chunks = self.chunk_text(text)
            print(f"从 {filename} 生成 {len(chunks)} 个文档块")
            
            # 创建文档块对象
            for i, chunk in enumerate(chunks):
                keywords = self.extract_keywords(chunk)
                metadata = {
                    'chunk_id': chunk_id_counter,
                    'source': filename,
                    'chunk_index': i,
                    'created_at': datetime.now().isoformat(),
                    'length': len(chunk),
                    'keyword_count': len(keywords)
                }
                
                doc_chunk = DocumentChunk(
                    id=f"chunk_{chunk_id_counter}",
                    content=chunk,
                    source_file=filename,
                    metadata=metadata,
                    keywords=keywords
                )
                
                all_chunks.append(doc_chunk)
                chunk_id_counter += 1
        
        return all_chunks
    
    def build_indexes(self, chunks: List[DocumentChunk]):
        """构建索引"""
        print("\n正在构建TF-IDF索引...")
        contents = [chunk.content for chunk in chunks]
        
        # TF-IDF索引
        num_docs = len(contents)
        min_df = 1 if num_docs < 10 else 2
        max_df = 1.0 if num_docs < 5 else 0.95
        
        tfidf_vectorizer = TfidfVectorizer(
            tokenizer=chinese_tokenizer,
            lowercase=False,
            min_df=min_df,
            max_df=max_df,
            max_features=5000,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = tfidf_vectorizer.fit_transform(contents)
        
        # 保存TF-IDF向量到chunk对象
        for i, chunk in enumerate(chunks):
            chunk.tfidf_vector = tfidf_matrix[i].toarray().flatten()
        
        print("正在构建BM25索引...")
        # BM25索引
        tokenized_contents = [chinese_tokenizer(content) for content in contents]
        bm25_model = SimpleBM25()
        bm25_model.fit(tokenized_contents)
        
        return tfidf_vectorizer, tfidf_matrix, bm25_model
    
    def build_database(self, docx_folder: str, output_path: str = "rag_database.pkl"):
        """构建完整数据库"""
        print(f"开始构建数据库，扫描文件夹: {docx_folder}")
        
        # 检查文件夹是否存在
        if not os.path.exists(docx_folder):
            raise ValueError(f"文件夹不存在: {docx_folder}")
        
        # 扫描并处理所有文档
        chunks = self.scan_documents(docx_folder)
        
        if not chunks:
            raise ValueError("没有找到可处理的文档或所有文档处理失败")
        
        print(f"\n总共生成 {len(chunks)} 个文档块")
        
        # 构建索引
        tfidf_vectorizer, tfidf_matrix, bm25_model = self.build_indexes(chunks)
        
        # 收集文件元数据
        file_metadata = {}
        for chunk in chunks:
            if chunk.source_file not in file_metadata:
                file_path = os.path.join(docx_folder, chunk.source_file)
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    file_metadata[chunk.source_file] = {
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'chunks_count': 0
                    }
            file_metadata[chunk.source_file]['chunks_count'] += 1
        
        # 保存数据库
        current_time = datetime.now().isoformat()
        database = {
            'chunks': chunks,
            'tfidf_vectorizer': tfidf_vectorizer,
            'tfidf_matrix': tfidf_matrix,
            'bm25_model': bm25_model,
            'created_at': current_time,
            'updated_at': current_time,
            'total_chunks': len(chunks),
            'source_files': list(set(chunk.source_file for chunk in chunks)),
            'file_metadata': file_metadata,
            'docs_folder': docx_folder
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(database, f)
        
        print(f"\n数据库构建完成！")
        print(f"保存路径: {output_path}")
        print(f"文档块总数: {len(chunks)}")
        print(f"来源文档: {len(database['source_files'])} 个")
        for source in database['source_files']:
            source_chunks = [c for c in chunks if c.source_file == source]
            print(f"  - {source}: {len(source_chunks)} 个块")
        
        return database


def main():
    """主函数"""
    # 配置路径
    docx_folder = "docx"  # 文档文件夹
    database_path = "rag_database.pkl"  # 数据库保存路径
    
    try:
        # 初始化构建器
        builder = DatabaseBuilder(chunk_size=500, chunk_overlap=50)
        
        # 构建数据库
        database = builder.build_database(docx_folder, database_path)
        
        print("\n=== 数据库构建成功 ===")
        print("现在可以运行 src/search_documents.py 进行检索")
        
    except Exception as e:
        print(f"构建数据库时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()