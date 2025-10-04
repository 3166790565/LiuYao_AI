# utils/logger.py
# 日志工具函数

import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Optional

# 导入配置
from config.settings import LOG_FILE, LOG_LEVEL, LOG_FORMAT


class DeduplicatingHandler(logging.Handler):
    """去重日志处理器，防止相同消息在短时间内重复输出"""
    
    def __init__(self, target_handler, dedup_window=1.0):
        super().__init__()
        self.target_handler = target_handler
        self.dedup_window = dedup_window  # 去重时间窗口（秒）
        self.recent_messages = {}  # 存储最近的消息和时间戳
    
    def emit(self, record):
        # 生成消息的唯一标识
        message_key = f"{record.levelname}:{record.getMessage()}"
        current_time = time.time()
        
        # 检查是否是重复消息
        if message_key in self.recent_messages:
            last_time = self.recent_messages[message_key]
            if current_time - last_time < self.dedup_window:
                return  # 跳过重复消息
        
        # 记录消息时间戳
        self.recent_messages[message_key] = current_time
        
        # 清理过期的消息记录
        expired_keys = [k for k, t in self.recent_messages.items() 
                       if current_time - t > self.dedup_window * 2]
        for key in expired_keys:
            del self.recent_messages[key]
        
        # 转发到目标处理器
        self.target_handler.emit(record)
    
    def setFormatter(self, formatter):
        self.target_handler.setFormatter(formatter)
    
    def setLevel(self, level):
        super().setLevel(level)
        self.target_handler.setLevel(level)


# 全局处理器实例，确保只创建一次
_console_handler = None
_file_handler = None
_logging_configured = False

def setup_logger(name: str = None) -> logging.Logger:
    """设置并返回日志记录器
    
    Args:
        name: 日志记录器名称，默认为根记录器
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    global _console_handler, _file_handler, _logging_configured
    
    # 获取日志级别
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    
    # 只在第一次调用时创建处理器
    if not _logging_configured:
        _logging_configured = True
        
        # 创建格式化器
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 创建原始控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 创建去重控制台处理器
        _console_handler = DeduplicatingHandler(console_handler, dedup_window=0.5)
        
        # 创建原始文件处理器
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            # 创建去重文件处理器
            _file_handler = DeduplicatingHandler(file_handler, dedup_window=0.5)
        except (IOError, PermissionError) as e:
            # 如果无法创建日志文件，使用控制台输出
            sys.stderr.write(f"无法创建日志文件: {str(e)}\n")
            _file_handler = None
        
        # 配置根logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(log_level)
        root_logger.addHandler(_console_handler)
        if _file_handler:
            root_logger.addHandler(_file_handler)
    
    # 返回指定名称的logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 确保命名logger不重复添加处理器
    if name and not logger.handlers:
        # 命名logger使用传播机制，不需要自己的处理器
        logger.propagate = True
    
    return logger


def log_exception(e: Exception, logger: Optional[logging.Logger] = None) -> None:
    """记录异常信息
    
    Args:
        e: 异常对象
        logger: 日志记录器，如果为None则使用根记录器
    """
    if logger is None:
        logger = logging.getLogger()
    
    import traceback
    error_msg = f"异常: {type(e).__name__}, {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)


def log_api_request(url: str, data: dict, logger: Optional[logging.Logger] = None) -> None:
    """记录API请求信息
    
    Args:
        url: 请求URL
        data: 请求数据
        logger: 日志记录器，如果为None则使用根记录器
    """
    if logger is None:
        logger = logging.getLogger()
    
    # 创建请求数据的副本，移除敏感信息
    safe_data = data.copy()
    if 'messages' in safe_data:
        # 只保留消息类型和长度信息
        safe_data['messages'] = [
            {'role': msg.get('role'), 'content_length': len(str(msg.get('content', '')))} 
            for msg in safe_data.get('messages', [])
        ]
    
    logger.debug(f"API请求: {url}, 数据: {safe_data}")


def log_api_response(response: dict, logger: Optional[logging.Logger] = None) -> None:
    """记录API响应信息
    
    Args:
        response: 响应数据
        logger: 日志记录器，如果为None则使用根记录器
    """
    if logger is None:
        logger = logging.getLogger()
    
    # 创建响应数据的副本，移除敏感信息或过长内容
    safe_response = {}
    if isinstance(response, dict):
        safe_response = response.copy()
        if 'choices' in safe_response and safe_response['choices']:
            for choice in safe_response['choices']:
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    choice['message']['content_length'] = len(content)
                    choice['message']['content_preview'] = content[:100] + '...' if len(content) > 100 else content
                    del choice['message']['content']
    
    logger.debug(f"API响应: {safe_response}")