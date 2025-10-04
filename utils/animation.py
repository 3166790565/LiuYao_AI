# utils/animation.py
# UI动画效果工具函数

import tkinter as tk
from typing import Callable, Any, Optional

# 导入配置
from config.settings import ANIMATION_DURATION, ANIMATION_STEPS
from utils.logger import setup_logger

# 设置日志记录器
logger = setup_logger(__name__)


def animate_widget_property(
    widget: tk.Widget,
    property_name: str,
    start_value: Any,
    end_value: Any,
    duration: int = 100,  # 默认使用更短的动画时间
    steps: int = 5,  # 大幅减少步数提高性能
    easing: str = 'linear',  # 默认使用线性缓动
    callback: Optional[Callable] = None
) -> None:
    """动画改变控件属性值 - 高性能版本
    
    Args:
        widget: 要动画的控件
        property_name: 属性名称
        start_value: 起始值
        end_value: 结束值
        duration: 动画持续时间(毫秒)
        steps: 动画步数
        easing: 缓动函数名称
        callback: 动画完成后的回调函数
    """
    # 从UI配置中读取性能模式设置
    try:
        from config.ui_config import UI_SETTINGS
        performance_mode = UI_SETTINGS.get("animation", {}).get("performance_mode", False)
        if performance_mode:
            # 在性能模式下，直接设置最终值，不执行动画
            try:
                if property_name in ['x', 'y']:
                    if property_name == 'x':
                        widget.place(x=end_value)
                    else:
                        widget.place(y=end_value)
                else:
                    widget.configure(**{property_name: end_value})
                
                if callback:
                    callback()
            except Exception:
                pass
            return
    except ImportError:
        pass  # 如果无法导入配置，继续使用默认行为
    
    # 如果动画持续时间太短，直接设置最终值
    if duration < 30:  # 进一步降低阈值
        try:
            if property_name in ['x', 'y']:
                if property_name == 'x':
                    widget.place(x=end_value)
                else:
                    widget.place(y=end_value)
            else:
                widget.configure(**{property_name: end_value})
            
            if callback:
                callback()
        except Exception:
            pass
        return
    
    # 极简缓动函数
    easing_func = lambda t: t  # 默认使用线性缓动，性能最好
    
    # 极简值计算函数
    def calculate_step_value(start, end, progress):
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            return start + (end - start) * progress
        elif isinstance(start, str) and start.startswith('#') and isinstance(end, str) and end.startswith('#'):
            # 极简颜色处理 - 只处理标准6位十六进制颜色
            try:
                # 直接返回结束颜色，避免复杂计算
                if progress > 0.5:
                    return end
                return start
            except:
                return end
        else:
            # 对于不支持的类型，直接返回结束值
            return end_value
    
    # 执行动画 - 使用after方法避免线程开销
    step_time = max(int(duration / steps), 10)  # 确保每步至少10毫秒
    current_step = [0]  # 使用列表以便在闭包中修改
    
    def animate_step():
        if current_step[0] >= steps:
            # 动画完成，设置最终值
            try:
                if property_name in ['x', 'y']:
                    if property_name == 'x':
                        widget.place(x=end_value)
                    else:
                        widget.place(y=end_value)
                else:
                    widget.configure(**{property_name: end_value})
                
                # 执行回调
                if callback:
                    callback()
            except Exception:
                pass
            return
        
        # 计算当前步骤值
        progress = current_step[0] / steps
        step_value = calculate_step_value(start_value, end_value, progress)
        
        # 更新UI
        try:
            if property_name in ['x', 'y']:
                if property_name == 'x':
                    widget.place(x=step_value)
                else:  # property_name == 'y'
                    widget.place(y=step_value)
            else:
                widget.configure(**{property_name: step_value})
        except Exception:
            # 如果控件已被销毁，停止动画
            return
        
        current_step[0] += 1
        widget.after(step_time, animate_step)
    
    # 开始动画
    animate_step()


def fade_in(
    widget: tk.Widget,
    duration: int = 100,  # 减少默认动画时间
    callback: Optional[Callable] = None,
    delay: int = 0
) -> None:
    """淡入动画 - 高性能版本
    
    Args:
        widget: 要动画的控件
        duration: 动画持续时间(毫秒)
        callback: 动画完成后的回调函数
        delay: 动画开始前的延迟时间(毫秒)
    """
    # 如果动画被禁用，直接显示控件
    if duration <= 0:
        if callback:
            callback()
        return
    
    def start_fade_in():
        # 直接显示控件，不使用alpha渐变
        widget.update_idletasks()
        if callback:
            callback()
    
    # 延迟开始动画
    if delay > 0:
        widget.after(delay, start_fade_in)
    else:
        start_fade_in()


