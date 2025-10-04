# UI工具函数和自定义控件

import re
import tkinter as tk
from tkinter import font

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
from utils.animation import fade_in, fade_out


# ThemeableWidget类定义
class ThemeableWidget:
    """可主题化的组件基类，提供主题颜色获取和应用的功能"""
    
    def __init__(self):
        from config.ui_config import get_ui_settings
        self.ui_settings = get_ui_settings()
        self.colors = self.ui_settings["colors"]
    
    def get_color(self, color_name, default=None):
        """获取主题颜色
        
        Args:
            color_name (str): 颜色名称
            default (str, optional): 默认颜色
            
        Returns:
            str: 颜色值
        """
        return self.colors.get(color_name, default)
    
    def update_theme(self):
        """更新主题颜色，子类应重写此方法以应用新的主题颜色"""
        from config.ui_config import get_ui_settings
        self.ui_settings = get_ui_settings()
        self.colors = self.ui_settings["colors"]


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """在画布上创建圆角矩形
    
    Args:
        canvas: 画布对象
        x1, y1: 左上角坐标
        x2, y2: 右下角坐标
        radius: 圆角半径
        **kwargs: 传递给canvas.create_polygon的参数
        
    Returns:
        int: 创建的多边形ID
    """
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class IOSButton(tk.Frame):
    """iOS风格按钮"""
    
    def __init__(
        self,
        master,
        text="",
        command=None,
        width=100,
        height=40,
        bg_color="#007AFF",
        text_color="white",
        hover_color=None,
        active_color=None,
        border_radius=8,
        font_family="SF Pro Display",
        font_size=16,
        font_weight="normal",
        state="normal",
        **kwargs
    ):
        # 安全地获取背景色
        try:
            if hasattr(master, "cget"):
                bg_color = master.cget("bg")
            else:
                # 尝试从主题获取背景色
                from config.themes import get_theme
                from config.ui_config import get_ui_settings
                ui_settings = get_ui_settings()
                theme = get_theme(ui_settings["appearance_mode"])
                bg_color = theme["card_bg"]
        except Exception:
            # 如果失败，使用默认背景色
            from config.themes import get_theme
            from config.ui_config import get_ui_settings
            try:
                ui_settings = get_ui_settings()
                theme = get_theme(ui_settings["appearance_mode"])
                bg_color = theme["card_bg"]
            except:
                bg_color = self.get_color("card_bg", "#ffffff")
        super().__init__(master, bg=bg_color, **kwargs)
        ThemeableWidget.__init__(self)
        
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color or self._adjust_color(bg_color, 0.8)
        self.active_color = active_color or self._adjust_color(bg_color, 0.6)
        self.border_radius = border_radius
        self.font_family = font_family
        self.font_size = font_size
        self.font_weight = font_weight
        self.state = state
        
        self.current_color = self.bg_color
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=bg_color
        )
        self.canvas.pack()
        
        # 绘制按钮
        self._draw_button()
        
        # 绑定事件
        if self.state == "normal":
            self.canvas.bind("<Enter>", self._on_enter)
            self.canvas.bind("<Leave>", self._on_leave)
            self.canvas.bind("<Button-1>", self._on_press)
            self.canvas.bind("<ButtonRelease-1>", self._on_release)
    
    def _draw_button(self):
        """绘制按钮"""
        self.canvas.delete("all")
        
        # 绘制圆角矩形背景
        create_rounded_rectangle(
            self.canvas,
            2, 2, self.width - 2, self.height - 2,
            radius=self.border_radius,
            fill=self.current_color,
            outline=""
        )
        
        # 绘制文本
        font_obj = font.Font(
            family=self.font_family,
            size=self.font_size,
            weight=self.font_weight
        )
        
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text=self.text,
            fill=self.text_color,
            font=font_obj,
            anchor="center"
        )
    
    def _adjust_color(self, color, factor):
        """调整颜色亮度"""
        try:
            # 移除#号
            color = color.lstrip('#')
            # 转换为RGB
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # 调整亮度
            rgb = tuple(int(c * factor) for c in rgb)
            # 确保值在0-255范围内
            rgb = tuple(max(0, min(255, c)) for c in rgb)
            # 转换回十六进制
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        except:
            return color
    
    def _on_enter(self, event):
        if self.state == "normal":
            self.current_color = self.hover_color
            self._draw_button()
    
    def _on_leave(self, event):
        if self.state == "normal":
            self.current_color = self.bg_color
            self._draw_button()
    
    def _on_press(self, event):
        if self.state == "normal":
            self.current_color = self.active_color
            self._draw_button()
    
    def _on_release(self, event):
        if self.state == "normal":
            self.current_color = self.hover_color
            self._draw_button()
            if self.command:
                self.command()
    
    def configure(self, **kwargs):
        """配置按钮属性"""
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "bg_color" in kwargs:
            self.bg_color = kwargs["bg_color"]
            self.current_color = self.bg_color
            self.hover_color = self._adjust_color(self.bg_color, 0.8)
            self.active_color = self._adjust_color(self.bg_color, 0.6)
        if "text_color" in kwargs:
            self.text_color = kwargs["text_color"]
        if "state" in kwargs:
            self.state = kwargs["state"]
            if self.state == "disabled":
                self.current_color = self._adjust_color(self.bg_color, 0.5)
                self.canvas.unbind("<Enter>")
                self.canvas.unbind("<Leave>")
                self.canvas.unbind("<Button-1>")
                self.canvas.unbind("<ButtonRelease-1>")
            else:
                self.current_color = self.bg_color
                self.canvas.bind("<Enter>", self._on_enter)
                self.canvas.bind("<Leave>", self._on_leave)
                self.canvas.bind("<Button-1>", self._on_press)
                self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        self._draw_button()
        
        # 传递其他参数给父类
        super().configure(**{k: v for k, v in kwargs.items() if k not in [
            "text", "bg_color", "text_color", "state"
        ]})


