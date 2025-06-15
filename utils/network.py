# utils/network.py
# 网络请求工具函数

import requests
import json
import time
import logging
import random
import datetime
from typing import Dict, Any, Optional, Tuple, Generator, List
from requests.exceptions import RequestException, Timeout
from urllib.parse import urljoin
from utils.logger import setup_logger

# 设置日志记录器
logger = setup_logger(__name__)

# 尝试导入requests_cache用于缓存请求
try:
    import requests_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# 导入配置
from config.settings import API_TIMEOUT, API_RETRY_COUNT, API_RETRY_DELAY, CACHE_ENABLED, CACHE_EXPIRY
from config.constants import API_ENDPOINTS, HEADERS, USER_AGENTS, MODEL_TYPES

# 初始化缓存
if CACHE_AVAILABLE and CACHE_ENABLED:
    requests_cache.install_cache(
        'api_cache',
        backend='sqlite',
        expire_after=CACHE_EXPIRY
    )


def generate_timestamp() -> str:
    """生成当前时间戳"""
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_request_headers(model_type: str) -> Dict[str, str]:
    """根据模型类型生成请求头
    
    Args:
        model_type: 模型类型 ("OPENAI")
        
    Returns:
        Dict[str, str]: 请求头字典
    """
    headers = HEADERS.get(model_type, {}).copy()
    
    # 添加时间戳和随机数
    timestamp = generate_timestamp()
    headers["X-Timestamp"] = timestamp
    
    # 添加User-Agent
    headers["User-Agent"] = USER_AGENTS.get(model_type, "")
    
    return headers


def get_model_type(model_name: str) -> str:
    """根据模型名称获取模型类型
    
    Args:
        model_name: 模型名称
        
    Returns:
        str: 模型类型 ("OPENAI")
    """
    for model_type, models in MODEL_TYPES.items():
        if model_name in models:
            return model_type
    return "OPENAI"  # 默认返回OPENAI


def get_api_endpoint(model_type: str) -> str:
    """根据模型类型获取API端点
    
    Args:
        model_type: 模型类型
        
    Returns:
        str: API端点URL
    """
    return API_ENDPOINTS.get(model_type, "")


def make_request(
    url: str,
    data: Dict[str, Any],
    headers: Dict[str, str],
    stream: bool = False
) -> Tuple[bool, Any]:
    """发送POST请求并处理响应
    
    Args:
        url: 请求URL
        data: 请求数据
        headers: 请求头
        stream: 是否使用流式响应
        
    Returns:
        Tuple[bool, Any]: (成功标志, 响应数据/错误信息)
    """
    for attempt in range(API_RETRY_COUNT):
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=API_TIMEOUT,
                stream=stream
            )
            
            # 检查响应状态码
            if response.status_code != 200:
                error_msg = f"API请求失败: HTTP {response.status_code}, {response.text}"
                logger.error(error_msg)
                
                # 如果不是最后一次尝试，则等待后重试
                if attempt < API_RETRY_COUNT - 1:
                    time.sleep(API_RETRY_DELAY)
                    continue
                    
                return False, error_msg
            
            return True, response
            
        except (RequestException, Timeout) as e:
            error_msg = f"网络请求异常: {str(e)}"
            logger.error(error_msg)
            
            # 如果不是最后一次尝试，则等待后重试
            if attempt < API_RETRY_COUNT - 1:
                time.sleep(API_RETRY_DELAY)
                continue
                
            return False, error_msg
    
    # 不应该到达这里，但为了安全起见
    return False, "所有重试尝试均失败"


def process_stream_response(response) -> Generator[Dict[str, Any], None, None]:
    """处理流式响应
    
    Args:
        response: 请求响应对象
        
    Yields:
        Dict[str, Any]: 解析后的响应数据
    """
    for line in response.iter_lines():
        if line:
            # 移除 "data: " 前缀
            if line.startswith(b'data: '):
                line = line[6:]
                
            # 跳过心跳消息
            if line.strip() == b'[DONE]':
                break
                
            try:
                data = json.loads(line)
                yield data
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}, 原始数据: {line}")


def parse_ai_response(response_text: str) -> List[Dict[str, Any]]:
    """解析AI响应文本为JSON数组
    
    Args:
        response_text: AI响应文本
        
    Returns:
        List[Dict[str, Any]]: 解析后的JSON数组
    """
    # 尝试直接解析JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # 尝试查找JSON数组
    import re
    json_array_pattern = r'\[\s*{.*}\s*\]'
    match = re.search(json_array_pattern, response_text, re.DOTALL)
    
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    # 尝试查找方括号内的内容
    bracket_pattern = r'\[(.*?)\]'
    match = re.search(bracket_pattern, response_text, re.DOTALL)
    
    if match:
        try:
            # 尝试将方括号内的内容解析为JSON数组
            content = f"[{match.group(1)}]"
            return json.loads(content)
        except json.JSONDecodeError:
            pass
    
    # 如果所有尝试都失败，返回空数组
    logger.error(f"无法解析响应为JSON数组: {response_text}")
    return []