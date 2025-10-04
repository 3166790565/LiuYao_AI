# config/ui_config.py
# UI配置文件

from config.settings import DEFAULT_WINDOW_SIZE, DEFAULT_FONT
from config.themes import get_theme
from utils.config_manager import config_manager

# UI设置
UI_SETTINGS = {
    # 外观设置
    "appearance_mode": config_manager.get_theme_mode(),  # 外观模式：light或dark
    "color_theme": "blue",  # 颜色主题：blue (customtkinter内置主题)
    
    # 窗口设置
    "window_width": int(DEFAULT_WINDOW_SIZE.split('x')[0]),  # 窗口宽度
    "window_height": int(DEFAULT_WINDOW_SIZE.split('x')[1]),  # 窗口高度
    "window_resizable": True,  # 窗口是否可调整大小
    "window_centered": True,  # 窗口是否居中显示
    
    # 字体设置
    "font_family": DEFAULT_FONT,  # 字体名称
    "font_size": 12,  # 字体大小
    "font_weight": "normal",  # 字体粗细
    
    # 颜色设置（根据主题自动设置）
    "colors": get_theme(config_manager.get_theme_mode()),  # 颜色配置
    
    # 组件设置
    "component": {
        "button_height": 36,  # 按钮高度
        "button_corner_radius": 8,  # 按钮圆角半径
        "entry_height": 36,  # 输入框高度
        "entry_corner_radius": 8,  # 输入框圆角半径
        "progressbar_height": 6,  # 进度条高度
        "progressbar_corner_radius": 3,  # 进度条圆角半径
        "card_corner_radius": 12,  # 卡片圆角半径
        "card_padding": 16,  # 卡片内边距
    },
    
    # 动画设置 - 优化性能
    "animation": {
        "enabled": True,  # 是否启用动画
        "duration": 100,  # 动画持续时间（毫秒）- 减少为原来的1/3
        "easing": "linear",  # 动画缓动函数 - 使用更简单的线性函数
        "performance_mode": True,  # 性能模式 - 启用时会简化动画效果
        "steps": 5,  # 动画步数 - 减少步数提高性能
    },
}

# 更新UI设置
def update_ui_settings(settings):
    """更新UI设置
    
    Args:
        settings (dict): 新的UI设置
        
    Returns:
        dict: 更新后的UI设置
    """
    global UI_SETTINGS
    UI_SETTINGS.update(settings)
    
    # 更新颜色设置
    if "appearance_mode" in settings:
        UI_SETTINGS["colors"] = get_theme(settings["appearance_mode"])
        
    return UI_SETTINGS

# 获取UI设置
def get_ui_settings():
    """获取UI设置
    
    Returns:
        dict: UI设置
    """
    return UI_SETTINGS

# 切换主题模式
def toggle_theme_mode():
    """切换主题模式（明亮/暗黑）
    
    Returns:
        dict: 更新后的UI设置
    """
    current_mode = UI_SETTINGS["appearance_mode"]
    new_mode = "dark" if current_mode == "light" else "light"
    
    # 保存新的主题模式到配置文件
    config_manager.set_theme_mode(new_mode)
    config_manager.save_config()
    
    return update_ui_settings({"appearance_mode": new_mode})

# 易学体系设置
DEFAULT_DIVINATION_METHOD = "六爻"  # 默认易学体系
SUPPORTED_DIVINATION_METHODS = ["六爻", "梅花易数", "奇门遁甲"]  # 支持的易学体系