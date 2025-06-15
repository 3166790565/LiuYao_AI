# config/themes.py
# UI主题配置

# iOS风格主题配色
IOS_LIGHT_THEME = {
    # 基础颜色
    "bg_color": "#f2f2f7",  # 背景色
    "card_bg": "#ffffff",  # 卡片背景色
    "text_color": "#000000",  # 主文本色
    "secondary_text": "#a1a1a6",  # 次要文本色
    "separator": "#c6c6c8",  # 分隔线颜色
    
    # 交互颜色
    "primary_color": "#007aff",  # iOS蓝色
    "secondary_color": "#5856d6",  # 紫色
    "accent_color": "#ff2d55",  # 粉色
    "success_color": "#34c759",  # 绿色
    "warning_color": "#ff9500",  # 橙色
    "danger_color": "#ff3b30",  # 红色
    
    # 灰度色阶
    "gray_1": "#f2f2f7",  # 最浅灰色
    "gray_2": "#e5e5ea",  # 浅灰色
    "gray_3": "#d1d1d6",  # 中浅灰色
    "gray_4": "#c7c7cc",  # 中灰色
    "gray_5": "#aeaeb2",  # 中深灰色
    "gray_6": "#8e8e93",  # 深灰色
    
    # 透明度变体 - 使用不带透明度的颜色
    "primary_alpha_10": "#cce4ff",  # 浅蓝色代替10%透明度
    "primary_alpha_20": "#99c9ff",  # 浅蓝色代替20%透明度
    "primary_alpha_40": "#66adff",  # 浅蓝色代替40%透明度
    "primary_alpha_50": "#66a3ff",  # 浅蓝色代替50%透明度
    
    # 次要颜色透明度变体
    "secondary_alpha_10": "#dedcfa",  # 浅紫色代替10%透明度
    "secondary_alpha_20": "#bdb9f5",  # 浅紫色代替20%透明度
    "secondary_alpha_40": "#9c97f0",  # 浅紫色代替40%透明度
    "secondary_alpha_50": "#7b75eb",  # 浅紫色代替50%透明度
    
    # 成功颜色透明度变体
    "success_alpha_10": "#d4f5df",  # 浅绿色代替10%透明度
    "success_alpha_20": "#a9ebbf",  # 浅绿色代替20%透明度
    "success_alpha_40": "#7de09f",  # 浅绿色代替40%透明度
    "success_alpha_50": "#67d98f",  # 浅绿色代替50%透明度
    
    # 渐变色
    "gradient_start": "#007aff",  # 渐变起始色
    "gradient_end": "#5ac8fa",  # 渐变结束色
}

# iOS深色主题配色
IOS_DARK_THEME = {
    # 基础颜色
    "bg_color": "#1c1c1e",  # 背景色
    "card_bg": "#2c2c2e",  # 卡片背景色
    "text_color": "#ffffff",  # 主文本色
    "secondary_text": "#a1a1a6",  # 次要文本色
    "separator": "#38383a",  # 分隔线颜色
    
    # 交互颜色
    "primary_color": "#0a84ff",  # iOS蓝色(深色模式)
    "secondary_color": "#5e5ce6",  # 紫色(深色模式)
    "accent_color": "#ff375f",  # 粉色(深色模式)
    "success_color": "#30d158",  # 绿色(深色模式)
    "warning_color": "#ff9f0a",  # 橙色(深色模式)
    "danger_color": "#ff453a",  # 红色(深色模式)
    
    # 灰度色阶
    "gray_1": "#2c2c2e",  # 最浅灰色(深色模式)
    "gray_2": "#38383a",  # 浅灰色(深色模式)
    "gray_3": "#48484a",  # 中浅灰色(深色模式)
    "gray_4": "#636366",  # 中灰色(深色模式)
    "gray_5": "#8e8e93",  # 中深灰色(深色模式)
    "gray_6": "#aeaeb2",  # 深灰色(深色模式)
    
    # 透明度变体 - 深色模式适配
    "primary_alpha_10": "#1a2d42",  # 深蓝色代替10%透明度
    "primary_alpha_20": "#2a3d52",  # 深蓝色代替20%透明度
    "primary_alpha_40": "#3a4d62",  # 深蓝色代替40%透明度
    "primary_alpha_50": "#4a5d72",  # 深蓝色代替50%透明度
    
    # 次要颜色透明度变体
    "secondary_alpha_10": "#2a2d42",  # 深紫色代替10%透明度
    "secondary_alpha_20": "#3a3d52",  # 深紫色代替20%透明度
    "secondary_alpha_40": "#4a4d62",  # 深紫色代替40%透明度
    "secondary_alpha_50": "#5a5d72",  # 深紫色代替50%透明度
    
    # 成功颜色透明度变体
    "success_alpha_10": "#1a3d2a",  # 深绿色代替10%透明度
    "success_alpha_20": "#2a4d3a",  # 深绿色代替20%透明度
    "success_alpha_40": "#3a5d4a",  # 深绿色代替40%透明度
    "success_alpha_50": "#4a6d5a",  # 深绿色代替50%透明度
    
    # 渐变色
    "gradient_start": "#0a84ff",  # 渐变起始色
    "gradient_end": "#64d2ff",  # 渐变结束色
}

# 获取主题配置
def get_theme(mode="light"):
    """获取指定模式的主题配置
    
    Args:
        mode (str): 主题模式，可选值为"light"或"dark"
        
    Returns:
        dict: 主题配置字典
    """
    if mode.lower() == "dark":
        return IOS_DARK_THEME
    return IOS_LIGHT_THEME