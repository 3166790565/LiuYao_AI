import customtkinter as ctk

from config.languages import t
from config.settings import DEFAULT_MODEL
from config.ui_config import get_ui_settings
from utils.logger import setup_logger
from utils.ui import IOSEntry

# 设置日志记录器
logger = setup_logger(__name__)

class InputFrame(ctk.CTkFrame):
    """应用程序输入区域，包含问题输入、起卦方式和模型选择"""
    
    def __init__(self, master, command=None, **kwargs):
        # 获取UI设置
        self.ui_settings = get_ui_settings()
        
        super().__init__(
            master, 
            corner_radius=self.ui_settings['component']['card_corner_radius'],
            fg_color=self.ui_settings['colors']['card_bg'],
            **kwargs
        )
        
        # 保存父组件引用
        self.parent = master
        
        # 保存回调函数
        self.command = command if command else lambda: None
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        
        # 创建输入区域组件
        self.create_widgets()
    
    def create_widgets(self):
        """创建输入区域的组件"""
        try:
            logger.info("开始创建InputFrame组件")
            
            # 1. 问题输入区域
            self.create_question_input()
            
            # 2. 起卦方式选择区域
            self.create_divination_selection()
            
            # 3. 按钮区域
            self.create_button_area()
            
            logger.info("InputFrame组件创建完成")
            
        except Exception as e:
            logger.error(f"创建InputFrame组件时出错: {e}")
            raise
    
    def create_question_input(self):
        """创建问题输入区域"""
        try:
            # 问题输入区域框架 - 水平排列
            question_frame = ctk.CTkFrame(self, fg_color="transparent")
            question_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 10))
            question_frame.grid_columnconfigure(1, weight=1)  # 让输入框可以扩展
            
            # 问题输入标签
            self.question_label = ctk.CTkLabel(
                question_frame,
                text=t("input_question_label"),
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=14
                ),
                anchor="w",
                width=120
            )
            self.question_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=0)
            
            # 问题输入框 - 调整高度和宽度
            self.question_entry = IOSEntry(
                question_frame,
                placeholder=t("input_question_placeholder"),
                height=40,  # 降低高度
                width=600  # 增加宽度
            )
            self.question_entry.grid(row=0, column=1, sticky="ew", padx=0, pady=0)

            # 用神输入区域框架
            yongshen_frame = ctk.CTkFrame(self, fg_color="transparent")
            yongshen_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            yongshen_frame.grid_columnconfigure(1, weight=1)  # 让输入框可以扩展

            # 用神输入标签
            self.yongshen_label = ctk.CTkLabel(
                yongshen_frame,
                text="用神",
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=14
                ),
                anchor="w",
                width=120
            )
            self.yongshen_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=0)

            # 用神输入框
            self.yongshen_entry = IOSEntry(
                yongshen_frame,
                placeholder="请输入用神，例如：五爻子孙。或留空让AI自动判断用神。",
                height=40,
                width=600
            )
            self.yongshen_entry.grid(row=0, column=1, sticky="ew", padx=0, pady=0)

            # 方面输入区域框架
            fangmian_frame = ctk.CTkFrame(self, fg_color="transparent")
            fangmian_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
            fangmian_frame.grid_columnconfigure(1, weight=1)  # 让输入框可以扩展

            # 用神输入标签
            self.fangmian_label = ctk.CTkLabel(
                fangmian_frame,
                text="分析方面",
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=14
                ),
                anchor="w",
                width=120
            )
            self.fangmian_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=0)

            # 用神输入框
            self.fangmian_entry = IOSEntry(
                fangmian_frame,
                placeholder="请输入分析方面，用“ ”分割。或留空让AI自动判断方面。",
                height=40,
                width=600
            )
            self.fangmian_entry.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
            
            logger.info("问题输入区域创建成功")
            
        except Exception as e:
            logger.error(f"创建问题输入区域时出错: {e}")
            raise
    
    def create_divination_selection(self):
        """创建起卦方式选择区域"""
        try:
            # 起卦方式区域框架 - 水平排列
            divination_frame = ctk.CTkFrame(self, fg_color="transparent")
            divination_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
            divination_frame.grid_columnconfigure(1, weight=1)  # 让下拉框可以扩展
            
            # 起卦方式标签
            self.divination_label = ctk.CTkLabel(
                divination_frame,
                text=t("input_divination_label"),
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=14
                ),
                anchor="w",
                width=120
            )
            self.divination_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=0)
            
            # 起卦方式下拉选择框 - 改为下拉式选择
            divination_methods = [
                t("divination_liuyao"),
                t("divination_qimen"),
            ]
            self.divination_combobox = ctk.CTkComboBox(
                divination_frame,
                values=divination_methods,
                state="readonly",
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=12
                ),
                height=35,
                width=200
            )
            self.divination_combobox.set(divination_methods[0])
            self.divination_combobox.grid(row=0, column=1, sticky="w", padx=0, pady=0)
            
            logger.info("起卦方式选择区域创建成功")
            
        except Exception as e:
            logger.error(f"创建起卦方式选择区域时出错: {e}")
            raise
    

    
    def create_button_area(self):
        """创建按钮区域"""
        try:
            # 按钮容器框架 - 修复按钮布局和边框问题
            button_frame = ctk.CTkFrame(self, fg_color="transparent")
            button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(10, 20))
            
            # 配置按钮框架的网格布局，确保按钮居中
            button_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            # 分析按钮 - 修复配色为蓝色
            self.analyze_button = ctk.CTkButton(
                button_frame,
                text=t("btn_analyze"),
                command=self.on_analyze_click,
                width=100,
                height=35,
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=12
                ),
                corner_radius=8,
                fg_color=self.ui_settings['colors']['primary_color'],  # 蓝色主题色
                hover_color=self.ui_settings['colors']['primary_alpha_20']  # 蓝色悬停色
            )
            self.analyze_button.grid(row=0, column=0, padx=5, pady=5)
            
            # 清空按钮 - 修复配色为蓝色
            self.clear_button = ctk.CTkButton(
                button_frame,
                text=t("btn_clear"),
                command=self.on_clear_click,
                width=100,
                height=35,
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=12
                ),
                corner_radius=8,
                fg_color=self.ui_settings['colors']['primary_color'],  # 蓝色主题色
                hover_color=self.ui_settings['colors']['primary_alpha_20']  # 蓝色悬停色
            )
            self.clear_button.grid(row=0, column=1, padx=5, pady=5)
            
            # 导出按钮 - 修复配色为蓝色
            self.export_button = ctk.CTkButton(
                button_frame,
                text=t("btn_export"),
                command=self.on_export_click,
                width=100,
                height=35,
                font=ctk.CTkFont(
                    family=self.ui_settings['font_family'],
                    size=12
                ),
                corner_radius=8,
                fg_color=self.ui_settings['colors']['primary_color'],  # 蓝色主题色
                hover_color=self.ui_settings['colors']['primary_alpha_20'],  # 蓝色悬停色
                state="disabled"
            )
            self.export_button.grid(row=0, column=2, padx=5, pady=5)
            
            logger.info("按钮区域创建成功")
            
        except Exception as e:
            logger.error(f"创建按钮区域时出错: {e}")
            raise
    
    def on_divination_changed(self):
        """起卦方式改变时的回调函数"""
        try:
            selected_method = self.divination_combobox.get()
            logger.info(f"起卦方式已更改为: {selected_method}")
            
        except Exception as e:
            logger.error(f"处理起卦方式改变时出错: {e}")
    
    def on_analyze_click(self):
        """分析按钮点击事件"""
        try:
            question = self.get_question()
            if not question.strip():
                logger.warning("问题内容为空")
                return
            
            divination_method = self.get_divination_method()
            model = self.get_model()
            
            logger.info(f"开始分析 - 问题: {question[:50]}..., 方式: {divination_method}, 模型: {model}")
            
            # 调用回调函数
            if self.command:
                self.command()
            
        except Exception as e:
            logger.error(f"处理分析按钮点击时出错: {e}")
    
    def on_clear_click(self):
        """清空按钮点击事件"""
        try:
            self.question_entry.delete(0, 'end')
            self.divination_combobox.set("六爻")
            # 模型选择现在在设置页面管理
            
            logger.info("内容已清空")
            
        except Exception as e:
            logger.error(f"清空内容时出错: {e}")
    
    def on_export_click(self):
        """导出按钮点击事件"""
        try:
            # 获取主应用程序实例
            app = self.master
            while app and not hasattr(app, 'notebook_frame'):
                app = app.master
            
            if not app or not hasattr(app, 'notebook_frame'):
                logger.error("无法找到主应用程序实例")
                return
            
            # 检查是否有分析结果
            result_text = app.notebook_frame.result_text.get(1.0, "end-1c").strip()
            if not result_text:
                # 没有可导出的分析结果，记录到日志
                logger.warning("没有可导出的分析结果")
                return
            
            # 调用导出功能
            app.show_export_dialog()
            
        except Exception as e:
            logger.error(f"导出时出错: {e}")
    
    def get_question(self):
        """获取问题内容"""
        try:
            return self.question_entry.get()
        except Exception as e:
            logger.error(f"获取问题内容时出错: {e}")
            return ""

    def get_yongshen(self):
        """获取用神内容"""
        try:
            return self.yongshen_entry.get()
        except Exception as e:
            logger.error(f"获取用神内容时出错: {e}")
            return ""

    def set_yongshen(self, yongshen):
        """设置用神内容"""
        try:
            self.yongshen_entry.set(yongshen)
            logger.info(f"设置用神内容: {yongshen}")
        except Exception as e:
            logger.error(f"设置用神内容时出错: {e}")

    def get_fangmian(self):
        """获取方面内容"""
        try:
            return self.fangmian_entry.get()
        except Exception as e:
            logger.error(f"获取方面内容时出错: {e}")
            return ""

    def set_fangmian(self, fangmian):
        """设置方面内容"""
        try:
            self.fangmian_entry.set(fangmian)
            logger.info(f"设置方面内容: {fangmian}")
        except Exception as e:
            logger.error(f"设置方面内容时出错: {e}")

    def set_question(self, question):
        """设置问题内容"""
        try:
            self.question_entry.set(question)
            logger.info(f"设置问题内容: {question}")
        except Exception as e:
            logger.error(f"设置问题内容时出错: {e}")
    
    def get_divination_method(self):
        """获取起卦方式"""
        return "六爻"

        try:
            return self.divination_combobox.get()
        except Exception as e:
            logger.error(f"获取起卦方式时出错: {e}")
            return "六爻"
    
    def set_divination_method(self, method):
        """设置起卦方式"""
        try:
            self.divination_combobox.set(method)
        except Exception as e:
            logger.error(f"设置起卦方式时出错: {e}")
    
    def get_model(self):
        """获取选择的模型"""
        try:
            # 从设置页面获取默认模型
            if hasattr(self.parent, 'notebook_frame') and hasattr(self.parent.notebook_frame, 'settings_frame'):
                return self.parent.notebook_frame.settings_frame.get_default_model()
            return DEFAULT_MODEL
        except Exception as e:
            logger.error(f"获取模型时出错: {e}")
            return DEFAULT_MODEL
    
    def set_model(self, model):
        """设置模型"""
        try:
            # 模型选择现在在设置页面管理
            if hasattr(self.parent, 'notebook_frame') and hasattr(self.parent.notebook_frame, 'settings_frame'):
                self.parent.notebook_frame.settings_frame.set_default_model(model)
        except Exception as e:
            logger.error(f"设置模型时出错: {e}")
    
    def update_model_list(self):
        """更新模型列表"""
        try:
            # 模型列表现在在设置页面管理
            if hasattr(self.parent, 'notebook_frame') and hasattr(self.parent.notebook_frame, 'settings_frame'):
                self.parent.notebook_frame.settings_frame.refresh_model_list()
            logger.info("模型列表更新请求已发送到设置页面")
        except Exception as e:
            logger.error(f"更新模型列表时出错: {e}")
    
    def set_buttons_state(self, state):
        """设置按钮状态"""
        try:
            self.analyze_button.configure(state=state)
            self.clear_button.configure(state=state)
            
        except Exception as e:
            logger.error(f"设置按钮状态时出错: {e}")
    
    def enable_export(self):
        """启用导出按钮"""
        try:
            self.export_button.configure(state="normal")
            
        except Exception as e:
            logger.error(f"启用导出按钮时出错: {e}")
    

    
    def update_theme(self):
        """更新主题颜色"""
        try:
            # 更新UI设置
            self.ui_settings = get_ui_settings()
            colors = self.ui_settings['colors']
            
            # 更新frame背景色
            self.configure(fg_color=colors['card_bg'])
            
            # 更新所有子组件的颜色
            # 问题输入框
            if hasattr(self, 'question_entry') and hasattr(self.question_entry, 'update_theme'):
                self.question_entry.update_theme()
            # 用神输入框
            if hasattr(self, 'yongshen_entry') and hasattr(self.yongshen_entry, 'update_theme'):
                self.yongshen_entry.update_theme()
            # 方面输入框
            if hasattr(self, 'fangmian_entry') and hasattr(self.fangmian_entry, 'update_theme'):
                self.fangmian_entry.update_theme()
            
            # 起卦方式选择框 (customtkinter组件)
            if hasattr(self, 'divination_combobox'):
                self.divination_combobox.configure(
                    fg_color=colors['bg_color'],
                    text_color=colors['text_color'],
                    dropdown_fg_color=colors['card_bg'],
                    dropdown_text_color=colors['text_color']
                )
            
            # 模型选择现在在设置页面管理
            
            # 按钮组
            if hasattr(self, 'analyze_button'):
                self.analyze_button.configure(
                    fg_color=colors['primary_color'],
                    hover_color=colors['primary_alpha_20']
                )
            
            if hasattr(self, 'clear_button'):
                self.clear_button.configure(
                    fg_color=colors['gray_3'],
                    hover_color=colors['gray_4']
                )
            
            if hasattr(self, 'export_button'):
                self.export_button.configure(
                    fg_color=colors['secondary_color'],
                    hover_color=colors['secondary_alpha_20']
                )
                
            logger.debug("InputFrame主题已更新")
        except Exception as e:
            logger.error(f"更新InputFrame主题时出错: {e}")