class IOSEntry(tk.Frame, ThemeableWidget):
    """iOS风格输入框"""
    
    def __init__(
        self,
        master,
        placeholder="",
        width=200,
        height=40,
        bg_color=None,
        text_color="#000000",
        placeholder_color="#8E8E93",
        border_color="#C7C7CC",
        focus_color="#007AFF",
        border_radius=8,
        font_family="SF Pro Display",
        font_size=16,
        **kwargs
    ):
        # 安全地获取背景色
        if bg_color is None:
            from config.ui_config import get_ui_settings
            ui_settings = get_ui_settings()
            bg_color = ui_settings["colors"].get("card_bg", "#ffffff")
        
        try:
            if bg_color is None:
                bg_color = master.cget("bg")
        except:
            try:
                fg_color = master.cget("fg_color")
                # 如果fg_color是复合颜色值或None，使用默认背景色
                if fg_color is None or isinstance(fg_color, (list, tuple)) or " " in str(fg_color):
                    from config.ui_config import get_ui_settings
                    ui_settings = get_ui_settings()
                    bg_color = ui_settings["colors"].get("card_bg", "#F2F2F7")  # 使用主题背景色
                else:
                    bg_color = fg_color
            except:
                from config.ui_config import get_ui_settings
                ui_settings = get_ui_settings()
                bg_color = ui_settings["colors"].get("card_bg", "#F2F2F7")  # 使用主题背景色
        
        super().__init__(master, bg=bg_color, **kwargs)
        ThemeableWidget.__init__(self)
        
        self.placeholder = placeholder
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.placeholder_color = placeholder_color
        self.border_color = border_color
        self.focus_color = focus_color
        self.border_radius = border_radius
        self.font_family = font_family
        self.font_size = font_size
        
        self.is_focused = False
        self.showing_placeholder = True
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=bg_color
        )
        self.canvas.pack()
        
        # 创建输入框
        self.entry = tk.Entry(
            self.canvas,
            font=(self.font_family, self.font_size),
            bg=self.bg_color,
            fg=self.placeholder_color,
            bd=0,
            highlightthickness=0,
            insertbackground=self.text_color
        )
        
        # 设置占位符
        self.entry.insert(0, self.placeholder)
        
        # 绘制边框
        self._draw_border()
        
        # 放置输入框
        self.canvas.create_window(
            self.border_radius + 5,
            self.height // 2,
            anchor="w",
            window=self.entry,
            width=self.width - 2 * (self.border_radius + 5)
        )
        
        # 绑定事件
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
    
    def _draw_border(self):
        """绘制边框"""
        self.canvas.delete("border")
        
        color = self.focus_color if self.is_focused else self.border_color
        
        create_rounded_rectangle(
            self.canvas,
            1, 1, self.width - 1, self.height - 1,
            radius=self.border_radius,
            fill=self.bg_color,
            outline=color,
            width=2,
            tags="border"
        )
    
    def _on_focus_in(self, event):
        """获得焦点时的处理"""
        self.is_focused = True
        self._draw_border()
        
        if self.showing_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.text_color)
            self.showing_placeholder = False
    
    def _on_focus_out(self, event):
        """失去焦点时的处理"""
        self.is_focused = False
        self._draw_border()
        
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
            self.showing_placeholder = True
    
    def get(self):
        """获取输入框的值"""
        if self.showing_placeholder:
            return ""
        return self.entry.get()
    
    def set(self, value):
        """设置输入框的值"""
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, value)
            self.entry.config(fg=self.text_color)
            self.showing_placeholder = False
        else:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
            self.showing_placeholder = True
    
    def configure(self, **kwargs):
        """配置输入框属性"""
        if "placeholder" in kwargs:
            self.placeholder = kwargs["placeholder"]
            if self.showing_placeholder:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, self.placeholder)
        
        if "bg_color" in kwargs:
            self.bg_color = kwargs["bg_color"]
            self.canvas.config(bg=self.bg_color)
            self.entry.config(bg=self.bg_color)
            self._draw_border()
        
        if "text_color" in kwargs:
            self.text_color = kwargs["text_color"]
            if not self.showing_placeholder:
                self.entry.config(fg=self.text_color)
        
        # 传递其他参数给父类
        super().configure(**{k: v for k, v in kwargs.items() if k not in [
            "placeholder", "bg_color", "text_color"
        ]})
    
    def update_theme(self):
        """更新主题颜色"""
        ThemeableWidget.update_theme(self)
        # 更新背景色
        new_bg_color = self.get_color("card_bg", "#F2F2F7")
        self.bg_color = new_bg_color
        self.config(bg=new_bg_color)
        self.canvas.config(bg=new_bg_color)
        self.entry.config(bg=new_bg_color)
        
        # 更新文本颜色
        new_text_color = self.get_color("text_color", "#000000")
        self.text_color = new_text_color
        if not self.showing_placeholder:
            self.entry.config(fg=new_text_color)
        
        # 更新占位符颜色
        new_placeholder_color = self.get_color("gray_3", "#8E8E93")
        self.placeholder_color = new_placeholder_color
        if self.showing_placeholder:
            self.entry.config(fg=new_placeholder_color)
        
        self._draw_border()


