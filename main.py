#!/usr/bin/env python3
import sys
import os
import traceback
from gui import SixYaoApp
from utils.logger import setup_logger
from utils.file_monitor import FileMonitor
from config.constants import APP_NAME, APP_VERSION

# 设置日志
logger = setup_logger(__name__)

def check_and_build_database():
    """检查文件变化并增量更新数据库"""
    docx_folder = os.path.join(os.path.dirname(__file__), "docx")
    
    # 检查docx文件夹是否存在
    if not os.path.exists(docx_folder):
        logger.warning(f"docx文件夹不存在: {docx_folder}")
        return False
    
    # 初始化文件监控器
    monitor = FileMonitor(docx_folder)
    
    # 检查文件变化
    has_changes, changes = monitor.check_changes()
    
    if has_changes:
        logger.info("检测到docx文件夹有变化，开始增量更新RAG数据库...")
        print("\n=== 检测到文档文件变化 ===")
        print(f"新增文件: {len(changes['added'])} 个")
        print(f"修改文件: {len(changes['modified'])} 个")
        print(f"删除文件: {len(changes['deleted'])} 个")
        print(f"总文件数: {changes['total_files']} 个")
        print("\n正在增量更新RAG数据库，请稍候...")
        
        try:
            # 导入并运行增量更新
            from src.incremental_update import IncrementalUpdater
            
            updater = IncrementalUpdater("rag_database.pkl", docx_folder)
            
            # 执行增量更新
            updated = updater.update_database_incremental()
            
            if updated:
                # 更新完成后更新缓存
                monitor.force_update_cache()
                
                logger.info("RAG数据库增量更新完成")
                print("\n=== 数据库增量更新完成 ===")
                
                # 获取更新后的数据库信息
                import pickle
                try:
                    with open("rag_database.pkl", 'rb') as f:
                        database = pickle.load(f)
                    print(f"文档块总数: {database['total_chunks']}")
                    print(f"来源文档: {len(database['source_files'])} 个")
                except:
                    print("数据库信息获取完成")
                print("\n启动应用程序...\n")
                return True
            else:
                logger.info("数据库无需更新")
                print("\n数据库已是最新，直接启动应用程序...\n")
                return False
            
        except Exception as e:
            logger.error(f"增量更新数据库失败: {str(e)}")
            print(f"\n增量更新数据库失败: {str(e)}")
            print("尝试回退到全量重建...")
            
            try:
                # 回退到全量重建
                from src.build_database import DatabaseBuilder
                builder = DatabaseBuilder(chunk_size=500, chunk_overlap=50)
                database = builder.build_database(docx_folder, "rag_database.pkl")
                
                # 构建完成后更新缓存
                monitor.force_update_cache()
                
                logger.info("全量重建数据库完成")
                print("\n=== 全量重建数据库完成 ===")
                print(f"文档块总数: {database['total_chunks']}")
                print(f"来源文档: {len(database['source_files'])} 个")
                print("\n启动应用程序...\n")
                return True
                
            except Exception as fallback_e:
                logger.error(f"全量重建也失败: {str(fallback_e)}")
                print(f"\n全量重建也失败: {str(fallback_e)}")
                print("将继续启动应用程序...\n")
                return False
    else:
        logger.info("docx文件夹无变化，跳过数据库构建")
        print("文档文件无变化，直接启动应用程序...\n")
        return False

def main():
    """主函数"""
    try:
        logger.info(f"启动{APP_NAME} v{APP_VERSION}")
        
        # 直接启动应用程序，数据库初始化在后台进行
        app = SixYaoApp()
        
        # 在后台线程中进行数据库初始化
        import threading
        init_thread = threading.Thread(target=app.background_initialization, daemon=True)
        init_thread.start()
        
        app.mainloop()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\n应用程序启动失败: {str(e)}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()