def fade_out(
    widget: tk.Widget,
    duration: int = 100,  # 减少默认动画时间
    callback: Optional[Callable] = None,
    delay: int = 0
) -> None:
    """淡出动画 - 高性能版本
    
    Args:
        widget: 要动画的控件
        duration: 动画持续时间(毫秒)
        callback: 动画完成后的回调函数
        delay: 动画开始前的延迟时间(毫秒)
    """
    # 如果动画被禁用，直接隐藏控件
    if duration <= 0:
        if callback:
            callback()
        return
    
    def start_fade_out():
        # 直接隐藏控件，不使用alpha渐变
        if callback:
            callback()
    
    # 延迟开始动画
    if delay > 0:
        widget.after(delay, start_fade_out)
    else:
        start_fade_out()


def slide_in(
    widget: tk.Widget,
    direction: str = 'right',
    duration: int = ANIMATION_DURATION,
    callback: Optional[Callable] = None,
    delay: int = 0
) -> None:
    """滑入动画 - 基于grid布局
    
    Args:
        widget: 要动画的控件
        direction: 滑入方向 ('left', 'right', 'top', 'bottom')
        duration: 动画持续时间(毫秒)
        callback: 动画完成后的回调函数
        delay: 动画开始前的延迟时间(毫秒)
    """
    # 保存控件的grid信息
    grid_info = widget.grid_info()
    if not grid_info:
        # 如果控件没有使用grid布局，则无法执行基于grid的动画
        widget.update()
        if callback:
            callback()
        return
    
    # 临时移除控件
    widget.grid_remove()
    
    # 创建动画效果
    steps = ANIMATION_STEPS
    step_time = duration / steps
    
    # 设置初始透明度
    if hasattr(widget, 'attributes'):
        widget.attributes('-alpha', 0.0)
    
    # 根据方向设置初始padding（确保为正数）
    padx = (0, 0)
    pady = (0, 0)
    widget_width = max(widget.winfo_reqwidth(), 1)
    widget_height = max(widget.winfo_reqheight(), 1)
    
    if direction == 'left':
        padx = (widget_width, 0)
    elif direction == 'right':
        padx = (0, widget_width)
    elif direction == 'top':
        pady = (widget_height, 0)
    elif direction == 'bottom':
        pady = (0, widget_height)
    
    # 保存原始grid配置
    original_padx = grid_info.get('padx', 0)
    original_pady = grid_info.get('pady', 0)
    if not isinstance(original_padx, tuple):
        original_padx = (original_padx, original_padx)
    if not isinstance(original_pady, tuple):
        original_pady = (original_pady, original_pady)
    
    def start_animation():
        # 显示控件，但使用初始padding
        widget.grid(row=grid_info['row'], column=grid_info['column'], 
                    sticky=grid_info.get('sticky', ''), 
                    padx=padx, pady=pady)
        
        def animate_step(step):
            progress = step / steps
            
            # 计算当前步骤的padding（确保为正数）
            step_padx = (
                max(0, int(padx[0] + (original_padx[0] - padx[0]) * progress)),
                max(0, int(padx[1] + (original_padx[1] - padx[1]) * progress))
            )
            step_pady = (
                max(0, int(pady[0] + (original_pady[0] - pady[0]) * progress)),
                max(0, int(pady[1] + (original_pady[1] - pady[1]) * progress))
            )
            
            # 更新透明度
            if hasattr(widget, 'attributes'):
                widget.attributes('-alpha', progress)
            
            # 更新padding
            widget.grid(row=grid_info['row'], column=grid_info['column'], 
                        sticky=grid_info.get('sticky', ''), 
                        padx=step_padx, pady=step_pady)
            
            if step < steps:
                widget.after(int(step_time), lambda: animate_step(step + 1))
            else:
                # 动画完成，恢复原始grid配置
                widget.grid(row=grid_info['row'], column=grid_info['column'], 
                            sticky=grid_info.get('sticky', ''), 
                            padx=original_padx, pady=original_pady)
                if callback:
                    callback()
        
        # 开始动画
        animate_step(0)
    
    # 延迟开始动画
    if delay > 0:
        widget.after(int(delay), start_animation)
    else:
        start_animation()


