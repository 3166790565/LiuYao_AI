# gui/frames/status_frame.py

import tkinter as tk

import customtkinter as ctk

from config.constants import APP_VERSION
from config.languages import t
from config.ui_config import UI_SETTINGS
from utils.logger import setup_logger

logger = setup_logger(__name__)

class StatusFrame(ctk.CTkFrame):
    """应用程序状态栏区域，包含进度条、状态标签和版本信息"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master, 
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            **kwargs
        )
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)  # 进度条
        self.grid_columnconfigure(1, weight=0)  # 状态标签
        self.grid_columnconfigure(2, weight=0)  # 版本标签
        
        # 初始化状态标识
        self.is_initializing = False
        self.original_bg_color = UI_SETTINGS['colors']['card_bg']
        
        # 创建状态栏组件
        self.create_widgets()
    
    def create_widgets(self):
        """创建状态栏的组件"""
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self,
            variable=self.progress_var,
            mode="determinate",
            height=15,  # 进一步增加高度
            corner_radius=UI_SETTINGS['component']['progressbar_corner_radius'],
            progress_color=UI_SETTINGS['colors']['primary_color'],
            fg_color=UI_SETTINGS['colors']['gray_2']
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=8)
        self.progress_bar.set(0)  # 初始化进度为0
        
        # 状态标签
        self.status_var = tk.StringVar(value=t("status_ready"))
        self.status_label = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=14,  # 增加字体大小
                weight="bold"  # 加粗字体
            ),
            width=140,  # 进一步增加宽度
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=8, pady=8)
        
        # 版本标签
        self.version_label = ctk.CTkLabel(
            self,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            ),
            text_color=UI_SETTINGS['colors']['secondary_text'],
            width=50,
            anchor="e"
        )
        self.version_label.grid(row=0, column=2, sticky="e", padx=5, pady=8)
        
    def update_progress(self, value):
        """更新进度条值"""
        self.progress_var.set(value)
        
        # 如果正在初始化，使进度条更显眼
        if self.is_initializing and hasattr(self, 'progress_bar'):
            # 使用更亮的颜色和更大的高度
            self.progress_bar.configure(
                progress_color="#0078d4",  # 微软蓝色，更显眼
                height=18  # 更大的高度
            )
        
        self.update_idletasks()  # 强制更新UI
    
    def update_status(self, status):
        """更新状态标签文本"""
        self.status_var.set(status)
        
        # 检查是否为初始化状态
        initialization_keywords = ["正在", "初始化", "加载", "检查", "构建"]
        self.is_initializing = any(keyword in status for keyword in initialization_keywords)
        
        if self.is_initializing:
            # 初始化时使用更显眼的样式
            self.status_label.configure(
                text_color="#ffffff",  # 白色文字，更显眼
                font=ctk.CTkFont(
                    family=UI_SETTINGS['font_family'],
                    size=15,  # 更大字体
                    weight="bold"
                )
            )
            # 改变背景色以突出显示
            self.configure(fg_color="#0078d4")  # 蓝色背景
            # 添加动画效果
            self._animate_status()
        else:
            # 恢复正常样式
            self.status_label.configure(
                text_color=UI_SETTINGS['colors']['text_color'],
                font=ctk.CTkFont(
                    family=UI_SETTINGS['font_family'],
                    size=14,
                    weight="bold"
                )
            )
            # 恢复原背景色
            self.configure(fg_color=self.original_bg_color)
            # 停止动画
            if hasattr(self, '_animation_job'):
                self.after_cancel(self._animation_job)
    
    def _animate_status(self):
        """为初始化状态添加动画效果"""
        if not self.is_initializing:
            return
            
        # 获取当前状态文本
        current_text = self.status_var.get()
        
        # 添加动画点
        if current_text.endswith("..."):
            new_text = current_text[:-3]
        elif current_text.endswith(".."):
            new_text = current_text + "."
        elif current_text.endswith("."):
            new_text = current_text + "."
        else:
            new_text = current_text + "."
        
        self.status_var.set(new_text)
        
        # 添加背景色闪烁效果
        current_bg = self.cget("fg_color")
        if current_bg == "#0078d4":
            self.configure(fg_color="#106ebe")  # 稍深的蓝色
        else:
            self.configure(fg_color="#0078d4")  # 原蓝色
        
        # 继续动画
        self._animation_job = self.after(600, self._animate_status)  # 稍快的动画
    
    def update_texts(self):
        """更新界面文本"""
        # 更新状态文本
        if not self.is_initializing:
            self.status_var.set(t("status_ready"))
    
    def reset(self):
        """重置状态栏"""
        self.is_initializing = False
        
        # 停止动画
        if hasattr(self, '_animation_job'):
            self.after_cancel(self._animation_job)
        
        self.update_progress(0)
        self.update_status(t("status_ready"))
        
        # 恢复进度条正常样式
        if hasattr(self, 'progress_bar'):
            self.progress_bar.configure(
                progress_color=UI_SETTINGS['colors']['primary_color'],
                height=15
            )
        
        # 恢复背景色
        self.configure(fg_color=self.original_bg_color)
    
    def show_message(self, message, duration=3000):
        """显示临时消息"""
        try:
            # 保存当前状态
            current_status = self.status_var.get()
            
            # 显示消息
            self.update_status(message)
            
            # 设置定时器恢复原状态
            def restore_status():
                self.update_status(current_status)
            
            self.after(duration, restore_status)
            logger.debug(f"显示状态消息: {message}")
        except Exception as e:
            logger.error(f"显示状态消息失败: {e}")
    
    def update_theme(self):
        """更新主题颜色"""
        try:
            from config.ui_config import get_ui_settings
            ui_settings = get_ui_settings()
            colors = ui_settings['colors']
            
            # 更新原始背景色
            self.original_bg_color = colors['card_bg']
            
            # 如果不在初始化状态，更新frame背景色
            if not self.is_initializing:
                self.configure(fg_color=colors['card_bg'])
            
            # 更新进度条颜色
            if hasattr(self, 'progress_bar') and not self.is_initializing:
                self.progress_bar.configure(
                    progress_color=colors['primary_color'],
                    fg_color=colors['gray_2']
                )
            
            # 更新状态标签颜色（如果不在初始化状态）
            if hasattr(self, 'status_label') and not self.is_initializing:
                self.status_label.configure(
                    text_color=colors['text_color']
                )
            
            # 更新版本标签颜色
            if hasattr(self, 'version_label'):
                self.version_label.configure(
                    text_color=colors['secondary_text']
                )
                
            logger.debug("StatusFrame主题已更新")
        except Exception as e:
            logger.error(f"更新StatusFrame主题时出错: {e}")