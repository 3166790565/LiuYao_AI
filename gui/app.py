# gui/app.py

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import logging
from datetime import datetime
import os
import sys
import importlib.util

# 导入项目模块
from config import APP_NAME, RESOURCES_DIR
from config.ui_config import UI_SETTINGS, get_ui_settings, update_ui_settings, toggle_theme_mode
from utils.config_manager import config_manager
from config.languages import t
from utils.logger import setup_logger
from utils.animation import fade_in, slide_in
from utils.resources import load_image, load_svg_icon
from utils.ui_components import IOSMessageBox
from utils.history import HistoryManager
from .frames import (
    HeaderFrame,
    InputFrame,
    NotebookFrame,
    StatusFrame,
    FooterFrame,
    SettingsFrame
)


# 设置日志记录器
logger = setup_logger(__name__)

class SixYaoApp(ctk.CTk):
    """主应用程序类，使用customtkinter实现iOS风格界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化状态变量
        self.database_built = False
        self.initialization_complete = False
        self.initialization_progress = 0
        
        # 获取UI设置
        self.ui_settings = get_ui_settings()
        
        # 设置应用程序外观
        ctk.set_appearance_mode(self.ui_settings["appearance_mode"])  # 明亮或暗黑模式
        ctk.set_default_color_theme("green")  # 使用customtkinter内置的green主题
        
        # 配置窗口
        self.title(APP_NAME)
        
        # 设置窗口大小和位置
        saved_geometry = config_manager.get_window_geometry()
        if saved_geometry:
            self.geometry(saved_geometry)
            logger.info(f"已恢复保存的窗口几何信息: {saved_geometry}")
        else:
            self.geometry(f"{self.ui_settings['window_width']}x{self.ui_settings['window_height']}")
            # 如果设置了窗口居中显示，则居中显示窗口
            if self.ui_settings["window_centered"]:
                self.center_window()
        
        self.minsize(800, 600)  # 设置最小窗口大小
        
        # 尝试设置图标
        try:
            icon_path = os.path.join(RESOURCES_DIR, "icons", "app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"无法加载应用图标: {e}")
        
        # 初始化变量
        self.current_tab = 0
        self.chat_messages = []
        self.analysis_result = ""
        self.hexagram_info = ""
        
        # 初始化历史记录管理器
        self.history_manager = HistoryManager()
        
        # 初始化RAG检索器（将在后台初始化）
        self.rag_searcher = None
        
        # 创建UI组件
        self.create_widgets()
        
        # 创建菜单栏 - 已移除
        # self.create_menu()
        
        # 应用主题颜色
        self.apply_theme_colors()
        
        # 绑定事件
        self.bind("<Configure>", self.on_resize)
        
        # 设置窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化时禁用功能按钮
        self.disable_ui_during_initialization()
        
        # 显示初始化状态
        self.update_initialization_status("正在初始化应用程序...", 0)
        
        # 应用启动动画
        if self.ui_settings["animation"]["enabled"]:
            self.after(100, self.apply_startup_animations)
    
    def background_initialization(self):
        """后台初始化方法"""
        try:
            # 步骤1: 检查文件变化
            self.update_initialization_status("检查文件变化...", 10)
            
            # 导入必要的模块
            from utils.file_monitor import FileMonitor
            
            docx_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docx")
            
            # 检查docx文件夹是否存在
            if not os.path.exists(docx_folder):
                logger.warning(f"docx文件夹不存在: {docx_folder}")
                self.update_initialization_status("docx文件夹不存在", 100)
                self.enable_ui_after_initialization()
                return
            
            # 初始化文件监控器
            monitor = FileMonitor(docx_folder)
            
            # 检查文件变化
            has_changes, changes = monitor.check_changes()
            
            if has_changes:
                self.update_initialization_status("检测到文件变化，正在更新数据库...", 20)
                
                try:
                    # 导入并运行增量更新
                    from src.incremental_update import IncrementalUpdater
                    
                    updater = IncrementalUpdater("rag_database.pkl", docx_folder)
                    
                    # 执行增量更新
                    self.update_initialization_status("正在增量更新数据库...", 40)
                    updated = updater.update_database_incremental()
                    
                    if updated:
                        # 更新完成后更新缓存
                        monitor.force_update_cache()
                        self.database_built = True
                        self.update_initialization_status("数据库更新完成", 70)
                        logger.info("RAG数据库增量更新完成")
                    else:
                        self.update_initialization_status("数据库无需更新", 70)
                        logger.info("数据库无需更新")
                        
                except Exception as e:
                    logger.error(f"增量更新数据库失败: {str(e)}")
                    self.update_initialization_status(f"数据库更新失败: {str(e)}", 70)
                    
                    try:
                        # 回退到全量重建
                        self.update_initialization_status("尝试全量重建数据库...", 50)
                        from src.build_database import DatabaseBuilder
                        builder = DatabaseBuilder(chunk_size=500, chunk_overlap=50)
                        database = builder.build_database(docx_folder, "rag_database.pkl")
                        
                        # 构建完成后更新缓存
                        monitor.force_update_cache()
                        self.database_built = True
                        self.update_initialization_status("全量重建数据库完成", 70)
                        logger.info("全量重建数据库完成")
                        
                    except Exception as fallback_e:
                        logger.error(f"全量重建也失败: {str(fallback_e)}")
                        self.update_initialization_status(f"数据库重建失败: {str(fallback_e)}", 70)
            else:
                self.update_initialization_status("文档文件无变化", 70)
                logger.info("docx文件夹无变化，跳过数据库构建")
            
            # 步骤2: 初始化RAG检索器
            self.update_initialization_status("初始化RAG检索器...", 80)
            self.init_rag_searcher()
            
            # 步骤3: 完成初始化
            self.update_initialization_status("初始化完成", 100)
            self.initialization_complete = True
            
            # 启用UI功能
            self.enable_ui_after_initialization()
            
            # 显示数据库状态提示
            if self.database_built:
                self.after(500, lambda: self.show_database_status("RAG数据库已更新，解卦准确性已提升"))
            
        except Exception as e:
            logger.error(f"后台初始化失败: {str(e)}")
            self.update_initialization_status(f"初始化失败: {str(e)}", 100)
            self.enable_ui_after_initialization()
    
    def init_rag_searcher(self):
        """初始化RAG检索器"""
        try:
            # 检查RAG数据库是否存在
            rag_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag_database.pkl")
            if os.path.exists(rag_db_path):
                # 动态导入search_documents模块
                search_documents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "search_documents.py")
                if os.path.exists(search_documents_path):
                    spec = importlib.util.spec_from_file_location("search_documents", search_documents_path)
                    search_documents = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(search_documents)
                    
                    # 创建DocumentSearcher实例
                    self.rag_searcher = search_documents.DocumentSearcher(rag_db_path)
                    logger.info("RAG检索器初始化成功")
                else:
                    logger.warning("src/search_documents.py文件不存在")
            else:
                logger.info("RAG数据库不存在，跳过RAG检索器初始化")
        except Exception as e:
            logger.error(f"初始化RAG检索器时出错: {e}")
            self.rag_searcher = None
    
    def update_initialization_status(self, status, progress):
        """更新初始化状态和进度"""
        self.initialization_progress = progress
        
        # 在主线程中更新UI
        def update_ui():
            if hasattr(self, 'status_frame'):
                self.status_frame.update_status(status)
                self.status_frame.update_progress(progress / 100.0)
        
        self.after(0, update_ui)
    
    def disable_ui_during_initialization(self):
        """初始化期间禁用UI功能"""
        def disable_ui():
            if hasattr(self, 'input_frame'):
                # 禁用输入框架的按钮
                if hasattr(self.input_frame, 'analyze_button'):
                    self.input_frame.analyze_button.configure(state="disabled")
                if hasattr(self.input_frame, 'clear_button'):
                    self.input_frame.clear_button.configure(state="disabled")
        
        self.after(100, disable_ui)
    
    def enable_ui_after_initialization(self):
        """初始化完成后启用UI功能"""
        def enable_ui():
            if hasattr(self, 'input_frame'):
                # 启用输入框架的按钮
                if hasattr(self.input_frame, 'analyze_button'):
                    self.input_frame.analyze_button.configure(state="normal")
                if hasattr(self.input_frame, 'clear_button'):
                    self.input_frame.clear_button.configure(state="normal")
            
            # 重置状态栏
            if hasattr(self, 'status_frame'):
                self.status_frame.reset()
        
        self.after(0, enable_ui)
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()  # 更新窗口信息
        width = int(self.ui_settings["window_width"])
        height = int(self.ui_settings["window_height"])
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """创建所有UI组件"""
        # 创建主布局 - 使用网格布局以便更好地响应窗口大小变化
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # 让笔记本区域可以扩展
        
        # 1. 头部区域 - 标题和副标题
        self.header_frame = HeaderFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # 2. 输入区域 - 问题输入、起卦方式和模型选择
        self.input_frame = InputFrame(self, command=self.start_analysis)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 15))
        
        # 3. 笔记本区域 - 卦象信息、解读结果和对话
        self.notebook_frame = NotebookFrame(self, on_tab_changed=self.on_tab_changed)
        self.notebook_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(15, 15))
        
        # 4. 状态区域 - 进度条和状态文本
        self.status_frame = StatusFrame(self)
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 5))
        
        # 5. 底部区域 - 版本信息和功能标签
        self.footer_frame = FooterFrame(self)
        self.footer_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        
        # 6. 初始化时更新模型列表
        self.after(100, self.update_model_list)
    
    # def create_menu(self):
    #     """创建菜单栏"""
    #     try:
    #         # 创建菜单栏
    #         menubar = tk.Menu(self)
    #         self.configure(menu=menubar)
    #         
    #         # 文件菜单
    #         file_menu = tk.Menu(menubar, tearoff=0)
    #         menubar.add_cascade(label=t("menu_file"), menu=file_menu)
    #         file_menu.add_command(label=t("btn_export"), command=self.show_export_dialog)
    #         file_menu.add_separator()
    #         file_menu.add_command(label=t("menu_exit"), command=self.quit)
    #         
    #         # 视图菜单
    #         view_menu = tk.Menu(menubar, tearoff=0)
    #         menubar.add_cascade(label=t("menu_view"), menu=view_menu)
    #         view_menu.add_command(label=t("menu_theme"), command=self.toggle_theme)
    #         
    #         # 工具菜单
    #         tools_menu = tk.Menu(menubar, tearoff=0)
    #         menubar.add_cascade(label=t("menu_tools"), menu=tools_menu)
    # 
    #         tools_menu.add_command(label=t("menu_settings"), command=self.show_settings)
    #         
    #         # 帮助菜单
    #         help_menu = tk.Menu(menubar, tearoff=0)
    #         menubar.add_cascade(label=t("menu_help"), menu=help_menu)
    #         help_menu.add_command(label=t("help_usage"), command=self.show_help)
    #         help_menu.add_command(label=t("menu_about"), command=self.show_about)
    #         
    #         self.menubar = menubar
    #         
    #     except Exception as e:
    #         logger.error(f"创建菜单栏时出错: {e}")
    
    def apply_theme_colors(self):
        """应用主题颜色到UI组件 - 优化性能版本"""
        colors = self.ui_settings["colors"]
        
        # 暂时禁用屏幕更新以减少闪烁
        self.update_idletasks()
        
        # 设置窗口背景色
        self.configure(fg_color=colors["bg_color"])
        
        # 批量更新所有子组件的主题
        try:
            # 创建要更新的组件列表
            frames_to_update = []
            
            # 收集所有需要更新的框架
            for frame_name in ['header_frame', 'input_frame', 'notebook_frame', 'status_frame', 'footer_frame', 'settings_frame']:
                if hasattr(self, frame_name):
                    frame = getattr(self, frame_name)
                    if hasattr(frame, 'update_theme'):
                        frames_to_update.append(frame)
            
            # 一次性更新所有框架
            for frame in frames_to_update:
                frame.update_theme()
            
            # 强制更新UI
            self.update_idletasks()
                
            logger.info(f"主题已切换到: {self.ui_settings['appearance_mode']} (优化版本)")
        except Exception as e:
            logger.error(f"应用主题颜色时出错: {e}")
    
    def toggle_theme(self):
        """切换主题模式（明亮/暗黑）- 优化性能"""
        try:
            # 显示加载状态
            self.status_frame.update_status("正在切换主题...") if hasattr(self, 'status_frame') else None
            self.update_idletasks()  # 立即更新UI
            
            # 取消之前的主题切换任务（如果有）
            if hasattr(self, '_theme_job') and self._theme_job:
                self.after_cancel(self._theme_job)
            
            # 延迟执行主题切换，减少频繁切换导致的闪烁
            self._theme_job = self.after(50, self._apply_theme_change)
        except Exception as e:
            logger.error(f"切换主题时出错: {e}")
    
    def _apply_theme_change(self):
        """实际应用主题变更 - 内部方法"""
        try:
            # 重置主题切换任务标识
            self._theme_job = None
            
            # 更新UI设置
            self.ui_settings = toggle_theme_mode()
            
            # 更新应用程序外观
            ctk.set_appearance_mode(self.ui_settings["appearance_mode"])
            
            # 禁用窗口更新以减少闪烁
            self.update_idletasks()
            
            # 应用主题颜色
            self.apply_theme_colors()
            
            # 更新设置窗口的主题（如果存在）
            if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                # 更新设置窗口的外观模式
                self.settings_window._set_appearance_mode(self.ui_settings["appearance_mode"])
                
                # 更新设置框架的主题
                if hasattr(self, 'settings_frame'):
                    self.settings_frame.update_theme()
                    
                logger.info(f"设置窗口主题已更新为: {self.ui_settings['appearance_mode']}")
            
            # 更新主窗口标签页中的设置框架主题
            if hasattr(self, 'notebook_frame') and hasattr(self.notebook_frame, 'settings_frame'):
                self.notebook_frame.settings_frame.update_theme()
                logger.info(f"设置标签页主题模式已设置为: {self.ui_settings['appearance_mode']}")
            
            # 恢复状态
            if hasattr(self, 'status_frame'):
                self.status_frame.update_status("就绪")
        except Exception as e:
            logger.error(f"应用主题变更时出错: {e}")
    
    def apply_startup_animations(self):
        """应用启动动画效果 - 高性能版本"""
        try:
            # 设置动画持续时间 - 极短时间以减少性能影响
            duration = 50  # 毫秒 - 大幅减少动画时长
            
            # 同时显示所有组件，不使用延迟，减少闪烁
            self.update_idletasks()  # 先更新布局
            
            # 一次性显示所有组件
            self.header_frame.update_idletasks()
            self.input_frame.update_idletasks()
            self.notebook_frame.update_idletasks()
            self.status_frame.update_idletasks()
            self.footer_frame.update_idletasks()
            
            logger.info("应用启动动画效果完成 - 高性能模式")
        except Exception as e:
            logger.error(f"应用启动动画效果时出错: {e}", exc_info=True)
    
    def on_resize(self, event):
        """窗口大小变化时的处理 - 添加防抖动逻辑"""
        # 只处理来自主窗口的调整事件
        if event.widget == self:
            # 取消之前的调整计划（如果有）
            if hasattr(self, '_resize_job') and self._resize_job:
                self.after_cancel(self._resize_job)
            
            # 设置新的调整计划，延迟100毫秒执行
            self._resize_job = self.after(100, self._apply_resize)
    
    def _apply_resize(self):
        """实际应用窗口大小调整后的处理"""
        try:
            # 重置调整任务标识
            self._resize_job = None
            
            # 更新布局，避免闪烁
            self.update_idletasks()
        except Exception as e:
            logger.error(f"应用窗口大小调整时出错: {e}")
    
    def on_tab_changed(self, event):
        """选项卡切换事件处理"""
        self.current_tab = self.notebook_frame.get_current_tab()
    
    def start_analysis(self):
        """开始分析按钮点击事件处理"""
        # 获取输入信息
        question = self.input_frame.get_question()
        divination_method = self.input_frame.get_divination_method()
        model = self.input_frame.get_model()
        hexagram_content = self.notebook_frame.get_hexagram_content()
        
        # 验证输入
        if not question:
            # 请输入问题的提示，记录到日志
            logger.warning("请输入您的问题！")
            return
        
        if not hexagram_content:
            # 请输入占卜信息的提示，记录到日志
            logger.warning(f"请输入{divination_method}信息！")
            # 切换到卦象信息选项卡
            self.notebook_frame.select_tab(0)
            return
        
        # 禁用按钮，防止重复提交
        self.input_frame.set_buttons_state("disabled")
        
        # 清空之前的结果
        self.notebook_frame.clear_result()
        
        # 更新状态
        self.status_frame.update_status("分析中...")
        self.status_frame.update_progress(0.1)
        
        # 切换到结果选项卡
        self.notebook_frame.select_tab(1)
        
        # 在新线程中执行分析，避免界面卡死
        threading.Thread(
            target=self.perform_analysis, 
            args=(question, hexagram_content, divination_method, model), 
            daemon=True
        ).start()
    
    def perform_analysis(self, question, hexagram_content, divination_method, model):
        """执行分析过程"""
        try:
            # 导入API模块
            import sys
            import os
            import importlib.util
            
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            api_file_path = os.path.join(project_root, 'api.py')
            
            # 使用已初始化的RAG检索器
            rag_references = set()  # 用于收集参考文件名
            
            # 动态导入api.py模块
            spec = importlib.util.spec_from_file_location("api_module", api_file_path)
            api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_module)
            
            AI = api_module.AI
            parse_ai_response = api_module.parse_ai_response
            
            # 更新UI状态为分析中
            # 合并初始状态更新
            def update_initial_status():
                self.status_frame.update_status("正在分析需求...")
                self.status_frame.update_progress(0.1)
            
            self.update_ui(update_initial_status)
            
            # 导入提示词模块
            prompts_file_path = os.path.join(project_root, 'src', 'prompts.py')
            prompts_spec = importlib.util.spec_from_file_location("prompts_module", prompts_file_path)
            prompts_module = importlib.util.module_from_spec(prompts_spec)
            prompts_spec.loader.exec_module(prompts_module)
            
            # 根据起卦方式选择提示词模板
            if divination_method == "六爻占卜":
                analysis_prompt = prompts_module.SIXYAO_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.SIXYAO_INTERPRETATION_PROMPT
            elif divination_method == "奇门遁甲":
                analysis_prompt = prompts_module.QIMEN_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.QIMEN_INTERPRETATION_PROMPT
            elif divination_method == "大六壬":
                analysis_prompt = prompts_module.DALIUREN_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.DALIUREN_INTERPRETATION_PROMPT
            elif divination_method == "金口诀":
                analysis_prompt = prompts_module.JINKOUJUE_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.JINKOUJUE_INTERPRETATION_PROMPT
            elif divination_method == "八字":
                analysis_prompt = prompts_module.BAZI_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.BAZI_INTERPRETATION_PROMPT
            elif divination_method == "河洛理数":
                analysis_prompt = prompts_module.HELUO_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.HELUO_INTERPRETATION_PROMPT
            elif divination_method == "玄空择日":
                analysis_prompt = prompts_module.XUANKONG_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.XUANKONG_INTERPRETATION_PROMPT
            elif divination_method == "紫微斗数":
                analysis_prompt = prompts_module.ZIWEI_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.ZIWEI_INTERPRETATION_PROMPT
            elif divination_method == "梅花易数":
                analysis_prompt = prompts_module.MEIHUA_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.MEIHUA_INTERPRETATION_PROMPT
            elif divination_method == "太乙神数":
                analysis_prompt = prompts_module.TAIYI_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.TAIYI_INTERPRETATION_PROMPT
            else:
                # 默认使用六爻
                analysis_prompt = prompts_module.SIXYAO_ANALYSIS_PROMPT
                interpretation_prompt = prompts_module.SIXYAO_INTERPRETATION_PROMPT
            
            # 获取分析方面
            # 合并获取方面的状态更新
            def update_aspects_status():
                self.status_frame.update_progress(0.3)
                self.status_frame.update_status("获取分析方面...")
            
            self.update_ui(update_aspects_status)
            try:
                ai_response = AI(question, model, analysis_prompt)
                
                # 检查是否是错误信息
                if ai_response.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                    def update_api_error():
                        self.status_frame.update_status("分析失败，请重试")
                        self.notebook_frame.insert_result(f"分析失败: {ai_response}", 'error')
                    
                    self.update_ui(update_api_error)
                    return
            except Exception as e:
                def update_exception_error():
                    self.status_frame.update_status("分析失败，请重试")
                    self.notebook_frame.insert_result(f"分析失败: {str(e)}", 'error')
                
                self.update_ui(update_exception_error)
                return
            
            # 解析AI返回的JSON数组
            # 合并解读阶段的状态更新
            def update_interpretation_status():
                self.status_frame.update_progress(0.5)
                self.status_frame.update_status(f"解读{divination_method}...")
            
            self.update_ui(update_interpretation_status)
            aspects = parse_ai_response(ai_response)
            
            # 解读每个方面
            total_aspects = len(aspects)
            for i, aspect in enumerate(aspects, 1):
                progress = 0.5 + 0.4 * (i / total_aspects)
                # 合并进度和状态更新
                def update_progress_and_status(p=progress, idx=i, total=total_aspects):
                    self.status_frame.update_progress(p)
                    self.status_frame.update_status(f"分析方面 {idx}/{total}...")
                
                self.update_ui(update_progress_and_status)
                
                # RAG检索相关内容
                rag_context = ""
                if self.rag_searcher:
                    try:
                        # 构建搜索查询：结合用户问题和当前分析方面
                        search_query = f"{question} {aspect}"
                        
                        # 从设置页面获取RAG配置参数
                        rag_result_count = 10  # 默认值
                        rag_threshold = 0.3   # 默认值
                        
                        if hasattr(self, 'settings_frame') and self.settings_frame:
                            rag_result_count = self.settings_frame.get_rag_result_count()
                            rag_threshold = self.settings_frame.get_rag_threshold()
                        else:
                            # 如果设置页面不可用，从配置管理器获取
                            rag_result_count = config_manager.get('rag_result_count', 10)
                            rag_threshold = config_manager.get('rag_threshold', 0.3)
                        
                        # 执行RAG搜索
                        search_results = self.rag_searcher.search(
                            query=search_query,
                            search_method='hybrid',
                            top_k=rag_result_count, # 使用配置的结果数量
                            similarity_threshold=rag_threshold, # 使用配置的相似度阈值
                            use_query_expansion=True # 使用查询扩展
                        )
                        
                        # 格式化搜索结果作为参考资料
                        if search_results:
                            rag_context = "\n\n参考资料：\n"
                            for idx, result in enumerate(search_results, 1):
                                rag_context += f"{idx}. {result['content'][:200]}...\n"
                                # 收集来源文件名
                                if result['source_file']:
                                    rag_references.add(result['source_file'])
                            rag_context += "\n"
                            
                            logger.info(f"为方面'{aspect}'找到{len(search_results)}个相关参考")
                    except Exception as e:
                        logger.error(f"RAG搜索失败: {e}")
                        rag_context = ""
                
                try:
                    # 构建增强的提示词，包含RAG检索结果
                    enhanced_prompt = f"问题：{question}  分析方面：{aspect}\n\n{hexagram_content}{rag_context}"
                    aspect_result = AI(enhanced_prompt, model, interpretation_prompt)
                    
                    # 检查是否是错误信息
                    if aspect_result.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                        self.update_ui(lambda asp=aspect, result=aspect_result: self.notebook_frame.insert_result(f"分析方面 '{asp}' 失败: {result}", 'error'))
                        continue
                except Exception as e:
                    self.update_ui(lambda asp=aspect, error=str(e): self.notebook_frame.insert_result(f"分析方面 '{asp}' 失败: {error}", 'error'))
                    continue
                
                # 插入方面标题
                self.update_ui(lambda i=i, aspect=aspect: self.notebook_frame.insert_result(f"{i}、{aspect}：", 'aspect_title'))
                
                # 解析并插入解读结果，高亮括号内的内容
                import re
                
                # 批量收集所有要插入的内容，减少UI更新频率
                content_parts = []
                current_pos = 0
                
                for match in re.finditer(r'（[^（）]*）', aspect_result):
                    start, end = match.span()
                    if start < 0 or end > len(aspect_result) or start >= end:
                        continue
                    
                    # 当前匹配前的文本
                    text_before = aspect_result[current_pos:start]
                    if text_before:
                        content_parts.append(('main_text', text_before))
                    
                    # 提取完整括号内容
                    full_match = aspect_result[start:end]
                    if len(full_match) >= 2:
                        # 左括号（主文本颜色）
                        content_parts.append(('main_text', full_match[0]))
                        # 括号内内容（解释颜色）
                        inner_content = full_match[1:-1]
                        if inner_content:
                            content_parts.append(('explanation', inner_content))
                        # 右括号（主文本颜色）
                        content_parts.append(('main_text', full_match[-1]))
                    
                    current_pos = end
                
                # 最后一个匹配后的剩余文本
                text_after = aspect_result[current_pos:]
                if text_after:
                    content_parts.append(('main_text', text_after))
                
                # 添加换行
                content_parts.append(('main_text', "\n\n"))
                
                # 批量更新UI，减少调用频率
                def batch_insert_content():
                    for content_type, content in content_parts:
                        self.notebook_frame.insert_result(content, content_type)
                
                self.update_ui(batch_insert_content)
            
            # 生成总结论
            # 合并结论生成的状态更新
            def update_conclusion_status():
                self.status_frame.update_progress(0.95)
                self.status_frame.update_status("生成结论...")
            
            self.update_ui(update_conclusion_status)
            
            # 收集所有方面的结果以便生成结论
            full_analysis_text = self.notebook_frame.result_text.get(1.0, tk.END)
            conclusion_prompt = prompts_module.CONCLUSION_PROMPT.format(full_analysis_text)
            try:
                conclusion = AI(conclusion_prompt, model)
                
                # 批量插入结论内容
                def batch_insert_conclusion():
                    self.notebook_frame.insert_result("结论：", 'conclusion_title')
                    # 检查是否是错误信息
                    if conclusion.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                        self.notebook_frame.insert_result(f"结论生成失败: {conclusion}\n", 'error')
                    else:
                        self.notebook_frame.insert_result(conclusion + "\n", 'main_text')
                
                self.update_ui(batch_insert_conclusion)
            except Exception as e:
                def batch_insert_error():
                    self.notebook_frame.insert_result("结论：", 'conclusion_title')
                    self.notebook_frame.insert_result(f"结论生成失败: {str(e)}\n", 'error')
                
                self.update_ui(batch_insert_error)
            
            # 显示参考文献
            if rag_references:
                def batch_insert_references():
                    self.notebook_frame.insert_result("\n", 'main_text')
                    self.notebook_frame.insert_result("参考文件：", 'reference_title')
                    self.notebook_frame.insert_result("\n", 'main_text')
                    for ref_file in sorted(rag_references):
                        self.notebook_frame.insert_result(f"• {ref_file}\n", 'reference_text')
                    self.notebook_frame.insert_result("\n", 'main_text')
                
                self.update_ui(batch_insert_references)
            
            # 完成
            # 合并完成阶段的状态更新
            def update_completion_status():
                self.status_frame.update_progress(1.0)
                self.status_frame.update_status("分析完成")
            
            self.update_ui(update_completion_status)
            
            # 保存到历史记录
            self.save_to_history(question, hexagram_content, divination_method, model)
            
            # 启用聊天功能
            self.update_ui(lambda: self.notebook_frame.enable_chat())
            
            # 启用导出按钮
            self.update_ui(lambda: self.input_frame.enable_export())
            
        except Exception as e:
            error_msg = str(e)
            # 移除重复的logging调用，已有logger.error
            # 合并错误状态更新
            def update_error_status():
                self.status_frame.update_status("分析失败")
                self.status_frame.update_progress(0)
            
            self.update_ui(update_error_status)
            # 分析过程出错，记录到日志
            logger.error(f"分析过程出错: {error_msg}")
        finally:
            # 恢复按钮状态
            self.update_ui(lambda: self.input_frame.set_buttons_state("normal"))
    
    def update_ui(self, func):
        """在主线程中更新UI"""
        self.after(0, func)
    
    def handle_chat_message(self, message, model):
        """处理聊天消息"""
        # 使用线程避免UI卡顿
        import threading
        thread = threading.Thread(target=self._process_chat_message, args=(message, model))
        thread.daemon = True
        thread.start()
    
    def save_to_history(self, question, hexagram_content, divination_method, model):
        """保存分析结果到历史记录"""
        try:
            # 获取分析结果
            result_text = self.notebook_frame.result_text.get(1.0, "end-1c")
            
            # 获取聊天消息记录（如果有）
            chat_messages = []
            if hasattr(self.notebook_frame, 'chat_messages'):
                chat_messages = [{                    
                    'message': msg['message'],
                    'is_user': msg['is_user'],
                    'is_error': msg.get('is_error', False)
                } for msg in self.notebook_frame.chat_messages]
            
            # 添加到历史记录
            record_id = self.history_manager.add_record(
                question=question,
                hexagram_info=hexagram_content,
                divination_method=divination_method,
                model=model,
                analysis_result=result_text,
                chat_messages=chat_messages
            )
            
            # 刷新历史记录界面（如果存在）
            if hasattr(self.notebook_frame, 'history_frame'):
                self.update_ui(lambda: self.notebook_frame.history_frame.refresh_records())
            
            logger.info(f"分析结果已保存到历史记录，ID: {record_id}")
            
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def show_export_dialog(self):
        """显示导出对话框"""
        try:
            from tkinter import filedialog, messagebox
            import os
            from utils.export import export_analysis_results
            
            # 创建导出选项对话框
            export_window = ctk.CTkToplevel(self)
            export_window.title("导出选项")
            export_window.geometry("400x300")
            export_window.resizable(False, False)
            export_window.transient(self)  # 设置为主窗口的临时窗口
            export_window.grab_set()  # 模态对话框
            
            # 居中显示
            export_window.update_idletasks()
            width = export_window.winfo_width()
            height = export_window.winfo_height()
            x = (export_window.winfo_screenwidth() // 2) - (width // 2)
            y = (export_window.winfo_screenheight() // 2) - (height // 2)
            export_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
            
            # 标题
            title_label = ctk.CTkLabel(export_window, text="选择导出格式", font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=20)
            
            # 导出格式选择
            format_var = tk.StringVar(value="PDF")
            
            formats_frame = ctk.CTkFrame(
                export_window,
                fg_color=self.get_color("card_bg")
            )
            formats_frame.pack(pady=10, padx=20, fill="x")
            
            pdf_radio = ctk.CTkRadioButton(formats_frame, text="PDF格式", variable=format_var, value="PDF")
            pdf_radio.pack(pady=5, anchor="w")
            
            word_radio = ctk.CTkRadioButton(formats_frame, text="Word格式", variable=format_var, value="Word")
            word_radio.pack(pady=5, anchor="w")
            
            text_radio = ctk.CTkRadioButton(formats_frame, text="文本格式", variable=format_var, value="Text")
            text_radio.pack(pady=5, anchor="w")
            
            # 按钮区域
            buttons_frame = ctk.CTkFrame(
                export_window,
                fg_color=self.get_color("card_bg")
            )
            buttons_frame.pack(pady=20, padx=20, fill="x")
            
            def do_export():
                try:
                    export_format = format_var.get()
                    
                    # 选择保存位置
                    if export_format == "PDF":
                        file_path = filedialog.asksaveasfilename(
                            defaultextension=".pdf",
                            filetypes=[("PDF文件", "*.pdf")],
                            title="保存PDF文件"
                        )
                    elif export_format == "Word":
                        file_path = filedialog.asksaveasfilename(
                            defaultextension=".docx",
                            filetypes=[("Word文档", "*.docx")],
                            title="保存Word文档"
                        )
                    else:  # Text
                        file_path = filedialog.asksaveasfilename(
                            defaultextension=".txt",
                            filetypes=[("文本文件", "*.txt")],
                            title="保存文本文件"
                        )
                    
                    if not file_path:
                        return
                    
                    # 获取分析结果
                    result_text = self.notebook_frame.result_text.get(1.0, "end-1c")
                    question = self.input_frame.get_question()
                    
                    # 调用导出功能
                    success, message = export_analysis_results(
                        file_path=file_path,
                        title="六爻分析结果",
                        question=question,
                        hexagram_info="",  # 可以根据需要添加卦象信息
                        analysis_results=result_text,
                        conclusion="",  # 可以根据需要提取结论
                        language="zh_CN"
                    )
                    
                    export_window.destroy()
                    
                    if success:
                        # 导出成功，记录到日志
                        logger.info(f"分析结果已成功导出到: {file_path}")
                    else:
                        # 导出错误，记录到日志
                        logger.error(f"导出过程中发生错误: {message}")
                        
                except Exception as e:
                    export_window.destroy()
                    # 导出错误，已记录到日志
                    logger.error(f"导出错误: {str(e)}")
            
            export_btn = ctk.CTkButton(buttons_frame, text="导出", command=do_export)
            export_btn.pack(side="left", padx=10, expand=True, fill="x")
            
            cancel_btn = ctk.CTkButton(buttons_frame, text="取消", command=export_window.destroy)
            cancel_btn.pack(side="right", padx=10, expand=True, fill="x")
            
        except Exception as e:
            logger.error(f"显示导出对话框时出错: {e}")
            # 显示导出对话框错误，已记录到日志
    
    def _process_chat_message(self, message, model):
        """在后台线程中处理聊天消息"""
        try:
            # 导入API模块和提示词
            import sys
            import os
            import importlib.util
            
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            api_file_path = os.path.join(project_root, 'api.py')
            prompts_file_path = os.path.join(project_root, 'src', 'prompts.py')
            
            # 动态导入api.py模块
            spec = importlib.util.spec_from_file_location("api_module", api_file_path)
            api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_module)
            
            # 动态导入prompts.py模块
            spec = importlib.util.spec_from_file_location("prompts_module", prompts_file_path)
            prompts_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(prompts_module)
            
            AI = api_module.AI
            INTERPRETATION_CHAT_PROMPT = prompts_module.INTERPRETATION_CHAT_PROMPT
            
            # 获取当前解读结果作为上下文
            current_result = self.notebook_frame.result_text.get(1.0, tk.END).strip()
            
            # 构建聊天提示词
            chat_prompt = f"""{INTERPRETATION_CHAT_PROMPT}

