# config/settings.py
# 应用程序设置

# 日志设置
LOG_FILE = "app.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# UI设置
DEFAULT_WINDOW_SIZE = "900x1000"
DEFAULT_FONT = "Microsoft YaHei UI"

# 主题颜色 - iOS风格配色
COLORS = {
    "bg_color": "#f8f9fa",  # 背景色
    "text_color": "#212529",  # 文本色
    "primary_color": "#007aff",  # iOS蓝色
    "secondary_color": "#5856d6",  # 紫色
    "accent_color": "#ff2d55",  # 粉色
    "success_color": "#34c759",  # 绿色
    "warning_color": "#ff9500",  # 橙色
    "danger_color": "#ff3b30",  # 红色
    "light_gray": "#e5e5ea",  # 浅灰色
    "mid_gray": "#c7c7cc",  # 中灰色
    "dark_gray": "#8e8e93",  # 深灰色
}

# 动画设置
ANIMATION_DURATION = 150  # 毫秒 - 减少动画时长提升流畅度
ANIMATION_STEPS = 10  # 减少动画步数提升性能

# API设置
API_TIMEOUT = 60  # 秒
API_RETRY_COUNT = 3
API_RETRY_DELAY = 2  # 秒

# 缓存设置
CACHE_ENABLED = True
CACHE_EXPIRY = 3600  # 秒

# 默认模型
DEFAULT_MODEL = "gpt-4.1"

# 支持的模型列表
SUPPORTED_MODELS = [
    "mita",
    "gpt-4.1",
    "gpt-4",
    "gpt-4o",
    "gpt-4o-mini"
]

# 支持的易学体系
DIVINATION_METHODS = [
    "六爻",
    "奇门遁甲",
]

# 默认易学体系
DEFAULT_DIVINATION_METHOD = DIVINATION_METHODS[0]