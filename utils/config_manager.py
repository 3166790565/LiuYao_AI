# -*- coding: utf-8 -*-
"""
配置管理模块
提供应用程序配置的保存和加载功能
"""

import json
import os
from typing import Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "app_config.json"):
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                logger.info(f"成功加载配置文件: {self.config_file}")
            else:
                logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                self.config_data = {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            self.config_data = {}
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config_data[key] = value
    
    def get_theme_mode(self) -> str:
        """获取主题模式"""
        return self.get('theme_mode', 'light')
    
    def set_theme_mode(self, mode: str) -> None:
        """设置主题模式"""
        self.set('theme_mode', mode)
        logger.info(f"主题模式已设置为: {mode}")
    
    def get_window_geometry(self) -> Optional[str]:
        """获取窗口几何信息"""
        return self.get('window_geometry')
    
    def set_window_geometry(self, geometry: str) -> None:
        """设置窗口几何信息"""
        self.set('window_geometry', geometry)
    
    def get_last_divination_method(self) -> Optional[str]:
        """获取上次使用的占卜方法"""
        return self.get('last_divination_method')
    
    def set_last_divination_method(self, method: str) -> None:
        """设置上次使用的占卜方法"""
        self.set('last_divination_method', method)
    
    def get_last_model(self) -> Optional[str]:
        """获取上次使用的模型"""
        return self.get('last_model')
    
    def set_last_model(self, model: str) -> None:
        """设置上次使用的模型"""
        self.set('last_model', model)

# 全局配置管理器实例
config_manager = ConfigManager()