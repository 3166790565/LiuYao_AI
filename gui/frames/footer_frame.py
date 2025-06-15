# gui/frames/footer_frame.py

import customtkinter as ctk
import tkinter as tk
from config import constants
from config.ui_config import UI_SETTINGS
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FooterFrame(ctk.CTkFrame):
    """应用程序底部区域，包含版权信息和其他底部元素"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master, 
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            **kwargs
        )
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        
        # 创建底部区域组件
        self.create_widgets()
    
    def create_widgets(self):
        """创建底部区域的组件"""
        # 版权信息标签
        self.copyright_var = tk.StringVar(value=f"© {constants.COPYRIGHT_YEAR} {constants.AUTHOR}")
        self.copyright_label = ctk.CTkLabel(
            self,
            textvariable=self.copyright_var,
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            ),
            text_color=UI_SETTINGS['colors']['secondary_text'],
            anchor="center"
        )
        self.copyright_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    
    def update_theme(self):
        """更新主题颜色"""
        try:
            from config.ui_config import get_ui_settings
            ui_settings = get_ui_settings()
            colors = ui_settings['colors']
            
            # 更新frame背景色
            self.configure(fg_color=colors['card_bg'])
            
            # 更新版权标签颜色
            if hasattr(self, 'copyright_label'):
                self.copyright_label.configure(
                    text_color=colors['secondary_text']
                )
                
            logger.debug("FooterFrame主题已更新")
        except Exception as e:
            logger.error(f"更新FooterFrame主题时出错: {e}")