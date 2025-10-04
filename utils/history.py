#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录管理模块
提供历史记录的存储、查询、管理功能
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any

from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class HistoryRecord:
    """历史记录数据模型"""
    id: str
    timestamp: str
    question: str
    divination_method: str
    yongshen: str
    fangmian: str
    model: str
    hexagram_info: str
    analysis_result: str
    tags: List[str] = None
    chat_messages: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.chat_messages is None:
            self.chat_messages = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryRecord':
        """从字典创建记录"""
        return cls(**data)

class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, history_file: str = "data/history.json"):
        self.history_file = history_file
        self.records: List[HistoryRecord] = []
        self.load_history()
    
    def load_history(self) -> None:
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [HistoryRecord.from_dict(record) for record in data]
                logger.info(f"加载了 {len(self.records)} 条历史记录")
            else:
                self.records = []
                logger.info("历史记录文件不存在，创建新的记录列表")
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self.records = []
    
    def save_history(self) -> bool:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = [record.to_dict() for record in self.records]
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(self.records)} 条历史记录")
            return True
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            return False

    def add_record(self, question: str, divination_method: str, yongshen: str, fangmian: str, model: str,
                   hexagram_info: str, analysis_result: str, tags: List[str] = None,
                   chat_messages: List[Dict[str, Any]] = None) -> str:
        """添加新记录"""
        record_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        record = HistoryRecord(
            id=record_id,
            timestamp=timestamp,
            question=question,
            divination_method=divination_method,
            yongshen=yongshen,
            fangmian=fangmian,
            model=model,
            hexagram_info=hexagram_info,
            analysis_result=analysis_result,
            tags=tags or [],
            chat_messages=chat_messages or []
        )
        
        self.records.insert(0, record)  # 新记录插入到开头
        self.save_history()
        logger.info(f"添加新历史记录: {record_id}")
        return record_id
    
    def get_records(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """获取历史记录列表"""
        if limit:
            return self.records[:limit]
        return self.records
    
    def get_record_by_id(self, record_id: str) -> Optional[HistoryRecord]:
        """根据ID获取记录"""
        for record in self.records:
            if record.id == record_id:
                return record
        return None
    
    def search_records(self, keyword: str = "", divination_method: str = "", 
                      start_date: str = "", end_date: str = "") -> List[HistoryRecord]:
        """搜索历史记录"""
        results = self.records
        
        # 关键词搜索
        if keyword:
            keyword = keyword.lower()
            results = [r for r in results if 
                      keyword in r.question.lower() or 
                      keyword in r.analysis_result.lower() or
                      any(keyword in tag.lower() for tag in r.tags)]
        
        # 起卦方式过滤
        if divination_method:
            results = [r for r in results if r.divination_method == divination_method]
        
        # 日期范围过滤
        if start_date:
            results = [r for r in results if r.timestamp >= start_date]
        if end_date:
            results = [r for r in results if r.timestamp <= end_date]
        
        return results
    
    def delete_record(self, record_id: str) -> bool:
        """删除记录"""
        for i, record in enumerate(self.records):
            if record.id == record_id:
                del self.records[i]
                self.save_history()
                logger.info(f"删除历史记录: {record_id}")
                return True
        return False
    
    def clear_all_records(self) -> bool:
        """清空所有历史记录"""
        try:
            self.records = []
            self.save_history()
            logger.info("已清空所有历史记录")
            return True
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            return False
    
    def update_record_tags(self, record_id: str, tags: List[str]) -> bool:
        """更新记录标签"""
        record = self.get_record_by_id(record_id)
        if record:
            record.tags = tags
            self.save_history()
            logger.info(f"更新记录标签: {record_id}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_records = len(self.records)
        if total_records == 0:
            return {
                "total_records": 0,
                "divination_methods": {},
                "models": {},
                "recent_activity": []
            }
        
        # 统计起卦方式
        divination_methods = {}
        for record in self.records:
            method = record.divination_method
            divination_methods[method] = divination_methods.get(method, 0) + 1
        
        # 统计模型使用
        models = {}
        for record in self.records:
            model = record.model
            models[model] = models.get(model, 0) + 1
        
        # 最近活动（最近7天）
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_records = [r for r in self.records if r.timestamp >= seven_days_ago]
        
        return {
            "total_records": total_records,
            "divination_methods": divination_methods,
            "models": models,
            "recent_activity": len(recent_records)
        }
    
    def export_records(self, records: List[HistoryRecord], format: str = "json") -> str:
        """导出记录"""
        if format == "json":
            return json.dumps([record.to_dict() for record in records], 
                            ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题行
            writer.writerow(["ID", "时间", "问题", "起卦方式", "模型", "卦象信息", "分析结果", "标签"])
            
            # 写入数据行
            for record in records:
                writer.writerow([
                    record.id,
                    record.timestamp,
                    record.question,
                    record.divination_method,
                    record.model,
                    record.hexagram_info,
                    record.analysis_result,
                    ",".join(record.tags)
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

# 全局历史记录管理器实例
history_manager = HistoryManager()