def slide_out(
    widget: tk.Widget,
    direction: str = 'right',
    duration: int = ANIMATION_DURATION,
    callback: Optional[Callable] = None,
    delay: int = 0
) -> None:
    """滑出动画 - 基于grid布局
    
    Args:
        widget: 要动画的控件
        direction: 滑出方向 ('left', 'right', 'top', 'bottom')
        duration: 动画持续时间(毫秒)
        callback: 动画完成后的回调函数
        delay: 动画开始前的延迟时间(毫秒)
    """
    # 保存控件的grid信息
    grid_info = widget.grid_info()
    if not grid_info:
        # 如果控件没有使用grid布局，则无法执行基于grid的动画
        if callback:
            callback()
        return
    
    # 创建动画效果
    steps = ANIMATION_STEPS
    step_time = duration / steps
    
    # 计算目标padding
    target_padx = (0, 0)
    target_pady = (0, 0)
    if direction == 'left':
        target_padx = (-widget.winfo_width(), 0)
    elif direction == 'right':
        target_padx = (widget.winfo_width(), 0)
    elif direction == 'top':
        target_pady = (-widget.winfo_height(), 0)
    elif direction == 'bottom':
        target_pady = (widget.winfo_height(), 0)
    
    # 获取当前padding
    current_padx = grid_info.get('padx', 0)
    current_pady = grid_info.get('pady', 0)
    if not isinstance(current_padx, tuple):
        current_padx = (current_padx, current_padx)
    if not isinstance(current_pady, tuple):
        current_pady = (current_pady, current_pady)
    
    def start_animation():
        def animate_step(step):
            progress = step / steps
            
            # 计算当前步骤的padding
            step_padx = current_padx
            step_pady = current_pady
            
            if direction == 'left' or direction == 'right':
                step_padx = (
                    int(current_padx[0] + (target_padx[0] - current_padx[0]) * progress),
                    int(current_padx[1] + (target_padx[1] - current_padx[1]) * progress)
                )
            elif direction == 'top' or direction == 'bottom':
                step_pady = (
                    int(current_pady[0] + (target_pady[0] - current_pady[0]) * progress),
                    int(current_pady[1] + (target_pady[1] - current_pady[1]) * progress)
                )
            
            # 更新透明度
            if hasattr(widget, 'attributes'):
                widget.attributes('-alpha', 1.0 - progress)
            
            # 更新padding
            widget.grid(row=grid_info['row'], column=grid_info['column'], 
                        sticky=grid_info.get('sticky', ''), 
                        padx=step_padx, pady=step_pady)
            
            if step < steps:
                widget.after(int(step_time), lambda: animate_step(step + 1))
            else:
                # 动画完成，移除控件
                widget.grid_remove()
                if callback:
                    callback()
        
        # 开始动画
        animate_step(0)
    
    # 延迟开始动画
    if delay > 0:
        widget.after(int(delay), start_animation)
    else:
        start_animation()


def pulse_animation(
    widget: tk.Widget,
    property_name: str = 'fg_color',
    start_color: str = '#ffffff',
    end_color: str = '#e5e5ea',
    duration: int = 500,
    repeat: int = 3,
    callback: Optional[Callable] = None,
    scale_factor: float = 1.0
) -> None:
    """脉冲动画效果
    
    Args:
        widget: 要动画的控件
        property_name: 属性名称
        start_color: 起始颜色
        end_color: 结束颜色
        duration: 单次动画持续时间(毫秒)
        repeat: 重复次数
        callback: 动画完成后的回调函数
        scale_factor: 缩放因子，控制脉冲效果的大小变化
    """
    current_repeat = [0]  # 使用列表存储当前重复次数，以便在闭包中修改
    
    def single_pulse():
        # 从起始颜色到结束颜色
        animate_widget_property(
            widget, 
            property_name, 
            start_color, 
            end_color, 
            duration // 2,
            callback=lambda: pulse_back()
        )
    
    def pulse_back():
        # 从结束颜色回到起始颜色
        animate_widget_property(
            widget, 
            property_name, 
            end_color, 
            start_color, 
            duration // 2,
            callback=lambda: check_repeat()
        )
    
    def check_repeat():
        current_repeat[0] += 1
        if current_repeat[0] < repeat:
            widget.after(100, single_pulse)
        elif callback:
            callback()
    
    single_pulse()


