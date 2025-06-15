# utils/resources.py
# 资源管理工具函数

import os
import json
import base64
import tempfile
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import threading
import time

# 尝试导入PIL用于图像处理
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 尝试导入requests用于网络请求
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 导入配置
from utils.logger import setup_logger

# 设置日志记录器
logger = setup_logger(__name__)

# 资源缓存
RESOURCE_CACHE = {}

# 资源目录
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")

# 确保资源目录存在
if not os.path.exists(RESOURCE_DIR):
    try:
        os.makedirs(RESOURCE_DIR)
    except Exception as e:
        logger.error(f"无法创建资源目录: {str(e)}")
        # 使用临时目录作为备用
        RESOURCE_DIR = os.path.join(tempfile.gettempdir(), "ai_yixue_resources")
        if not os.path.exists(RESOURCE_DIR):
            os.makedirs(RESOURCE_DIR)


def get_resource_path(resource_name: str) -> str:
    """获取资源文件路径
    
    Args:
        resource_name: 资源名称
        
    Returns:
        str: 资源文件路径
    """
    return os.path.join(RESOURCE_DIR, resource_name)


def download_resource(url: str, save_path: str) -> bool:
    """下载资源文件
    
    Args:
        url: 资源URL
        save_path: 保存路径
        
    Returns:
        bool: 下载是否成功
    """
    if not REQUESTS_AVAILABLE:
        logger.error("缺少requests库，无法下载资源")
        return False
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        logger.error(f"下载资源失败: {url}, 错误: {str(e)}")
        return False


def load_image(image_name: str, size: Optional[Tuple[int, int]] = None) -> Optional[Any]:
    """加载图像资源
    
    Args:
        image_name: 图像名称
        size: 图像大小 (width, height)
        
    Returns:
        Optional[Any]: 加载的图像对象，如果加载失败则返回None
    """
    if not PIL_AVAILABLE:
        logger.error("缺少PIL库，无法加载图像")
        return None
    
    # 检查缓存
    cache_key = f"{image_name}_{size[0]}x{size[1]}" if size else image_name
    if cache_key in RESOURCE_CACHE:
        return RESOURCE_CACHE[cache_key]
    
    # 构建图像路径
    image_path = get_resource_path(image_name)
    
    # 如果本地文件不存在，尝试下载
    if not os.path.exists(image_path):
        # 获取图像URL
        image_url = None
        if image_name in IMAGE_URLS:
            image_url = IMAGE_URLS[image_name]
        elif '.' in image_name:
            # 尝试从ICONS中查找
            icon_name = image_name.split('.')[0].upper()
            if 'ICONS' in IMAGE_URLS and icon_name in IMAGE_URLS['ICONS']:
                image_url = IMAGE_URLS['ICONS'][icon_name]
        
        if image_url:
            if not download_resource(image_url, image_path):
                return None
        else:
            logger.error(f"未找到图像资源: {image_name}")
            return None
    
    try:
        # 加载图像
        image = Image.open(image_path)
        
        # 调整大小
        if size:
            image = image.resize(size, Image.LANCZOS)
        
        # 转换为PhotoImage
        photo_image = ImageTk.PhotoImage(image)
        
        # 缓存图像
        RESOURCE_CACHE[cache_key] = photo_image
        
        return photo_image
    except Exception as e:
        logger.error(f"加载图像失败: {image_name}, 错误: {str(e)}")
        return None


def load_svg_icon(icon_name: str, size: Tuple[int, int] = (24, 24), color: str = "#000000") -> str:
    """加载SVG图标并返回其内容
    
    Args:
        icon_name: 图标名称
        size: 图标大小 (width, height)
        color: 图标颜色
        
    Returns:
        str: SVG图标内容
    """
    # 构建图标路径
    icon_path = get_resource_path(f"{icon_name}.svg")
    
    # 如果本地文件不存在，使用默认图标
    if not os.path.exists(icon_path):
        # 创建默认图标
        width, height = size
        return f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{width}" height="{height}" fill="none" stroke="{color}" stroke-width="2" />
            <text x="{width/2}" y="{height/2}" font-family="Arial" font-size="{min(width, height)/2}" 
                  fill="{color}" text-anchor="middle" dominant-baseline="middle">
                {icon_name[0].upper()}
            </text>
        </svg>
        '''
    
    try:
        # 读取SVG文件
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # 替换颜色和大小
        svg_content = svg_content.replace('width="24"', f'width="{size[0]}"')
        svg_content = svg_content.replace('height="24"', f'height="{size[1]}"')
        
        # 替换颜色（简单替换，可能不适用于所有SVG）
        svg_content = svg_content.replace('fill="#000"', f'fill="{color}"')
        svg_content = svg_content.replace('fill="black"', f'fill="{color}"')
        svg_content = svg_content.replace('stroke="#000"', f'stroke="{color}"')
        svg_content = svg_content.replace('stroke="black"', f'stroke="{color}"')
        
        return svg_content
    except Exception as e:
        logger.error(f"加载SVG图标失败: {icon_name}, 错误: {str(e)}")
        # 返回默认图标
        width, height = size
        return f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{width}" height="{height}" fill="none" stroke="{color}" stroke-width="2" />
            <text x="{width/2}" y="{height/2}" font-family="Arial" font-size="{min(width, height)/2}" 
                  fill="{color}" text-anchor="middle" dominant-baseline="middle">
                {icon_name[0].upper()}
            </text>
        </svg>
        '''


def create_svg_icons():
    """创建默认的SVG图标"""
    # 分析图标
    analysis_icon = '''
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 3v18h18" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M7 16l4-8 4 4 4-8" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    
    # 聊天图标
    chat_icon = '''
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M21 12c0 4.418-4.03 8-9 8-1.174 0-2.3-.19-3.36-.54L4 21l.54-4.64C3.19 14.3 3 13.174 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    
    # 导出图标
    export_icon = '''
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 3v12m0-12L8 7m4-4l4 4" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M8 15H4a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1h-4" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    
    # 清除图标
    clear_icon = '''
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    
    # 发送图标
    send_icon = '''
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    
    # 保存图标
    icons = {
        "analysis.svg": analysis_icon,
        "chat.svg": chat_icon,
        "export.svg": export_icon,
        "clear.svg": clear_icon,
        "send.svg": send_icon
    }
    
    # 保存图标
    for icon_name, icon_content in icons.items():
        icon_path = get_resource_path(icon_name)
        if not os.path.exists(icon_path):
            try:
                with open(icon_path, 'w', encoding='utf-8') as f:
                    f.write(icon_content)
            except Exception as e:
                logger.error(f"创建SVG图标失败: {icon_name}, 错误: {str(e)}")


def preload_resources():
    """预加载资源文件"""
    # 创建SVG图标
    create_svg_icons()
    
    # 预加载常用图标
    icons = ["analysis.svg", "chat.svg", "export.svg", "clear.svg", "send.svg"]
    for icon_name in icons:
        load_svg_icon(icon_name)


# 在模块导入时预加载资源
preload_resources()