class IOSProgressBar(tk.Frame, ThemeableWidget):
    """iOS风格进度条"""
    
    def __init__(
        self,
        master,
        width=200,
        height=6,
        bg_color="#E5E5EA",
        fg_color="#007AFF",
        border_radius=3,
        value=0,
        max_value=100,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        ThemeableWidget.__init__(self)
        
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_radius = border_radius
        self.value = value
        self.max_value = max_value
        
        # 创建画布
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=self.get_color("bg_color", "#f0f0f0")
        )
        self.canvas.pack()
        
        # 绘制进度条
        self._draw_progress()
    
    def _draw_progress(self):
        """绘制进度条"""
        self.canvas.delete("all")
        
        # 绘制背景
        create_rounded_rectangle(
            self.canvas,
            0, 0, self.width, self.height,
            radius=self.border_radius,
            fill=self.bg_color,
            outline=""
        )
        
        # 计算进度宽度
        progress_width = (self.value / self.max_value) * self.width
        
        if progress_width > 0:
            # 绘制进度
            create_rounded_rectangle(
                self.canvas,
                0, 0, progress_width, self.height,
                radius=self.border_radius,
                fill=self.fg_color,
                outline=""
            )
    
    def set(self, value):
        """设置进度值"""
        self.value = max(0, min(self.max_value, value))
        self._draw_progress()
    
    def get(self):
        """获取当前进度值"""
        return self.value
    
    def configure(self, **kwargs):
        """配置进度条属性"""
        if "bg_color" in kwargs:
            self.bg_color = kwargs["bg_color"]
        if "fg_color" in kwargs:
            self.fg_color = kwargs["fg_color"]
        if "value" in kwargs:
            self.value = kwargs["value"]
        if "max_value" in kwargs:
            self.max_value = kwargs["max_value"]
        
        if any(k in kwargs for k in ["bg_color", "fg_color", "value", "max_value"]):
            self._draw_progress()
        
        super().configure(**{k: v for k, v in kwargs.items() if k not in [
            "bg_color", "fg_color", "value", "max_value"
        ]})
    
    def update_theme(self):
        """更新主题"""
        # 更新画布背景色
        self.canvas.configure(bg=self.get_color("bg_color", "#f0f0f0"))
        # 重绘进度条
        self._draw_progress()


