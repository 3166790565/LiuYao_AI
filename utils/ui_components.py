# utils/ui_components.py
# 现代化UI组件库，支持主题系统

import tkinter as tk
from tkinter import ttk, font
import time
import threading
from typing import Callable, Any, Dict, List, Tuple, Optional, Union
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 尝试导入PIL用于图像处理
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 尝试导入customtkinter用于现代UI组件
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# 导入配置和工具
from config.ui_config import get_ui_settings
from utils.animation import fade_in, fade_out, slide_in, slide_out, pulse_animation, typing_animation


# 导入所需的基类和函数
from utils.ui import create_rounded_rectangle, ThemeableWidget


class IOSButton(tk.Frame, ThemeableWidget):
    """iOS风格按钮，支持主题系统"""
    
    def __init__(
        self,
        master,
        text="",
        command=None,
        width=100,
        height=40,
        bg_color=None,
        text_color=None,
        hover_color=None,
        active_color=None,
        border_radius=None,
        font_size=None,
        font_family=None,
        icon=None,
        icon_size=(20, 20),
        **kwargs
    ):
        # 先初始化ThemeableWidget以获取colors属性
        ThemeableWidget.__init__(self)
        
        # 安全地获取背景色
        try:
            if CTK_AVAILABLE and isinstance(master, ctk.CTkFrame):
                master_bg = master.cget("fg_color")
                # 如果是transparent，使用默认背景色
                if master_bg == "transparent":
                    bg_color = self.get_color("card_bg")
                else:
                    bg_color = master_bg
            else:
                bg_color = self.get_color("card_bg")
        except Exception:
            bg_color = self.get_color("card_bg")
        
        tk.Frame.__init__(self, master, bg=bg_color, **kwargs)
        
        # 获取组件设置
        component_settings = self.ui_settings["component"]
        
        # 设置默认值
        self.command = command
        self.bg_color = bg_color or self.get_color("primary_color")
        self.text_color = text_color or self.get_color("text_color")
        self.border_radius = border_radius or component_settings["button_corner_radius"]
        self.height = height or component_settings["button_height"]
        self.border_radius = min(self.border_radius, self.height // 2)
        self.font_family = font_family or self.ui_settings["font_family"]
        # 确保字体大小是整数
        try:
            self.font_size = int(font_size or self.ui_settings["font_size"])
        except (ValueError, TypeError):
            self.font_size = 12  # 默认字体大小
        
        # 计算悬停和激活颜色
        self.hover_color = hover_color or self._adjust_color(self.bg_color, 1.1)
        self.active_color = active_color or self._adjust_color(self.bg_color, 0.9)
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=self.height,
            bg=self["bg"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 创建按钮背景
        self.bg_rect = create_rounded_rectangle(
            self.canvas, 0, 0, width, self.height,
            radius=self.border_radius,
            fill=self.bg_color,
            outline=""
        )
        
        # 创建文本和图标
        self.text_id = None
        self.icon_id = None
        
        if icon and PIL_AVAILABLE:
            # 加载并调整图标大小
            try:
                self.icon_image = Image.open(icon)
                self.icon_image = self.icon_image.resize(icon_size, Image.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(self.icon_image)
                
                # 计算图标位置
                icon_x = width // 2 - icon_size[0] // 2
                if text:
                    icon_x = 10  # 如果有文本，图标靠左
                
                self.icon_id = self.canvas.create_image(
                    icon_x + icon_size[0] // 2,
                    self.height // 2,
                    image=self.icon_photo
                )
            except Exception as e:
                logger.error(f"无法加载图标: {e}")
        
        if text:
            # 创建文本
            text_x = width // 2
            if icon and self.icon_id and PIL_AVAILABLE:
                text_x = width // 2 + 10  # 如果有图标，文本稍微右移
            
            self.text_id = self.canvas.create_text(
                text_x, self.height // 2,
                text=text,
                fill=self.text_color,
                font=(self.font_family, self.font_size)
            )
        
        # 绑定事件
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
    
    def _adjust_color(self, hex_color, factor):
        """调整颜色亮度"""
        try:
            # 移除#前缀
            hex_color = hex_color.lstrip('#')
            
            # 处理带透明度的颜色值（8位十六进制）
            if len(hex_color) == 8:
                hex_color = hex_color[:6]  # 只保留RGB部分，移除透明度
            
            # 确保颜色值长度为6位（RGB）
            if len(hex_color) != 6:
                # 如果颜色格式不正确，返回安全的默认颜色
                return "#007aff" if factor > 1 else "#0055cc"
            
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # 调整亮度
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        except ValueError:
            # 如果颜色值解析失败，返回安全的默认颜色
            return "#007aff" if factor > 1 else "#0055cc"
    
    def _on_enter(self, event):
        """鼠标进入事件"""
        self.canvas.itemconfig(self.bg_rect, fill=self.hover_color)
    
    def _on_leave(self, event):
        """鼠标离开事件"""
        self.canvas.itemconfig(self.bg_rect, fill=self.bg_color)
    
    def _on_press(self, event):
        """鼠标按下事件"""
        self.canvas.itemconfig(self.bg_rect, fill=self.active_color)
    
    def _on_release(self, event):
        """鼠标释放事件"""
        self.canvas.itemconfig(self.bg_rect, fill=self.hover_color)
        if self.command:
            self.command()
    
    def configure(self, **kwargs):
        """配置按钮属性"""
        if "text" in kwargs and self.text_id:
            self.canvas.itemconfig(self.text_id, text=kwargs["text"])
        
        if "bg_color" in kwargs:
            self.bg_color = kwargs["bg_color"]
            self.hover_color = self._adjust_color(self.bg_color, 1.1)
            self.active_color = self._adjust_color(self.bg_color, 0.9)
            self.canvas.itemconfig(self.bg_rect, fill=self.bg_color)
        
        if "text_color" in kwargs and self.text_id:
            self.text_color = kwargs["text_color"]
            self.canvas.itemconfig(self.text_id, fill=self.text_color)
    
    def update_theme(self):
        """更新主题颜色"""
        super().update_theme()
        
        # 更新按钮颜色
        self.bg_color = self.get_color("primary_color")
        self.text_color = self.get_color("text_color")
        self.hover_color = self._adjust_color(self.bg_color, 1.1)
        self.active_color = self._adjust_color(self.bg_color, 0.9)
        
        # 应用新颜色
        self.canvas.itemconfig(self.bg_rect, fill=self.bg_color)
        if self.text_id:
            self.canvas.itemconfig(self.text_id, fill=self.text_color)


class IOSMessageBox:
    """iOS风格消息框"""
    
    @staticmethod
    def showinfo(title, message):
        """显示信息消息框（已禁用）"""
        # 弹窗已移除，不再显示
        return None
        # 弹窗代码已移除
    
    @staticmethod
    def show_success(parent, title, message):
        """显示成功消息框（已禁用）"""
        # 弹窗已移除，不再显示
        return None
        # 弹窗代码已移除
    
    @staticmethod
    def show_error(parent, title, message):
        """显示错误消息框（别名方法）"""
        return IOSMessageBox.showerror(title, message)
    
    @staticmethod
    def show_warning(parent, title, message):
        """显示警告消息框（已禁用）"""
        # 弹窗已移除，不再显示
        return None
        # 弹窗代码已移除
    
    @staticmethod
    def show_question(parent, title, message):
        """显示询问消息框（已禁用）"""
        # 弹窗已移除，默认返回False（取消）
        return False
        # 弹窗代码已移除
    
    @staticmethod
    def askyesno(title, message):
        """询问是否确认（别名方法）"""
        return IOSMessageBox.show_question(None, title, message)
    
    @staticmethod
    def showerror(title, message):
        """显示错误消息框（已禁用）"""
        # 弹窗已移除，不再显示
        return None
        # 弹窗代码已移除