【当前解读结果】
{current_result}

【用户问题】
{message}

请基于上述解读结果，针对用户的具体问题给出专业解答："""
            
            # 调用AI获取回复
            try:
                response = AI(chat_prompt, model)
                
                # 在主线程中更新UI
                # 检查是否是错误信息
                is_error = response.startswith(("API请求失败", "API响应解析失败", "处理失败"))
                if is_error:
                    ai_response = f"抱歉，回复生成失败: {response}"
                    self.after(0, lambda: self.notebook_frame.add_ai_response(ai_response, is_error=True))
                else:
                    ai_response = response
                    self.after(0, lambda: self.notebook_frame.add_ai_response(ai_response))
                
                # 更新当前历史记录中的聊天消息
                self._update_history_chat_messages(message, ai_response, is_error)
                
            except Exception as e:
                error_msg = f"抱歉，回复生成失败: {str(e)}"
                self.after(0, lambda: self.notebook_frame.add_ai_response(error_msg, is_error=True))
                
                # 更新当前历史记录中的聊天消息（错误情况）
                self._update_history_chat_messages(message, error_msg, True)
            
        except Exception as e:
            error_msg = f"聊天功能出错: {str(e)}"
            logger.error(error_msg)
            # 在主线程中更新UI
            self.after(0, lambda: self.notebook_frame.add_ai_response(error_msg, is_error=True))
            
            # 更新当前历史记录中的聊天消息（错误情况）
            self._update_history_chat_messages(message, error_msg, True)
    
    def _update_history_chat_messages(self, user_message, ai_response, is_error=False):
        """更新当前历史记录中的聊天消息"""
        try:
            # 获取当前问题和分析结果
            question = self.input_frame.get_question()
            divination_method = self.input_frame.get_divination_method()
            model = self.input_frame.get_model()
            
            # 查找当前记录 - 只匹配问题、起卦方式和模型，不再匹配卦象信息和分析结果
            # 这样可以更灵活地找到匹配的历史记录
            current_record = None
            for record in self.history_manager.records:
                if (record.question == question and 
                    record.divination_method == divination_method and 
                    record.model == model):
                    current_record = record
                    break
            
            if current_record:
                # 确保记录有chat_messages属性
                if not hasattr(current_record, 'chat_messages'):
                    current_record.chat_messages = []
                
                # 添加用户消息
                current_record.chat_messages.append({
                    'message': user_message,
                    'is_user': True,
                    'is_error': False
                })
                
                # 添加AI回复
                current_record.chat_messages.append({
                    'message': ai_response,
                    'is_user': False,
                    'is_error': is_error
                })
                
                # 保存更新后的历史记录
                self.history_manager.save_history()
                logger.info(f"已更新历史记录中的聊天消息: {user_message[:30]}...")
            else:
                logger.warning("无法找到匹配的历史记录来更新聊天消息")
                
        except Exception as e:
            logger.error(f"更新历史记录中的聊天消息时出错: {e}")

    

    

    
    # 旧版设置对话框方法已删除，使用弹出窗口版本
    
    def show_help(self):
        """显示帮助信息"""
        try:
            help_text = """AI易学分析系统使用说明：