# 消息框函数已移至utils/ui_components.py中，避免重复定义


# 兼容性函数
def showerror(title, message):
    """显示错误消息（已禁用）"""
    # 弹窗已移除，不再显示
    return None


def highlight_text(text_widget, pattern, tag_name, foreground=None, background=None, font=None):
    """在文本控件中高亮显示匹配的文本
    
    Args:
        text_widget: 文本控件
        pattern: 要匹配的正则表达式模式
        tag_name: 标签名称
        foreground: 前景色
        background: 背景色
        font: 字体
    """
    # 获取文本内容
    content = text_widget.get("1.0", tk.END)
    
    # 清除之前的标签
    text_widget.tag_delete(tag_name)
    
    # 查找匹配项
    for match in re.finditer(pattern, content):
        start_line = content[:match.start()].count('\n') + 1
        start_col = match.start() - content.rfind('\n', 0, match.start()) - 1
        end_line = content[:match.end()].count('\n') + 1
        end_col = match.end() - content.rfind('\n', 0, match.end()) - 1
        
        start_index = f"{start_line}.{start_col}"
        end_index = f"{end_line}.{end_col}"
        
        # 添加标签
        text_widget.tag_add(tag_name, start_index, end_index)
    
    # 配置标签样式
    tag_config = {}
    if foreground:
        tag_config['foreground'] = foreground
    if background:
        tag_config['background'] = background
    if font:
        tag_config['font'] = font
    
    if tag_config:
        text_widget.tag_config(tag_name, **tag_config)


def create_tooltip(widget, text, delay=500, **kwargs):
    """为控件创建工具提示
    
    Args:
        widget: 要添加工具提示的控件
        text: 工具提示文本
        delay: 显示延迟（毫秒）
        **kwargs: 其他样式参数
    """
    tooltip = None
    timer_id = None
    
    def show_tooltip(event=None):
        nonlocal tooltip
        
        # 创建工具提示窗口
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_attributes("-topmost", True)
        
        # 创建标签
        from config.ui_config import get_ui_settings
        ui_settings = get_ui_settings()
        tooltip_bg = ui_settings["colors"].get("card_bg", "#ffffe0")
        label = tk.Label(
            tooltip,
            text=text,
            justify="left",
            background=kwargs.get("background", tooltip_bg),
            foreground=kwargs.get("foreground", "#000000"),
            relief="solid",
            borderwidth=1,
            font=kwargs.get("font", ("SF Pro Display", 10))
        )
        label.pack()
        
        # 计算位置
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        tooltip.wm_geometry(f"+{x}+{y}")
        
        # 添加淡入动画
        if hasattr(fade_in, '__call__'):
            fade_in(tooltip)
    
    def schedule_tooltip(event=None):
        nonlocal timer_id
        
        # 取消之前的定时器
        if timer_id:
            widget.after_cancel(timer_id)
        
        # 设置新的定时器
        timer_id = widget.after(delay, show_tooltip)
    
    def hide_tooltip(event=None):
        nonlocal tooltip, timer_id
        
        # 取消定时器
        if timer_id:
            widget.after_cancel(timer_id)
            timer_id = None
        
        # 关闭工具提示
        if tooltip:
            if hasattr(fade_out, '__call__'):
                fade_out(tooltip, callback=tooltip.destroy)
            else:
                tooltip.destroy()
            tooltip = None
    
    # 绑定事件
    widget.bind("<Enter>", schedule_tooltip)
    widget.bind("<Leave>", hide_tooltip)
    widget.bind("<ButtonPress>", hide_tooltip)