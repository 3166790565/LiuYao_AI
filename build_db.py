#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库构建脚本
通过模块导入的方式避免pickle序列化时的__main__问题
"""

import sys
import os

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入构建器
from src.build_database import DatabaseBuilder

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