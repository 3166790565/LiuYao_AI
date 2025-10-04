# gui/app.py

import importlib.util
import os
import threading
import tkinter as tk

import customtkinter as ctk

# 导入项目模块
from config import APP_NAME, RESOURCES_DIR
from config.languages import t
from config.ui_config import UI_SETTINGS, get_ui_settings, toggle_theme_mode
from utils.config_manager import config_manager
from utils.history import HistoryManager
from utils.logger import setup_logger
from .frames import (
    HeaderFrame,
    InputFrame,
    NotebookFrame,
    StatusFrame,
    FooterFrame
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
        yongshen = self.input_frame.get_yongshen()
        fangmian = self.input_frame.get_fangmian()
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
            args=(question, hexagram_content, divination_method, model, yongshen, fangmian),
            daemon=True
        ).start()

    def perform_analysis(self, question, hexagram_content, divination_method, model, yongshen, fangmian):
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

            # 添加用神判断步骤（仅对六爻占卜）
            logger.info(f"当前起卦方式: {divination_method}")
            if divination_method == "六爻":
                logger.info("开始执行用神判断功能")

                def update_yongshen_status():
                    self.status_frame.update_progress(0.25)
                    self.status_frame.update_status("正在判断用神...")

                self.update_ui(update_yongshen_status)

                try:
                    # 构建用神判断的提示词
                    yongshen_prompt = """你是一名资深的六爻解卦大师，精通《周易》和六爻预测学。你的任务是根据用户提供的卦象信息和所问问题，准确判断应该使用本卦中的哪一爻作为用神，并详细说明判断依据。

请按照以下步骤进行分析：
1. 分析卦象的基本信息（主卦、变卦、动爻等）
2. 根据所问事情的性质确定用神的选择原则
3. 结合六亲关系、五行生克、旺衰等因素综合判断
4. 明确指出用神所在的爻位（初爻、二爻、三爻、四爻、五爻、上爻）
5. 只能在本卦中或本卦伏神中选择用神，变卦不做考虑范围

参考资料：
1. 根据所问之事先确定六亲
2. 再看六亲在哪一爻：优先取"世爻、应爻"上的为用神、优先取"本卦动爻"为用神、优先取有"特殊现象的爻"为用神（如：月破、日冲、月合、日合、旬空等）

父母爻：占父母，以卦中父母爻为用神。祖父母、伯、叔、姑、姨父母，凡在我父母之上，或与我父母同辈之亲，及师长，妻子的父母，拜认的干父母、三父、八母，或仆人占主人，全部用父母爻作为用神。占天地、城池、墙垣、宅舍、屋宇、舟车、衣服、雨具、绸缎、布匹、杂货、及奏章、文书、文章、书馆、文契，亦以父母爻为用神。一切庇护我的全可以用父母爻为用神。
官鬼爻：占功名、官府、雷霆、鬼神、妻子占老公、全部以官鬼爻为用神。占乱臣、贼盗、邪祟、也可以用官鬼爻为用神。一切拘束我身者都可以用官鬼爻为用神。
兄弟爻：占兄弟、姐妹、族中兄弟、姑姨，姐夫、妹夫、及结拜兄弟，全部以兄弟爻为用神。兄弟爻代表与自己身份地位相当的人。兄弟乃同类之人，彼得志则欺陵，见财则夺，所以占财物，以此为劫财之神，占谋事，以此为 阻隔之神，占妻妾、婢仆，以此为刑伤克害之神。占姐丈、妹夫，以世爻为用神，予屡得验。占表兄弟，以兄弟爻为用神而不验，还以应为用神。
妻财爻：占妻妾、婢仆、下役，凡我驱使之人，皆以财爻为用神。占货财、珠宝、金银、仓库、 钱粮，一切使用之财物、什物、器皿，亦以财爻为用神。
子孙爻：占子孙、占女、女婿、侄、甥、门徒，凡在我子孙辈中，皆以子孙爻为用神。占忠臣、 良将、医士、医药、僧、道、兵、卒，皆以子孙爻为用神。占六畜、禽兽，亦以子孙爻为用神。子孙为福德之神、为制鬼之神、为解忧之神、又为剥官、引职之神，故谓之子孙乃是福神，诸 事见之为喜，独占功名者忌之。

[乾按曰] 用神者，实为卦中所占事之六亲标志也。用即取用，神指阴阳二气之变化也。取准用 神与测占灵验至关紧要，倘用神错取，则百无一用矣。

返回内容必须严格按照以下JSON格式，不要添加任何其他文字：
{"text":"用神所在爻位","yiju":"详细的判断依据和分析过程"}

注意：
- text字段填写例如："初爻妻财"、"二爻官鬼"、"三爻父母"、"四爻子孙"、"五爻兄弟"、"上爻妻财"，或如果选择伏神为用神示例：“初爻伏神官鬼”
- yiju字段要用一段话说明选择该爻作为用神的理由，包括六亲关系、五行属性、旺衰状态等分析"""

                    # 构建用神判断的输入
                    yongshen_input = f"卦象信息：\n{hexagram_content}\n\n用户问题：{question}"

                    # 如果用户输入了用神信息，则直接使用用户输入的用神
                    if yongshen and yongshen.strip():
                        logger.info(f"用户指定用神: {yongshen}")
                        # 创建用户指定的用神信息
                        self.yongshen_info = {
                            "text": yongshen,
                            "yiju": "用户手动指定的用神"
                        }

                        # 插入用户指定的用神到解读结果编辑框
                        def insert_user_yongshen():
                            self.notebook_frame.insert_result("【用神信息】\n", 'aspect_title')
                            self.notebook_frame.insert_result(f"用神：{yongshen}\n")
                            self.notebook_frame.insert_result("判断依据：用户手动指定\n\n")

                        self.update_ui(insert_user_yongshen)
                        logger.info(f"使用用户指定的用神：{yongshen}")
                    else:
                        # 只有在用户未指定用神时，才调用AI进行用神判断
                        yongshen_response = AI(yongshen_input, model, yongshen_prompt)

                        # 检查是否是错误信息
                        if not yongshen_response.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                            try:
                                # 解析用神判断结果
                                import json
                                yongshen_result = json.loads(yongshen_response)

                                # 保存用神判断结果供后续步骤使用
                                self.yongshen_info = yongshen_result

                                # 插入用神判断结果到解读结果编辑框
                                def insert_yongshen_result():
                                    self.notebook_frame.insert_result("【用神判断】\n", 'aspect_title')
                                    self.notebook_frame.insert_result(f"用神：{yongshen_result.get('text', '未知')}\n")
                                    self.notebook_frame.insert_result(
                                        f"判断依据：{yongshen_result.get('yiju', '无详细说明')}\n\n")

                                self.update_ui(insert_yongshen_result)
                                logger.info(f"用神判断完成：{yongshen_result.get('text', '未知')}")

                            except json.JSONDecodeError as e:
                                logger.error(f"用神判断结果JSON解析失败: {e}")
                                self.yongshen_info = None

                                def insert_yongshen_error():
                                    self.notebook_frame.insert_result("【用神判断】\n", 'aspect_title')
                                    self.notebook_frame.insert_result("用神判断结果解析失败，请重试\n\n", 'error')

                                self.update_ui(insert_yongshen_error)
                        else:
                            logger.error(f"用神判断API调用失败: {yongshen_response}")
                            self.yongshen_info = None

                            def insert_yongshen_api_error():
                                self.notebook_frame.insert_result("【用神判断】\n", 'aspect_title')
                                self.notebook_frame.insert_result(f"用神判断失败: {yongshen_response}\n\n", 'error')

                            self.update_ui(insert_yongshen_api_error)

                except Exception as e:
                    logger.error(f"用神判断过程出错: {e}")

                    def insert_yongshen_exception():
                        self.notebook_frame.insert_result("【用神判断】\n", 'aspect_title')
                        self.notebook_frame.insert_result(f"用神判断过程出错: {str(e)}\n\n", 'error')

                    self.update_ui(insert_yongshen_exception)

            # 添加用神卦理分析步骤（仅对六爻占卜）
            if divination_method == "六爻":
                logger.info("开始执行用神卦理分析功能")

                def update_guli_status():
                    self.status_frame.update_progress(0.28)
                    self.status_frame.update_status("正在分析用神卦理...")

                self.update_ui(update_guli_status)

                try:
                    # 构建用神卦理分析的提示词
                    guli_prompt = prompts_module.YONGSHEN_GULI_ANALYSIS_PROMPT

                    # 构建用神卦理分析的输入，包含前一阶段选定的用神信息
                    yongshen_info_text = ""
                    if hasattr(self, 'yongshen_info') and self.yongshen_info:
                        yongshen_info_text = f"\n\n选定用神：{self.yongshen_info.get('text', '未知')}\n判断依据：{self.yongshen_info.get('yiju', '无详细说明')}"

                    guli_input = f"卦象信息：\n{hexagram_content}\n\n用户问题：{question}{yongshen_info_text}\n\n请根据以上信息分析用神在整体卦象中的卦理状态。"

                    # 调用AI进行用神卦理分析
                    guli_response = AI(guli_input, model, guli_prompt)
                    logger.info(guli_response)
                    # 检查是否是错误信息
                    if not guli_response.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                        try:
                            # 解析用神卦理分析结果
                            import json
                            guli_result = json.loads(guli_response)

                            # 插入用神卦理分析结果到解读结果编辑框
                            def insert_guli_result():
                                self.notebook_frame.insert_result("【用神卦理分析】\n", 'aspect_title')
                                self.notebook_frame.insert_result(f"月建关系：{guli_result.get('月建关系', '未知')}\n")
                                self.notebook_frame.insert_result(f"日辰关系：{guli_result.get('日辰关系', '未知')}\n")
                                self.notebook_frame.insert_result(f"动爻关系：{guli_result.get('动爻关系', '未知')}\n")
                                self.notebook_frame.insert_result(f"特殊状态：{guli_result.get('特殊状态', '未知')}\n")
                                self.notebook_frame.insert_result(f"回头生克：{guli_result.get('回头生克', '未知')}\n")
                                self.notebook_frame.insert_result(f"原神忌神：{guli_result.get('原神忌神', '未知')}\n")
                                self.notebook_frame.insert_result(f"旺衰评估：{guli_result.get('旺衰评估', '未知')}\n\n")

                            self.update_ui(insert_guli_result)
                            logger.info("用神卦理分析完成")

                        except json.JSONDecodeError as e:
                            logger.error(f"用神卦理分析结果JSON解析失败: {e}")

                            def insert_guli_error():
                                self.notebook_frame.insert_result("【用神卦理分析】\n", 'aspect_title')
                                self.notebook_frame.insert_result("用神卦理分析结果解析失败，请重试\n\n", 'error')

                            self.update_ui(insert_guli_error)
                    else:
                        logger.error(f"用神卦理分析API调用失败: {guli_response}")

                        def insert_guli_api_error():
                            self.notebook_frame.insert_result("【用神卦理分析】\n", 'aspect_title')
                            self.notebook_frame.insert_result(f"用神卦理分析失败: {guli_response}\n\n", 'error')

                        self.update_ui(insert_guli_api_error)

                except Exception as e:
                    logger.error(f"用神卦理分析过程出错: {e}")

                    def insert_guli_exception():
                        self.notebook_frame.insert_result("【用神卦理分析】\n", 'aspect_title')
                        self.notebook_frame.insert_result(f"用神卦理分析过程出错: {str(e)}\n\n", 'error')

                    self.update_ui(insert_guli_exception)

            # 添加动爻卦理分析步骤（仅对六爻占卜）
            if divination_method == "六爻":
                logger.info("开始执行动爻卦理分析功能")

                def update_dongyao_status():
                    self.status_frame.update_progress(0.29)
                    self.status_frame.update_status("正在分析动爻卦理...")

                self.update_ui(update_dongyao_status)

                try:
                    # 构建动爻卦理分析的提示词
                    dongyao_prompt = prompts_module.DONGYAO_GULI_ANALYSIS_PROMPT

                    # 构建动爻卦理分析的输入
                    dongyao_input = f"卦象信息：\n{hexagram_content}\n\n用户问题：{question}\n\n请根据以上信息分析卦中所有动爻在整体卦象中的卦理状态。"

                    # 调用AI进行动爻卦理分析
                    dongyao_response = AI(dongyao_input, model, dongyao_prompt).replace("json", "").replace("```", "")
                    logger.info(dongyao_response)
                    # 检查是否是错误信息
                    if not dongyao_response.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                        try:
                            logger.info(dongyao_response)
                            # 解析动爻卦理分析结果
                            import json
                            dongyao_result = json.loads(dongyao_response)
                            logger.info(dongyao_response)

                            # 插入动爻卦理分析结果到解读结果编辑框
                            def insert_dongyao_result():
                                self.notebook_frame.insert_result("【动爻卦理分析】\n", 'aspect_title')

                                has_dongyao = dongyao_result.get('有动爻', False)
                                logger.info(has_dongyao)
                                if has_dongyao:
                                    dongyao_list = dongyao_result.get('动爻列表', [])
                                    logger.info(dongyao_list)
                                    if dongyao_list:
                                        for i, dongyao in enumerate(dongyao_list, 1):
                                            self.notebook_frame.insert_result(
                                                f"动爻{i}（{dongyao.get('爻位', '未知')}）：\n")
                                            self.notebook_frame.insert_result(
                                                f"  月建关系：{dongyao.get('月建关系', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  日辰关系：{dongyao.get('日辰关系', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  动爻关系：{dongyao.get('动爻关系', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  特殊状态：{dongyao.get('特殊状态', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  回头生克：{dongyao.get('回头生克', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  变爻关系：{dongyao.get('变爻关系', '未知')}\n")
                                            self.notebook_frame.insert_result(
                                                f"  旺衰评估：{dongyao.get('旺衰评估', '未知')}\n\n")
                                    else:
                                        self.notebook_frame.insert_result("卦中有动爻但分析列表为空\n\n")
                                else:
                                    self.notebook_frame.insert_result("卦中无动爻\n\n")

                            self.update_ui(insert_dongyao_result)
                            logger.info("动爻卦理分析完成")

                        except json.JSONDecodeError as e:
                            logger.error(f"动爻卦理分析结果JSON解析失败: {e}")

                            def insert_dongyao_error():
                                self.notebook_frame.insert_result("【动爻卦理分析】\n", 'aspect_title')
                                self.notebook_frame.insert_result("动爻卦理分析结果解析失败，请重试\n\n", 'error')

                            self.update_ui(insert_dongyao_error)
                    else:
                        logger.error(f"动爻卦理分析API调用失败: {dongyao_response}")

                        def insert_dongyao_api_error():
                            self.notebook_frame.insert_result("【动爻卦理分析】\n", 'aspect_title')
                            self.notebook_frame.insert_result(f"动爻卦理分析失败: {dongyao_response}\n\n", 'error')

                        self.update_ui(insert_dongyao_api_error)

                except Exception as e:
                    logger.error(f"动爻卦理分析过程出错: {e}")

                    def insert_dongyao_exception():
                        self.notebook_frame.insert_result("【动爻卦理分析】\n", 'aspect_title')
                        self.notebook_frame.insert_result(f"动爻卦理分析过程出错: {str(e)}\n\n", 'error')

                    self.update_ui(insert_dongyao_exception)

            # 添加数字量化分析步骤（仅对六爻占卜）
            if divination_method == "六爻":
                logger.info("开始执行数字量化分析功能")

                def update_shuzi_status():
                    self.status_frame.update_progress(0.295)
                    self.status_frame.update_status("正在进行数字量化分析...")

                self.update_ui(update_shuzi_status)

                try:
                    # 导入数字量化函数
                    from utils.shuzilianghua import shuzilianghua

                    # 构建数字量化分析的提示词
                    shuzi_prompt = prompts_module.SHUZI_LIANGHUA_ANALYSIS_PROMPT

                    # 构建数字量化分析的输入
                    shuzi_input = f"卦象信息：\n{hexagram_content}\n\n请从以上卦象信息中提取月建、日辰、用神和动爻的地支信息。"

                    # 调用AI进行数字量化分析
                    shuzi_response = AI(shuzi_input, model, shuzi_prompt).replace("json", "").replace("```", "")

                    # 检查是否是错误信息
                    if not shuzi_response.startswith(("API请求失败", "API响应解析失败", "处理失败")):
                        try:
                            # 解析数字量化分析结果
                            import json
                            shuzi_result = json.loads(shuzi_response)

                            # 提取地支信息
                            yuejian = shuzi_result.get('月建', '')
                            richen = shuzi_result.get('日辰', '')
                            yongshen_dz = shuzi_result.get('用神', '')
                            dongyao_list = shuzi_result.get('动爻列表', [])

                            # 插入数字量化分析结果到解读结果编辑框
                            def insert_shuzi_result():
                                self.notebook_frame.insert_result("【数字量化分析】\n", 'aspect_title')

                                # 分析用神强弱指数
                                if yongshen_dz:
                                    try:
                                        yuejianshu, richenshu = shuzilianghua(yuejian, richen, yongshen_dz)

                                        if richenshu == "po":
                                            # 日破情况，需要AI判断是暗动还是日破
                                            ripo_prompt = prompts_module.RIPO_ANDONG_ANALYSIS_PROMPT
                                            ripo_input = f"卦象信息：\n{hexagram_content}\n\n月建数字量化：{yuejianshu}\n\n请判断用神是暗动还是日破。"
                                            ripo_response = AI(ripo_input, model, ripo_prompt)

                                            try:
                                                ripo_result = json.loads(ripo_response)
                                                result_text = ripo_result.get('text', '未知')
                                                result_yiju = ripo_result.get('yiju', '无依据')
                                                self.notebook_frame.insert_result(f"用神状态：{result_text}\n")
                                                self.notebook_frame.insert_result(f"判断依据：{result_yiju}\n\n")
                                            except json.JSONDecodeError:
                                                self.notebook_frame.insert_result("用神状态：日破（AI分析失败）\n\n")
                                        else:
                                            # 正常情况，计算强弱指数
                                            qiangruo_zhishu = yuejianshu + richenshu
                                            self.notebook_frame.insert_result(f"用神强弱指数：{qiangruo_zhishu}\n")
                                            self.notebook_frame.insert_result(f"  月建数：{yuejianshu}\n")
                                            self.notebook_frame.insert_result(f"  日辰数：{richenshu}\n\n")
                                    except Exception as e:
                                        self.notebook_frame.insert_result(f"用神数字量化计算失败：{str(e)}\n\n")

                                # 分析动爻强弱指数
                                if dongyao_list:
                                    for i, dongyao_dizhi in enumerate(dongyao_list, 1):
                                        try:
                                            yuejianshu, richenshu = shuzilianghua(yuejian, richen, dongyao_dizhi)

                                            if richenshu == "po":
                                                # 日破情况，需要AI判断是暗动还是日破
                                                ripo_prompt = prompts_module.RIPO_ANDONG_ANALYSIS_PROMPT
                                                ripo_input = f"卦象信息：\n{hexagram_content}\n\n月建数字量化：{yuejianshu}\n\n请判断动爻{i}是暗动还是日破。"
                                                ripo_response = AI(ripo_input, model, ripo_prompt)

                                                try:
                                                    ripo_result = json.loads(ripo_response)
                                                    result_text = ripo_result.get('text', '未知')
                                                    result_yiju = ripo_result.get('yiju', '无依据')
                                                    self.notebook_frame.insert_result(f"动爻{i}状态：{result_text}\n")
                                                    self.notebook_frame.insert_result(f"判断依据：{result_yiju}\n\n")
                                                except json.JSONDecodeError:
                                                    self.notebook_frame.insert_result(
                                                        f"动爻{i}状态：日破（AI分析失败）\n\n")
                                            else:
                                                # 正常情况，计算强弱指数
                                                qiangruo_zhishu = yuejianshu + richenshu
                                                self.notebook_frame.insert_result(
                                                    f"动爻{i}强弱指数：{qiangruo_zhishu}\n")
                                                self.notebook_frame.insert_result(f"  月建数：{yuejianshu}\n")
                                                self.notebook_frame.insert_result(f"  日辰数：{richenshu}\n\n")
                                        except Exception as e:
                                            self.notebook_frame.insert_result(f"动爻{i}数字量化计算失败：{str(e)}\n\n")
                                else:
                                    self.notebook_frame.insert_result("无动爻需要分析\n\n")

                            self.update_ui(insert_shuzi_result)
                            logger.info("数字量化分析完成")

                        except json.JSONDecodeError as e:
                            logger.error(f"数字量化分析结果JSON解析失败: {e}")

                            def insert_shuzi_error():
                                self.notebook_frame.insert_result("【数字量化分析】\n", 'aspect_title')
                                self.notebook_frame.insert_result("数字量化分析结果解析失败，请重试\n\n", 'error')

                            self.update_ui(insert_shuzi_error)
                    else:
                        logger.error(f"数字量化分析API调用失败: {shuzi_response}")

                        def insert_shuzi_api_error():
                            self.notebook_frame.insert_result("【数字量化分析】\n", 'aspect_title')
                            self.notebook_frame.insert_result(f"数字量化分析失败: {shuzi_response}\n\n", 'error')

                        self.update_ui(insert_shuzi_api_error)

                except Exception as e:
                    logger.error(f"数字量化分析过程出错: {e}")

                    def insert_shuzi_exception():
                        self.notebook_frame.insert_result("【数字量化分析】\n", 'aspect_title')
                        self.notebook_frame.insert_result(f"数字量化分析过程出错: {str(e)}\n\n", 'error')

                    self.update_ui(insert_shuzi_exception)
            
            # 获取分析方面
            # 合并获取方面的状态更新
            def update_aspects_status():
                self.status_frame.update_progress(0.3)
                self.status_frame.update_status("获取分析方面...")
            
            self.update_ui(update_aspects_status)
            # 收集前期分析结果
            previous_analysis = self.notebook_frame.result_text.get(1.0, tk.END)

            # 构建包含前期分析结果的输入
            analysis_input = f"问题：{question}\n\n前期分析结果：\n{previous_analysis}\n\n请基于以上信息分析需要解读的方面。"
            if fangmian != "":
                aspects = fangmian.split()
            else:
                try:
                    ai_response = AI(analysis_input, model, analysis_prompt)

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
                    self.status_frame.update_progress(0.4)
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
                        # 从前期分析结果中提取用神卦理信息用于RAG搜索
                        yongshen_guli_info = ""
                        previous_text = self.notebook_frame.result_text.get(1.0, tk.END)

                        # 提取用神卦理分析部分
                        if "【用神卦理分析】" in previous_text:
                            start_idx = previous_text.find("【用神卦理分析】")
                            end_idx = previous_text.find("【动爻卦理分析】", start_idx)
                            if end_idx == -1:
                                end_idx = previous_text.find("【数字量化分析】", start_idx)
                            if end_idx != -1:
                                yongshen_guli_info = previous_text[start_idx:end_idx].strip()
                        
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

                        # 执行两次RAG搜索并合并结果
                        search_results = []

                        # 第一次查询：使用问题和方面
                        search_query1 = f"{question} {aspect}"
                        search_results1 = self.rag_searcher.search(
                            query=search_query1,
                            search_method='hybrid',
                            top_k=rag_result_count, # 使用配置的结果数量
                            similarity_threshold=rag_threshold, # 使用配置的相似度阈值
                            use_query_expansion=True # 使用查询扩展
                        )
                        if search_results1:
                            search_results.extend(search_results1)

                        # 第二次查询：使用用神卦理信息（如果存在）
                        if yongshen_guli_info:
                            search_query2 = yongshen_guli_info
                            search_results2 = self.rag_searcher.search(
                                query=search_query2,
                                search_method='hybrid',
                                top_k=rag_result_count,  # 使用配置的结果数量
                                similarity_threshold=rag_threshold,  # 使用配置的相似度阈值
                                use_query_expansion=True  # 使用查询扩展
                            )
                            if search_results2:
                                search_results.extend(search_results2)
                        
                        # 格式化搜索结果作为参考资料
                        if search_results:
                            rag_context = "\n\n参考资料：\n"
                            for idx, result in enumerate(search_results, 1):
                                rag_context += f"{idx}. {result['content'][:200]}...\n"
                                # 收集来源文件名
                                if result['source_file']:
                                    rag_references.add(result['source_file'])
                            rag_context += "\n"

                            logger.info(f"为方面'{aspect}'找到{len(search_results)}个相关参考（使用用神卦理搜索）")
                    except Exception as e:
                        logger.error(f"RAG搜索失败: {e}")
                        rag_context = ""
                
                try:
                    # 构建增强的提示词，包含前期分析结果和RAG检索结果
                    enhanced_prompt = f"问题：{question}  分析方面：{aspect}\n\n前期分析结果：\n{previous_analysis}\n\n{hexagram_content}{rag_context}"
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
            self.save_to_history(question, hexagram_content, divination_method, yongshen, fangmian, model)
            
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

    def save_to_history(self, question, hexagram_content, divination_method, yongshen, fangmian, model):
        """保存分析结果到历史记录"""
        try:
            # 获取分析结果（获取纯文本，不包含格式标签）
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
                yongshen=yongshen,
                fangmian=fangmian,
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

            # 提取各个分析部分的内容
            analysis_sections = {}
            sections = ["【用神判断】", "【用神卦理分析】", "【动爻卦理分析】", "【数字量化分析】"]

            for i, section in enumerate(sections):
                if section in current_result:
                    start_idx = current_result.find(section)
                    # 找到下一个分析部分的开始位置作为结束位置
                    end_idx = len(current_result)
                    for j in range(i + 1, len(sections)):
                        next_section_idx = current_result.find(sections[j], start_idx)
                        if next_section_idx != -1:
                            end_idx = next_section_idx
                            break

                    # 如果没有找到下一个分析部分，尝试找其他可能的结束标志
                    if end_idx == len(current_result):
                        for end_marker in ["【方面分析】", "【综合解读】", "【总结论】"]:
                            marker_idx = current_result.find(end_marker, start_idx)
                            if marker_idx != -1:
                                end_idx = marker_idx
                                break

                    analysis_sections[section] = current_result[start_idx:end_idx].strip()

            # 构建包含分析部分的聊天提示词
            analysis_context = ""
            for section, content in analysis_sections.items():
                if content:
                    analysis_context += f"{content}\n\n"

            # 执行RAG检索
            rag_context = ""
            rag_references = set()
            if self.rag_searcher:
                try:
                    # 从设置页面获取RAG配置参数
                    rag_result_count = 10  # 默认值
                    rag_threshold = 0.3  # 默认值

                    if hasattr(self, 'settings_frame') and self.settings_frame:
                        rag_result_count = self.settings_frame.get_rag_result_count()
                        rag_threshold = self.settings_frame.get_rag_threshold()
                    else:
                        # 如果设置页面不可用，从配置管理器获取
                        rag_result_count = config_manager.get('rag_result_count', 10)
                        rag_threshold = config_manager.get('rag_threshold', 0.3)

                    # 执行RAG搜索
                    search_query = f"{message}"
                    search_results = self.rag_searcher.search(
                        query=search_query,
                        search_method='hybrid',
                        top_k=rag_result_count,
                        similarity_threshold=rag_threshold,
                        use_query_expansion=True
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

                        logger.info(f"为聊天问题'{message[:30]}...'找到{len(search_results)}个相关参考")
                except Exception as e:
                    logger.error(f"聊天RAG搜索失败: {e}")
                    rag_context = ""
            
            chat_prompt = f"""{INTERPRETATION_CHAT_PROMPT}

【前期分析结果】
{analysis_context}
【完整解读结果】
{current_result}
【参考文件】
{rag_context}
【用户问题】
{message}

请基于上述解读结果和参考资料，针对用户的具体问题给出专业解答。解答中不要出现参考文件的序号及文件名。"""
            
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
                self._update_history_chat_messages(message, ai_response, search_results, is_error)
                
            except Exception as e:
                error_msg = f"抱歉，回复生成失败: {str(e)}"
                self.after(0, lambda: self.notebook_frame.add_ai_response(error_msg, is_error=True))
                
                # 更新当前历史记录中的聊天消息（错误情况）
                self._update_history_chat_messages(message, error_msg, None, True)
            
        except Exception as e:
            error_msg = f"聊天功能出错: {str(e)}"
            logger.error(error_msg)
            # 在主线程中更新UI
            self.after(0, lambda: self.notebook_frame.add_ai_response(error_msg, is_error=True))
            
            # 更新当前历史记录中的聊天消息（错误情况）
            self._update_history_chat_messages(message, error_msg, None, True)

    def _update_history_chat_messages(self, user_message, ai_response, references=None, is_error=False):
        """更新当前历史记录中的聊天消息"""
        try:
            # 添加RAG检索参考文档
            if references and not is_error:
                try:
                    # 格式化参考文档
                    references_text = "\n\n📚 参考文档:\n"
                    for i, doc in enumerate(references, 1):
                        # 截断过长的文档片段
                        snippet = doc['content'][:150] + '...' if len(doc['content']) > 150 else doc['content']
                        references_text += f"{i}. {references['source_file']} (相似度: {doc['similarity']:.2f})\n   {snippet}\n"

                    # 将参考文档添加到AI响应中
                    ai_response += references_text
                except Exception as e:
                    logger.error(f"处理参考文档失败: {str(e)}")
                    # 不中断对话流程，仅记录错误
            
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