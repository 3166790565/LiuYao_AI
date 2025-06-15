# gui/frames/header_frame.py

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os

from config import RESOURCES_DIR
from config.constants import APP_NAME, APP_VERSION
from config.constants import TEXT
from config.ui_config import get_ui_settings
from utils.resources import load_svg_icon
from utils.animation import pulse_animation
from utils.ui_components import ThemeableWidget, IOSButton
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HeaderFrame(ctk.CTkFrame, ThemeableWidget):
    """应用程序头部区域，包含标题、副标题和主题切换按钮"""
    
    def __init__(self, master, **kwargs):
        # 初始化主题
        ThemeableWidget.__init__(self)
        
        # 获取UI设置
        self.ui_settings = get_ui_settings()
        
        # 初始化框架
        ctk.CTkFrame.__init__(
            self,
            master, 
            corner_radius=self.ui_settings["component"]["card_corner_radius"],
            fg_color=self.get_color("card_bg"),
            **kwargs
        )
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        
        # 创建标题和副标题
        self.create_widgets()
    
    def create_widgets(self):
        """创建头部区域的组件"""
        # 配置网格
        self.grid_columnconfigure(0, weight=1)  # 标题列可扩展
        self.grid_columnconfigure(1, weight=0)  # 主题切换按钮列固定宽度
        
        # 创建标题框架
        title_container = ctk.CTkFrame(self, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # 加载应用图标
        self.app_icon = None
        try:
            # 尝试加载PNG图标
            icon_path = os.path.join(RESOURCES_DIR, "icons", "app_icon.png")
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((40, 40), Image.LANCZOS)
                self.app_icon = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(40, 40))
                
                # 创建图标标签
                self.icon_label = ctk.CTkLabel(
                    title_container,
                    image=self.app_icon,
                    text=""
                )
                self.icon_label.pack(side="left", padx=(0, 10))
            else:
                # 如果图标文件不存在，创建一个简单的文本标签
                self.icon_label = ctk.CTkLabel(
                    title_container,
                    text="🔮",
                    font=ctk.CTkFont(size=24)
                )
                self.icon_label.pack(side="left", padx=(0, 10))
        except Exception as e:
            logger.error(f"无法加载应用图标: {e}")
            # 创建一个简单的文本标签作为备用
            self.icon_label = ctk.CTkLabel(
                title_container,
                text="🔮",
                font=ctk.CTkFont(size=24)
            )
            self.icon_label.pack(side="left", padx=(0, 10))
        
        # 标题标签 - 使用大号字体和主题色
        self.title_label = ctk.CTkLabel(
            title_container,
            text=APP_NAME,
            font=ctk.CTkFont(
                family=self.ui_settings["font_family"],
                size=24,
                weight="bold"
            ),
            text_color=self.get_color("primary_color")
        )
        self.title_label.pack(side="left")
        
        # 版本标签
        self.version_label = ctk.CTkLabel(
            title_container,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(
                family=self.ui_settings["font_family"],
                size=12
            ),
            text_color=self.get_color("secondary_text")
        )
        self.version_label.pack(side="left", padx=(5, 0), pady=(8, 0))
        
        # 副标题标签 - 使用较小字体和次要颜色
        self.subtitle_label = ctk.CTkLabel(
            self,
            text=TEXT['zh_CN']['subtitle'],
            font=ctk.CTkFont(
                family=self.ui_settings["font_family"],
                size=14
            ),
            text_color=self.get_color("secondary_text")
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        # 创建按钮容器
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=20, pady=10)
        
        # 设置按钮已移除
        
        # 创建主题切换按钮
        self.theme_button = IOSButton(
            button_frame,
            text="切换主题",
            command=self.toggle_theme,
            width=100,
            bg_color=self.get_color("secondary_color"),
            text_color=self.get_color("text_color")
        )
        self.theme_button.pack(side="left")
        
        # 应用脉冲动画到标题
        if self.ui_settings["animation"]["enabled"]:
            # 使用不带透明度的颜色
            start_color = self.get_color("primary_color")
            end_color = self.get_color("gray_2")
            self.after(1000, lambda: pulse_animation(
                self.title_label, 
                property_name='text_color', 
                start_color=start_color,
                end_color=end_color,
                scale_factor=1.05, 
                duration=self.ui_settings["animation"]["duration"]
            ))
    
    # show_settings方法已移除
    
    def toggle_theme(self):
        """切换主题模式"""
        # 调用主应用程序的主题切换方法
        self.master.toggle_theme()
        
        # 更新自身主题
        self.update_theme()
    
    def update_theme(self):
        """更新主题颜色"""
        super().update_theme()
        
        # 更新框架颜色
        self.configure(fg_color=self.get_color("card_bg"))
        
        # 更新标题颜色
        self.title_label.configure(text_color=self.get_color("primary_color"))
        self.subtitle_label.configure(text_color=self.get_color("secondary_text"))
        self.version_label.configure(text_color=self.get_color("secondary_text"))
        
        # 更新图标背景色（如果是tk.Label）
        if hasattr(self, 'icon_label') and isinstance(self.icon_label, tk.Label):
            self.icon_label.configure(bg=self.get_color("card_bg"))
        
        # 设置按钮更新代码已移除
        
        # 更新主题按钮颜色
        self.theme_button.update_theme()
    

    
    def set_title(self, title):
        """设置标题文本"""
        self.title_label.configure(text=title)
    
    def set_subtitle(self, subtitle):
        """设置副标题文本"""
        self.subtitle_label.configure(text=subtitle)