def typing_animation(
    widget: tk.Label,
    text: str,
    delay: int = 20,  # 默认延迟减少到20毫秒，加快打字速度
    callback: Optional[Callable] = None,
    cursor: str = "|",  # 光标字符
    cursor_blink: bool = True,  # 是否闪烁光标
    auto_scroll: bool = True  # 是否自动滚动以保持最后一行可见
) -> None:
    """打字机效果动画
    
    Args:
        widget: 标签控件
        text: 要显示的文本
        delay: 每个字符的延迟时间(毫秒)
        callback: 动画完成后的回调函数
        cursor: 光标字符
        cursor_blink: 是否闪烁光标
        auto_scroll: 是否自动滚动以保持最后一行可见
    """
    cursor_visible = [True]  # 使用列表以便在闭包中修改
    
    def scroll_to_bottom():
        """滚动到底部，确保最后一行可见"""
        if not auto_scroll:
            return
            
        # 尝试获取父级滚动区域
        try:
            # 查找父级滚动画布
            parent = widget.winfo_parent()
            parent_widget = widget._nametowidget(parent)
            
            # 向上查找父级，直到找到带有_parent_canvas属性的组件或CTkScrollableFrame
            while parent_widget and not hasattr(parent_widget, '_parent_canvas'):
                if not hasattr(parent_widget, 'winfo_parent') or not parent_widget.winfo_parent():
                    break
                parent = parent_widget.winfo_parent()
                parent_widget = widget._nametowidget(parent)
            
            # 如果找到了滚动画布，滚动到底部
            if hasattr(parent_widget, '_parent_canvas'):
                parent_widget._parent_canvas.update_idletasks()
                parent_widget._parent_canvas.yview_moveto(1.0)
            
            # 尝试其他常见的滚动容器类型
            elif hasattr(parent_widget, 'yview_moveto'):
                parent_widget.yview_moveto(1.0)
                
        except Exception:
            # 如果出现任何错误，忽略并继续
            pass
    
    def blink_cursor():
        if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
            return
            
        if cursor_blink and hasattr(widget, '_typing_active') and widget._typing_active:
            cursor_visible[0] = not cursor_visible[0]
            current_text = text[:getattr(widget, '_current_index', 0)]
            cursor_text = cursor if cursor_visible[0] else " "
            
            try:
                widget.configure(text=current_text + cursor_text)
            except AttributeError:
                widget.config(text=current_text + cursor_text)
            
            # 确保光标可见
            scroll_to_bottom()
                
            widget.after(500, blink_cursor)  # 光标每500毫秒闪烁一次
    
    def type_text(index=0):
        if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
            return
            
        widget._typing_active = True  # 标记打字动画正在进行
        widget._current_index = index  # 保存当前索引
        
        if index <= len(text):
            # 使用configure而不是config，以兼容customtkinter控件
            try:
                widget.configure(text=text[:index] + (cursor if cursor_visible[0] else ""))
            except AttributeError:
                # 兼容标准tkinter控件
                widget.config(text=text[:index] + (cursor if cursor_visible[0] else ""))
            
            # 每次更新文本后滚动到底部
            scroll_to_bottom()
                
            widget.after(delay, lambda: type_text(index + 1))
        else:
            # 打字完成后，移除光标
            try:
                widget.configure(text=text)
            except AttributeError:
                widget.config(text=text)
            
            # 最后一次滚动到底部
            scroll_to_bottom()
                
            widget._typing_active = False  # 标记打字动画已完成
            if callback:
                callback()
    
    # 开始打字动画
    type_text()
    
    # 如果启用光标闪烁，开始闪烁
    if cursor_blink:
        blink_cursor()


def progress_animation(
    progressbar: tk.Widget,
    start_value: float,
    end_value: float,
    duration: int = ANIMATION_DURATION,
    callback: Optional[Callable] = None
) -> None:
    """进度条动画
    
    Args:
        progressbar: 进度条控件
        start_value: 起始值
        end_value: 结束值
        duration: 动画持续时间(毫秒)
        callback: 动画完成后的回调函数
    """
    steps = ANIMATION_STEPS
    step_time = duration / steps
    value_increment = (end_value - start_value) / steps
    
    def update_progress(step=0, current_value=start_value):
        if step <= steps:
            progressbar['value'] = current_value
            next_value = current_value + value_increment
            progressbar.after(int(step_time), lambda: update_progress(step + 1, next_value))
        else:
            # 确保最终值正确设置
            progressbar['value'] = end_value
            if callback:
                callback()
    
    update_progress()