1. 在问题输入框中输入您要咨询的问题
2. 选择合适的起卦方式
3. 选择AI模型
4. 在卦象信息页面输入相关信息
5. 点击开始分析按钮
6. 查看分析结果
7. 可以在对话页面进行进一步交流

更多功能正在开发中..."""
            # 帮助信息，记录到日志
            logger.info(f"帮助信息: {help_text}")
        except Exception as e:
            logger.error(f"显示帮助信息时出错: {e}")
    
    def show_about(self):
        """显示关于信息"""
        try:
            about_text = f"""{t('app_name')}
{t('app_version')}: 1.0.0

一个基于AI的易学分析工具，支持多种占卜方式。

开发者: AI助手
技术支持: Python + CustomTkinter"""
            # 关于信息，记录到日志
            logger.info(f"关于信息: {about_text}")
        except Exception as e:
            logger.error(f"显示关于信息时出错: {e}")
    
    def show_settings(self):
        """显示设置页面 - 切换到主窗口中的设置标签页"""
        try:
            # 切换到设置标签页
            if hasattr(self, 'notebook_frame'):
                # 获取设置标签页的名称
                from config.languages import t
                settings_tab_name = t("tab_settings")
                
                # 切换到设置标签页
                self.notebook_frame.tabview.set(settings_tab_name)
                logger.info("已切换到设置标签页")
        except Exception as e:
            logger.error(f"切换到设置标签页时出错: {e}")
            try:
                import tkinter.messagebox as msgbox
                msgbox.showerror("错误", f"无法打开设置页面: {str(e)}")
            except:
                logger.error(f"无法打开设置页面: {str(e)}")
    
    def center_settings_window(self, window):
        """设置窗口居中"""
        try:
            window.update_idletasks()
            x = (window.winfo_screenwidth() // 2) - (400)
            y = (window.winfo_screenheight() // 2) - (300)
            window.geometry(f"800x600+{x}+{y}")
        except Exception as e:
            logger.error(f"设置窗口居中时出错: {e}")
    
    def show_database_status(self, message):
        """显示数据库状态提示"""
        try:
            # 在状态栏显示消息
            if hasattr(self, 'status_frame'):
                self.status_frame.show_message(message, duration=5000)
            
            # 在头部区域显示临时提示 - 使用grid布局
            if hasattr(self, 'header_frame'):
                # 创建临时提示标签
                status_label = ctk.CTkLabel(
                    self.header_frame,
                    text=f"✅ {message}",
                    font=ctk.CTkFont(size=12),
                    text_color=("#2E8B57", "#90EE90")  # 绿色文字
                )
                # 使用grid布局而不是pack，放在第2行，跨越两列
                status_label.grid(row=2, column=0, columnspan=2, pady=(5, 0), sticky="w", padx=20)
                
                # 5秒后自动隐藏
                self.after(5000, lambda: status_label.destroy())
            
            logger.info(f"显示数据库状态: {message}")
        except Exception as e:
            logger.error(f"显示数据库状态时出错: {e}")
    
    def update_model_list(self):
        """更新模型列表"""
        try:
            # 更新输入框架中的模型选择
            if hasattr(self, 'input_frame') and hasattr(self.input_frame, 'update_model_list'):
                self.input_frame.update_model_list()
            
            # 更新笔记本框架中的聊天模型选择
            if hasattr(self, 'notebook_frame') and hasattr(self.notebook_frame, 'update_chat_model_list'):
                self.notebook_frame.update_chat_model_list()
                
            logger.info("主应用程序模型列表已更新")
        except Exception as e:
            logger.error(f"更新模型列表时出错: {e}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 保存当前主题模式
            current_mode = UI_SETTINGS["appearance_mode"]
            config_manager.set_theme_mode(current_mode)
            
            # 保存窗口几何信息
            geometry = self.geometry()
            config_manager.set_window_geometry(geometry)
            
            # 保存RAG配置设置
            if hasattr(self, 'settings_frame') and self.settings_frame:
                self.settings_frame.save_rag_settings()
            
            # 保存配置文件
            config_manager.save_config()
            logger.info(f"应用退出时已保存配置：主题模式={current_mode}, 窗口几何={geometry}")
            
        except Exception as e:
            logger.error(f"保存配置时出错: {e}")
        finally:
            self.destroy()
    
    def destroy(self):
        """销毁窗口时清理资源"""
        try:
            pass
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")
        finally:
            super().destroy()