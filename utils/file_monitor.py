# -*- coding: utf-8 -*-
"""
文件变化监控模块
用于检测docx文件夹中文件的变化
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Set


class FileMonitor:
    """文件变化监控器"""
    
    def __init__(self, monitor_folder: str, cache_file: str = "data/file_cache.json"):
        self.monitor_folder = monitor_folder
        self.cache_file = cache_file
        self.supported_extensions = {'.docx', '.doc', '.txt'}
    
    def _get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _scan_folder(self) -> Dict[str, Dict]:
        """扫描文件夹，获取所有支持文件的信息"""
        file_info = {}
        
        if not os.path.exists(self.monitor_folder):
            return file_info
        
        for filename in os.listdir(self.monitor_folder):
            file_path = os.path.join(self.monitor_folder, filename)
            
            # 只处理文件，跳过文件夹
            if not os.path.isfile(file_path):
                continue
            
            # 检查文件扩展名
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.supported_extensions:
                continue
            
            # 获取文件信息
            try:
                stat = os.stat(file_path)
                file_info[filename] = {
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'hash': self._get_file_hash(file_path),
                    'path': file_path
                }
            except Exception:
                continue
        
        return file_info
    
    def _load_cache(self) -> Dict[str, Dict]:
        """加载缓存的文件信息"""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_cache(self, file_info: Dict[str, Dict]):
        """保存文件信息到缓存"""
        cache_data = {
            'last_scan': datetime.now().isoformat(),
            'files': file_info
        }
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def check_changes(self) -> tuple[bool, Dict]:
        """检查文件是否有变化
        
        Returns:
            tuple: (是否有变化, 变化详情)
        """
        current_files = self._scan_folder()
        cached_data = self._load_cache()
        cached_files = cached_data.get('files', {})
        
        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
            'total_files': len(current_files)
        }
        
        # 检查新增和修改的文件
        for filename, file_info in current_files.items():
            if filename not in cached_files:
                changes['added'].append(filename)
            elif (
                file_info['size'] != cached_files[filename].get('size') or
                file_info['mtime'] != cached_files[filename].get('mtime') or
                file_info['hash'] != cached_files[filename].get('hash')
            ):
                changes['modified'].append(filename)
        
        # 检查删除的文件
        for filename in cached_files:
            if filename not in current_files:
                changes['deleted'].append(filename)
        
        # 判断是否有变化
        has_changes = bool(
            changes['added'] or 
            changes['modified'] or 
            changes['deleted']
        )
        
        # 如果有变化或者是首次运行，更新缓存
        if has_changes or not cached_data:
            self._save_cache(current_files)
        
        return has_changes, changes
    
    def get_file_list(self) -> Set[str]:
        """获取当前监控文件夹中的所有支持文件列表"""
        file_info = self._scan_folder()
        return set(file_info.keys())
    
    def force_update_cache(self):
        """强制更新缓存（用于数据库构建完成后）"""
        current_files = self._scan_folder()
        self._save_cache(current_files)
        print(f"缓存已更新，监控 {len(current_files)} 个文件")