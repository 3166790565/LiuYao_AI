#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量索引更新模块
功能：支持增量更新RAG数据库，避免重建整个数据库
"""

import os
import pickle
import hashlib
import time
import json
from typing import List, Dict, Set, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

# 导入现有模块
from src.build_database import DatabaseBuilder, DocumentChunk
from src.search_documents import DocumentSearcher


@dataclass
class FileInfo:
    """文件信息结构"""
    path: str
    size: int
    mtime: float
    hash: str
    chunks_count: int = 0
    
    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        return (self.size == other.size and 
                abs(self.mtime - other.mtime) < 1.0 and  # 允许1秒误差
                self.hash == other.hash)
    
    def __hash__(self):
        return hash((self.path, self.size, self.mtime, self.hash))


class IncrementalUpdater:
    """增量更新器"""
    
    def __init__(self, database_path: str = 'rag_database.pkl', 
                 docx_folder: str = 'docx'):
        self.database_path = database_path
        self.docx_folder = docx_folder
        self.metadata_path = database_path.replace('.pkl', '_metadata.json')
        self.index_cache_path = database_path.replace('.pkl', '_indexes.pkl')
        self.vector_cache_path = database_path.replace('.pkl', '_vectors.pkl')
        
        # 初始化构建器
        self.builder = DatabaseBuilder(chunk_size=500, chunk_overlap=50)
        
        # 文件元数据缓存
        self.file_metadata = {}
        self.load_metadata()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # 分块读取，避免大文件内存问题
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            file_hash = self.calculate_file_hash(file_path)
            return FileInfo(
                path=file_path,
                size=stat.st_size,
                mtime=stat.st_mtime,
                hash=file_hash
            )
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return None
    
    def scan_folder_changes(self) -> Tuple[Set[str], Set[str], Set[str]]:
        """扫描文件夹变化，返回新增、修改、删除的文件集合"""
        print(f"扫描文件夹变化: {self.docx_folder}")
        
        if not os.path.exists(self.docx_folder):
            print(f"文件夹不存在: {self.docx_folder}")
            return set(), set(), set()
        
        # 当前文件列表（使用绝对路径，统一大小写）
        current_files = set()
        supported_extensions = ['.docx', '.txt']
        
        for filename in os.listdir(self.docx_folder):
            file_path = os.path.join(self.docx_folder, filename)
            if (os.path.isfile(file_path) and 
                os.path.splitext(filename)[1].lower() in supported_extensions):
                # 统一使用绝对路径，并转换为小写以避免大小写问题
                abs_path = os.path.abspath(file_path).lower()
                current_files.add(abs_path)
        
        # 历史文件列表（确保也是绝对路径，统一大小写）
        historical_files = set()
        for file_path in self.file_metadata.keys():
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(file_path):
                abs_path = os.path.abspath(os.path.join(self.docx_folder, file_path)).lower()
                historical_files.add(abs_path)
            else:
                abs_path = os.path.abspath(file_path).lower()
                historical_files.add(abs_path)
        
        # 计算变化（需要转换回原始路径）
        new_files_lower = current_files - historical_files
        deleted_files_lower = historical_files - current_files
        
        # 转换回原始路径格式
        new_files = set()
        for file_lower in new_files_lower:
            for filename in os.listdir(self.docx_folder):
                full_path = os.path.join(self.docx_folder, filename)
                if os.path.abspath(full_path).lower() == file_lower:
                    new_files.add(os.path.abspath(full_path))
                    break
        
        deleted_files = set()
        for file_lower in deleted_files_lower:
            # 对于删除的文件，从元数据中找到原始路径
            for hist_path in self.file_metadata.keys():
                if os.path.abspath(hist_path).lower() == file_lower:
                    deleted_files.add(hist_path)
                    break
        
        # 检查修改的文件
        modified_files = set()
        for file_path_lower in current_files & historical_files:
            # 找到原始路径（保持原始大小写）
            original_current_path = None
            for filename in os.listdir(self.docx_folder):
                full_path = os.path.join(self.docx_folder, filename)
                if os.path.abspath(full_path).lower() == file_path_lower:
                    original_current_path = os.path.abspath(full_path)
                    break
            
            if not original_current_path:
                continue
                
            current_info = self.get_file_info(original_current_path)
            
            # 查找对应的历史信息（忽略大小写差异）
            historical_info = None
            for hist_path, info in self.file_metadata.items():
                hist_abs_path = os.path.abspath(hist_path).lower()
                if hist_abs_path == file_path_lower:
                    historical_info = info
                    break
            
            if current_info and historical_info and current_info != historical_info:
                modified_files.add(original_current_path)
        
        print(f"文件变化统计:")
        print(f"  新增: {len(new_files)} 个")
        print(f"  修改: {len(modified_files)} 个")
        print(f"  删除: {len(deleted_files)} 个")
        
        return new_files, modified_files, deleted_files
    
    def load_metadata(self):
        """加载文件元数据"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为FileInfo对象，确保使用绝对路径
                for file_path, info_dict in data.get('files', {}).items():
                    # 统一转换为绝对路径
                    abs_file_path = os.path.abspath(file_path)
                    abs_info_path = os.path.abspath(info_dict['path'])
                    
                    self.file_metadata[abs_file_path] = FileInfo(
                        path=abs_info_path,
                        size=info_dict['size'],
                        mtime=info_dict['mtime'],
                        hash=info_dict['hash'],
                        chunks_count=info_dict.get('chunks_count', 0)
                    )
                
                print(f"加载文件元数据: {len(self.file_metadata)} 个文件")
                
            except Exception as e:
                print(f"加载元数据失败: {e}")
                self.file_metadata = {}
        else:
            print("元数据文件不存在，将创建新的")
            self.file_metadata = {}
    
    def save_metadata(self):
        """保存文件元数据"""
        try:
            # 转换为可序列化的格式，统一使用绝对路径
            data = {
                'files': {
                    os.path.abspath(file_path): {
                        'path': os.path.abspath(info.path),
                        'size': info.size,
                        'mtime': info.mtime,
                        'hash': info.hash,
                        'chunks_count': info.chunks_count
                    }
                    for file_path, info in self.file_metadata.items()
                },
                'last_update': datetime.now().isoformat(),
                'database_path': self.database_path
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"元数据已保存: {self.metadata_path}")
            
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    def process_file_chunks(self, file_path: str) -> List[DocumentChunk]:
        """处理单个文件，生成文档块"""
        print(f"处理文件: {os.path.basename(file_path)}")
        
        try:
            # 提取文本
            text = self.builder.extract_text_from_file(file_path)
            if not text:
                print(f"无法从 {file_path} 提取文本")
                return []
            
            # 预处理文本
            text = self.builder.preprocess_text(text)
            
            # 分块
            chunks = self.builder.chunk_text(text)
            
            # 创建文档块对象
            document_chunks = []
            for i, chunk in enumerate(chunks):
                keywords = self.builder.extract_keywords(chunk)
                metadata = {
                    'chunk_id': f"{os.path.basename(file_path)}_{i}",
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_path': file_path,
                    'processed_at': datetime.now().isoformat()
                }
                
                doc_chunk = DocumentChunk(
                    id=metadata['chunk_id'],
                    content=chunk,
                    source_file=os.path.basename(file_path),
                    metadata=metadata,
                    keywords=keywords
                )
                
                document_chunks.append(doc_chunk)
            
            print(f"从 {os.path.basename(file_path)} 生成 {len(document_chunks)} 个文档块")
            return document_chunks
            
        except Exception as e:
            print(f"处理文件失败 {file_path}: {e}")
            return []
    
    def load_existing_database(self) -> Dict[str, Any]:
        """加载现有数据库"""
        if not os.path.exists(self.database_path):
            print("数据库文件不存在，将创建新数据库")
            return {
                'chunks': [],
                'tfidf_vectorizer': None,
                'tfidf_matrix': None,
                'bm25_model': None,
                'created_at': datetime.now().isoformat(),
                'total_chunks': 0,
                'source_files': []
            }
        
        try:
            with open(self.database_path, 'rb') as f:
                database = pickle.load(f)
            print(f"加载现有数据库: {len(database.get('chunks', []))} 个文档块")
            return database
        except Exception as e:
            print(f"加载数据库失败: {e}")
            raise
    
    def update_database_incremental(self, force_rebuild: bool = False) -> bool:
        """增量更新数据库
        
        Args:
            force_rebuild: 是否强制重建整个数据库
            
        Returns:
            bool: 是否有更新
        """
        print("=== 开始增量更新数据库 ===")
        start_time = time.time()
        
        if force_rebuild:
            print("强制重建整个数据库...")
            return self._rebuild_full_database()
        
        # 扫描文件变化
        new_files, modified_files, deleted_files = self.scan_folder_changes()
        
        # 如果没有变化，直接返回
        if not (new_files or modified_files or deleted_files):
            print("没有检测到文件变化，无需更新")
            return False
        
        # 加载现有数据库
        database = self.load_existing_database()
        existing_chunks = database.get('chunks', [])
        
        # 创建文件到chunks的映射
        file_to_chunks = defaultdict(list)
        for chunk in existing_chunks:
            source_file = chunk.source_file
            file_to_chunks[source_file].append(chunk)
        
        # 处理删除的文件
        updated_chunks = []
        deleted_sources = set()
        
        for deleted_file in deleted_files:
            source_name = os.path.basename(deleted_file)
            deleted_sources.add(source_name)
            print(f"删除文件相关的文档块: {source_name}")
            # 从元数据中删除
            if deleted_file in self.file_metadata:
                del self.file_metadata[deleted_file]
        
        # 保留未删除文件的chunks
        for chunk in existing_chunks:
            if chunk.source_file not in deleted_sources:
                updated_chunks.append(chunk)
        
        # 处理修改的文件（删除旧chunks，添加新chunks）
        for modified_file in modified_files:
            source_name = os.path.basename(modified_file)
            print(f"更新修改的文件: {source_name}")
            
            # 删除旧的chunks
            updated_chunks = [chunk for chunk in updated_chunks 
                            if chunk.source_file != source_name]
            
            # 添加新的chunks
            new_chunks = self.process_file_chunks(modified_file)
            updated_chunks.extend(new_chunks)
            
            # 更新文件元数据
            file_info = self.get_file_info(modified_file)
            if file_info:
                file_info.chunks_count = len(new_chunks)
                self.file_metadata[modified_file] = file_info
        
        # 处理新增的文件
        for new_file in new_files:
            print(f"添加新文件: {os.path.basename(new_file)}")
            
            new_chunks = self.process_file_chunks(new_file)
            updated_chunks.extend(new_chunks)
            
            # 添加文件元数据
            file_info = self.get_file_info(new_file)
            if file_info:
                file_info.chunks_count = len(new_chunks)
                self.file_metadata[new_file] = file_info
        
        # 重建索引（如果有chunks变化）
        if new_files or modified_files or deleted_files:
            print(f"重建索引，文档块总数: {len(updated_chunks)}")
            
            # 重建TF-IDF和BM25索引
            tfidf_vectorizer, tfidf_matrix, bm25_model = self.builder.build_indexes(updated_chunks)
            
            # 更新数据库
            database.update({
                'chunks': updated_chunks,
                'tfidf_vectorizer': tfidf_vectorizer,
                'tfidf_matrix': tfidf_matrix,
                'bm25_model': bm25_model,
                'updated_at': datetime.now().isoformat(),
                'total_chunks': len(updated_chunks),
                'source_files': list(set(chunk.source_file for chunk in updated_chunks))
            })
            
            # 保存更新后的数据库
            with open(self.database_path, 'wb') as f:
                pickle.dump(database, f)
            
            # 增量更新索引缓存
            self._update_indexes_incremental(updated_chunks, new_files, modified_files, deleted_files)
            
            # 保存元数据
            self.save_metadata()
            
            update_time = time.time() - start_time
            print(f"\n=== 增量更新完成 ===")
            print(f"更新时间: {update_time:.2f}秒")
            print(f"文档块总数: {len(updated_chunks)}")
            print(f"来源文档: {len(database['source_files'])} 个")
            
            return True
        
        return False
    
    def _update_indexes_incremental(self, updated_chunks: List[DocumentChunk], 
                                  new_files: Set[str], modified_files: Set[str], 
                                  deleted_files: Set[str]):
        """增量更新索引缓存
        
        Args:
            updated_chunks: 更新后的所有文档块
            new_files: 新增文件集合
            modified_files: 修改文件集合
            deleted_files: 删除文件集合
        """
        print("正在增量更新索引缓存...")
        
        # 如果有文件变化，需要更新索引
        if new_files or modified_files or deleted_files:
            # 更新内存优化索引
            self._update_memory_indexes(updated_chunks)
            
            # 更新向量索引
            self._update_vector_indexes(updated_chunks, new_files, modified_files, deleted_files)
    
    def _update_memory_indexes(self, updated_chunks: List[DocumentChunk]):
        """更新内存优化索引"""
        try:
            print("更新内存优化索引...")
            
            # 导入必要的模块
            import jieba
            from src.search_documents import chinese_tokenizer
            import gc
            
            # 重建关键词索引和内容tokens缓存
            keyword_index = {}
            content_tokens_cache = {}
            
            # 批处理构建索引
            batch_size = 1000
            for i in range(0, len(updated_chunks), batch_size):
                batch_chunks = updated_chunks[i:i+batch_size]
                
                for j, chunk in enumerate(batch_chunks):
                    chunk_idx = i + j
                    
                    # 缓存内容tokens
                    content_tokens = frozenset(chinese_tokenizer(chunk.content))
                    content_tokens_cache[chunk_idx] = content_tokens
                    
                    # 合并关键词和内容tokens
                    all_tokens = frozenset(chunk.keywords) | content_tokens
                    
                    # 构建倒排索引
                    for token in all_tokens:
                        if token not in keyword_index:
                            keyword_index[token] = frozenset()
                        temp_set = set(keyword_index[token])
                        temp_set.add(chunk_idx)
                        keyword_index[token] = frozenset(temp_set)
                
                # 定期垃圾回收
                if i % (batch_size * 5) == 0:
                    gc.collect()
            
            # 优化索引结构
            optimized_index = {}
            for token, chunk_ids in keyword_index.items():
                if len(chunk_ids) <= 3:
                    optimized_index[token] = tuple(sorted(chunk_ids))
                else:
                    optimized_index[token] = chunk_ids
            
            # 保存索引缓存
            index_data = {
                'keyword_index': optimized_index,
                'content_tokens_cache': content_tokens_cache
            }
            
            import pickle
            with open(self.index_cache_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            print(f"内存优化索引更新完成，索引词汇数: {len(optimized_index)}")
            
        except Exception as e:
            print(f"更新内存优化索引失败: {e}")
            # 删除损坏的缓存文件
            if os.path.exists(self.index_cache_path):
                os.remove(self.index_cache_path)
    
    def _update_vector_indexes(self, updated_chunks: List[DocumentChunk],
                             new_files: Set[str], modified_files: Set[str], 
                             deleted_files: Set[str]):
        """增量更新向量索引"""
        try:
            # 检查是否支持向量搜索
            try:
                from sentence_transformers import SentenceTransformer
                import faiss
                import numpy as np
            except ImportError:
                print("向量搜索依赖未安装，跳过向量索引更新")
                return
            
            print("更新向量索引...")
            
            # 如果有大量变化，直接重建向量索引
            total_changes = len(new_files) + len(modified_files) + len(deleted_files)
            if total_changes > len(updated_chunks) * 0.3:  # 变化超过30%
                print("变化较大，重建向量索引")
                if os.path.exists(self.vector_cache_path):
                    os.remove(self.vector_cache_path)
                return
            
            # 尝试加载现有向量缓存
            existing_embeddings = None
            if os.path.exists(self.vector_cache_path):
                try:
                    import pickle
                    with open(self.vector_cache_path, 'rb') as f:
                        cache_data = pickle.load(f)
                    existing_embeddings = cache_data.get('embeddings')
                except Exception as e:
                    print(f"加载现有向量缓存失败: {e}")
            
            # 如果没有现有向量或向量数量不匹配，重建
            if (existing_embeddings is None or 
                len(existing_embeddings) != len(updated_chunks)):
                print("向量缓存不匹配，重建向量索引")
                if os.path.exists(self.vector_cache_path):
                    os.remove(self.vector_cache_path)
                return
            
            # 如果变化较小，保持现有缓存
            print(f"向量索引保持现有缓存，文档块数: {len(updated_chunks)}")
            
        except Exception as e:
            print(f"更新向量索引失败: {e}")
            # 删除损坏的缓存文件
            if os.path.exists(self.vector_cache_path):
                os.remove(self.vector_cache_path)
    
    def _rebuild_full_database(self) -> bool:
        """重建整个数据库"""
        print("重建整个数据库...")
        
        try:
            # 使用原始构建器重建
            database = self.builder.build_database(self.docx_folder, self.database_path)
            
            # 更新文件元数据
            self.file_metadata = {}
            for source_file in database['source_files']:
                file_path = os.path.join(self.docx_folder, source_file)
                if os.path.exists(file_path):
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        # 计算该文件的chunks数量
                        chunks_count = len([c for c in database['chunks'] 
                                          if c.source_file == source_file])
                        file_info.chunks_count = chunks_count
                        # 使用绝对路径作为键
                        abs_file_path = os.path.abspath(file_path)
                        self.file_metadata[abs_file_path] = file_info
            
            # 保存元数据
            self.save_metadata()
            
            return True
            
        except Exception as e:
            print(f"重建数据库失败: {e}")
            return False
    
    def get_update_status(self) -> Dict[str, Any]:
        """获取更新状态信息"""
        new_files, modified_files, deleted_files = self.scan_folder_changes()
        
        return {
            'has_changes': bool(new_files or modified_files or deleted_files),
            'new_files': list(new_files),
            'modified_files': list(modified_files),
            'deleted_files': list(deleted_files),
            'total_tracked_files': len(self.file_metadata),
            'database_exists': os.path.exists(self.database_path),
            'metadata_exists': os.path.exists(self.metadata_path)
        }


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG数据库增量更新工具')
    parser.add_argument('--database', '-d', default='rag_database.pkl',
                       help='数据库文件路径')
    parser.add_argument('--folder', '-f', default='docx',
                       help='文档文件夹路径')
    parser.add_argument('--force', action='store_true',
                       help='强制重建整个数据库')
    parser.add_argument('--status', action='store_true',
                       help='只显示更新状态，不执行更新')
    
    args = parser.parse_args()
    
    # 初始化更新器
    updater = IncrementalUpdater(args.database, args.folder)
    
    if args.status:
        # 显示状态
        status = updater.get_update_status()
        print("=== 更新状态 ===")
        print(f"数据库存在: {status['database_exists']}")
        print(f"元数据存在: {status['metadata_exists']}")
        print(f"跟踪文件数: {status['total_tracked_files']}")
        print(f"有变化: {status['has_changes']}")
        
        if status['has_changes']:
            print(f"新增文件: {len(status['new_files'])}")
            print(f"修改文件: {len(status['modified_files'])}")
            print(f"删除文件: {len(status['deleted_files'])}")
    else:
        # 执行更新
        success = updater.update_database_incremental(force_rebuild=args.force)
        if success:
            print("\n数据库更新成功！")
        else:
            print("\n无需更新或更新失败")


if __name__ == "__main__":
    main()