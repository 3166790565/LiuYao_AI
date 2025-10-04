#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录管理界面框架
提供历史记录的查看、搜索、管理功能
"""

from datetime import datetime, timedelta
from tkinter import ttk, filedialog
from typing import List, Optional

import customtkinter as ctk

from config.settings import DIVINATION_METHODS
from config.ui_config import UI_SETTINGS
from utils.logger import setup_logger

logger = setup_logger(__name__)
from config.languages import t
from utils.history import HistoryManager, HistoryRecord
from utils.logger import setup_logger
from utils.ui_components import IOSMessageBox

logger = setup_logger(__name__)

class HistoryFrame(ctk.CTkFrame):
    """历史记录管理界面"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            **kwargs
        )
        
        # 历史记录管理器
        self.history_manager = HistoryManager()
        
        # 当前显示的记录列表
        self.current_records: List[HistoryRecord] = []
        self.selected_record: Optional[HistoryRecord] = None
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 创建界面组件
        self.create_widgets()
        
        # 加载历史记录
        self.refresh_records()
    
    def create_widgets(self):
        """创建界面组件"""
        # 1. 搜索和过滤区域
        self.create_search_frame()
        
        # 2. 记录列表区域
        self.create_records_frame()
        
        # 3. 操作按钮区域
        self.create_action_frame()
    
    def create_search_frame(self):
        """创建搜索和过滤区域"""
        search_frame = ctk.CTkFrame(
            self,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['gray_1']
        )
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        search_frame.grid_columnconfigure(1, weight=1)
        
        # 搜索标签
        search_label = ctk.CTkLabel(
            search_frame,
            text=t("history_search_label"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        search_label.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="w")
        
        # 搜索输入框
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=t("history_search_placeholder"),
            font=ctk.CTkFont(size=12),
            height=32
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # 起卦方式过滤
        method_label = ctk.CTkLabel(
            search_frame,
            text=t("history_method_label"),
            font=ctk.CTkFont(size=12)
        )
        method_label.grid(row=0, column=2, padx=(10, 5), pady=10, sticky="w")
        
        self.method_combobox = ctk.CTkComboBox(
            search_frame,
            values=[t("history_filter_all")] + DIVINATION_METHODS,
            command=self.on_filter_changed,
            width=120,
            height=32
        )
        self.method_combobox.set(t("history_filter_all"))
        self.method_combobox.grid(row=0, column=3, padx=5, pady=10)
        
        # 日期范围过滤
        date_label = ctk.CTkLabel(
            search_frame,
            text=t("history_date_label"),
            font=ctk.CTkFont(size=12)
        )
        date_label.grid(row=0, column=4, padx=(10, 5), pady=10, sticky="w")
        
        self.date_combobox = ctk.CTkComboBox(
            search_frame,
            values=[t("history_filter_all"), t("history_filter_today"), 
                   t("history_filter_week"), t("history_filter_month"), 
                   t("history_filter_custom")],
            command=self.on_date_filter_changed,
            width=100,
            height=32
        )
        self.date_combobox.set(t("history_filter_all"))
        self.date_combobox.grid(row=0, column=5, padx=5, pady=10)
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            search_frame,
            text=t("btn_refresh"),
            command=self.refresh_records,
            width=60,
            height=32
        )
        refresh_btn.grid(row=0, column=6, padx=(10, 15), pady=10)
    
    def create_records_frame(self):
        """创建记录列表区域"""
        records_frame = ctk.CTkFrame(
            self,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg']
        )
        records_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        records_frame.grid_columnconfigure(0, weight=1)
        records_frame.grid_rowconfigure(1, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            records_frame,
            text=t("history_list_title"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        # 创建Treeview用于显示记录列表
        tree_frame = ctk.CTkFrame(records_frame, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # 创建Treeview
        self.records_tree = ttk.Treeview(
            tree_frame,
            columns=("time", "question", "method", "model"),
            show="headings",
            height=15
        )
        
        # 设置列标题和宽度
        self.records_tree.heading("time", text=t("history_column_time"))
        self.records_tree.heading("question", text=t("history_column_question"))
        self.records_tree.heading("method", text=t("history_column_method"))
        self.records_tree.heading("model", text=t("history_column_model"))
        
        self.records_tree.column("time", width=150, minwidth=120)
        self.records_tree.column("question", width=300, minwidth=200)
        self.records_tree.column("method", width=100, minwidth=80)
        self.records_tree.column("model", width=100, minwidth=80)
        
        # 绑定选择事件
        self.records_tree.bind("<<TreeviewSelect>>", self.on_record_selected)
        self.records_tree.bind("<Double-1>", self.on_record_double_click)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.records_tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
    
    # 记录详情区域已移除
    
    def create_action_frame(self):
        """创建操作按钮区域"""
        action_frame = ctk.CTkFrame(
            self,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['gray_1']
        )
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(
            action_frame,
            text=f"{t('history_stats_total')} 0",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # 操作按钮
        button_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        
        # 导出按钮
        export_btn = ctk.CTkButton(
            button_frame,
            text=t("history_export_btn"),
            command=self.export_records,
            width=100,
            height=32
        )
        export_btn.grid(row=0, column=0, padx=5)
        
        # 删除按钮
        delete_btn = ctk.CTkButton(
            button_frame,
            text=t("history_delete_btn"),
            command=self.delete_selected_record,
            width=100,
            height=32,
            fg_color=UI_SETTINGS['colors']['danger_color'],
            hover_color=UI_SETTINGS['colors']['gray_3']
        )
        delete_btn.grid(row=0, column=1, padx=5)
        
        # 清空所有按钮
        clear_all_btn = ctk.CTkButton(
            button_frame,
            text=t("history_clear_btn"),
            command=self.clear_all_records,
            width=100,
            height=32,
            fg_color=UI_SETTINGS['colors']['danger_color'],
            hover_color=UI_SETTINGS['colors']['gray_3']
        )
        clear_all_btn.grid(row=0, column=2, padx=5)
        
        action_frame.grid_columnconfigure(1, weight=1)
    
    def refresh_records(self):
        """刷新记录列表"""
        try:
            # 重新加载历史记录
            self.history_manager.load_history()
            
            # 应用当前的搜索和过滤条件
            self.apply_filters()
            
            
            # 更新统计信息
            self.update_statistics()
            
            logger.info("历史记录列表已刷新")
        except Exception as e:
            logger.error(f"刷新历史记录失败: {e}")
            IOSMessageBox.show_error(self, "错误", f"刷新历史记录失败: {e}")
    
    def apply_filters(self):
        """应用搜索和过滤条件"""
        keyword = self.search_entry.get().strip()
        method = self.method_combobox.get()
        date_filter = self.date_combobox.get()
        
        # 构建搜索参数
        search_params = {}
        
        if keyword:
            search_params["keyword"] = keyword
        
        if method != t("history_filter_all"):
            search_params["divination_method"] = method
        
        # 处理日期过滤
        if date_filter != t("history_filter_all"):
            if date_filter == t("history_filter_today"):
                start_date = datetime.now().strftime("%Y-%m-%d")
                search_params["start_date"] = start_date
            elif date_filter == t("history_filter_week"):
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                search_params["start_date"] = start_date
            elif date_filter == t("history_filter_month"):
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                search_params["start_date"] = start_date
        
        # 执行搜索
        self.current_records = self.history_manager.search_records(**search_params)
        
        # 更新列表显示
        self.update_records_display()
    
    def update_records_display(self):
        """更新记录列表显示"""
        # 保存当前选择的记录ID
        selected_id = None
        if self.selected_record:
            selected_id = self.selected_record.id
        
        # 清空现有项目
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        
        # 添加记录
        for record in self.current_records:
            # 截断问题文本以适应显示
            question_display = record.question[:50] + "..." if len(record.question) > 50 else record.question
            
            item_id = self.records_tree.insert("", "end", values=(
                record.timestamp,
                question_display,
                record.divination_method,
                record.model
            ), tags=(record.id,))
            
            # 如果这是之前选择的记录，重新选择它
            if selected_id and str(record.id) == str(selected_id):
                self.records_tree.selection_set(item_id)
                self.records_tree.focus(item_id)
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.history_manager.get_statistics()
        total = len(self.current_records)
        total_all = len(self.history_manager.records)
        
        if total == total_all:
            stats_text = f"{t('history_stats_total')} {total}"
        else:
            stats_text = f"{t('history_stats_showing')} {total} / {t('history_stats_total')} {total_all}"
        
        self.stats_label.configure(text=stats_text)
    
    def on_search_changed(self, event=None):
        """搜索内容变化事件"""
        self.apply_filters()
    
    def on_filter_changed(self, value=None):
        """过滤条件变化事件"""
        self.apply_filters()
    
    def on_date_filter_changed(self, value=None):
        """日期过滤变化事件"""
        if value == "自定义":
            # 自定义日期范围功能暂未实现
            pass
        self.apply_filters()
    
    def on_record_selected(self, event=None):
        """记录选择事件"""
        selection = self.records_tree.selection()
        if selection:
            item = self.records_tree.item(selection[0])
            record_id = item["tags"][0] if item["tags"] else None
            
            if record_id:
                # 查找对应的记录
                found = False
                for record in self.current_records:
                    # 处理ID格式差异：移除下划线进行比较
                    record_id_clean = str(record.id).replace('_', '')
                    target_id_clean = str(record_id).replace('_', '')
                    
                    if record_id_clean == target_id_clean:
                        self.selected_record = record
                        logger.info(f"已选择记录: {record.id}")
                        found = True
                        break
                
                if not found:
                    self.selected_record = None
                    logger.warning(f"未找到ID为 {record_id} 的记录")
            else:
                self.selected_record = None
                logger.warning("选择的项目没有有效的ID标签")
        else:
            self.selected_record = None
            logger.info("取消选择记录")
    
    def on_record_double_click(self, event=None):
        """记录双击事件 - 自动填写历史记录到主界面"""
        # 获取双击的项目
        selection = self.records_tree.selection()
        if not selection:
            logger.warning("没有选中的记录")
            return
            
        item = self.records_tree.item(selection[0])
        record_id = item["tags"][0] if item["tags"] else None
        
        # 查找对应的记录
        selected_record = None
        for record in self.current_records:
            # 处理ID格式差异：移除下划线进行比较
            record_id_clean = str(record.id).replace('_', '')
            target_id_clean = str(record_id).replace('_', '')
            if record_id_clean == target_id_clean:
                selected_record = record
                break
                
        if selected_record:
            logger.info(f"自动填写历史记录: {selected_record.question[:30]}...")
            try:
                # 获取主应用程序实例
                app = self.master
                while app and not hasattr(app, 'input_frame'):
                    app = app.master
                
                if app and hasattr(app, 'input_frame') and hasattr(app, 'notebook_frame'):
                    # 填写问题内容
                    app.input_frame.set_question(selected_record.question)

                    # 填写用神内容
                    app.input_frame.set_yongshen(selected_record.yongshen)

                    # 填写方面内容
                    app.input_frame.set_fangmian(selected_record.fangmian)
                    
                    # 填写起卦方式
                    app.input_frame.set_divination_method(selected_record.divination_method)
                    
                    # 填写模型
                    # app.input_frame.set_model(selected_record.model)
                    
                    # 填写卦象信息
                    if selected_record.hexagram_info:
                        app.notebook_frame.set_hexagram_content(selected_record.hexagram_info)
                    
                    # 填写解读结果
                    if selected_record.analysis_result:
                        app.notebook_frame.set_result_content(selected_record.analysis_result)
                        # 启用聊天功能
                        app.notebook_frame.enable_chat()
                    
                    # 无论是否有聊天记录，都先清空当前聊天区域
                    app.notebook_frame.clear_welcome_message()
                    app.notebook_frame.clear_chat(add_welcome=False)
                    
                    # 加载聊天历史记录（如果有）
                    if hasattr(selected_record, 'chat_messages') and selected_record.chat_messages:
                        # 恢复历史聊天记录（不使用打字机效果）
                        for msg in selected_record.chat_messages:
                            if 'message' in msg and 'is_user' in msg:
                                app.notebook_frame.add_chat_bubble(
                                    message=msg['message'],
                                    is_user=msg['is_user'],
                                    is_error=msg.get('is_error', False),
                                    use_typing_effect=False  # 禁用打字机效果
                                )
                        
                        # 添加历史记录分割线
                        app.notebook_frame.add_history_divider()
                        
                        # 设置标志，表示已加载历史记录
                        app.notebook_frame.is_first_chat_message = False
                    
                    # 切换到卦象信息标签页
                    app.notebook_frame.select_tab(0)
                    
                    logger.info(f"已自动填写历史记录: {selected_record.question[:30]}...")
                    
                else:
                    logger.error("无法找到主应用程序实例")
                    
            except Exception as e:
                logger.error(f"自动填写历史记录时出错: {e}")
    
    # 记录详情显示方法已移除
    
    def export_records(self):
        """导出记录"""
        if not self.current_records:
            # 没有可导出的记录，记录到日志
            logger.warning("没有可导出的记录")
            return
        
        # 选择导出格式
        format_dialog = ctk.CTkInputDialog(
            text="选择导出格式 (json/csv):",
            title="导出格式"
        )
        export_format = format_dialog.get_input()
        
        if not export_format or export_format.lower() not in ["json", "csv"]:
            return
        
        # 选择保存位置
        file_extension = export_format.lower()
        filename = filedialog.asksaveasfilename(
            title="保存导出文件",
            defaultextension=f".{file_extension}",
            filetypes=[(f"{file_extension.upper()} files", f"*.{file_extension}")]
        )
        
        if filename:
            try:
                content = self.history_manager.export_records(self.current_records, export_format.lower())
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 导出成功，记录到日志
                logger.info(f"已导出 {len(self.current_records)} 条记录到 {filename}")
                logger.info(f"导出 {len(self.current_records)} 条记录到 {filename}")
            except Exception as e:
                logger.error(f"导出记录失败: {e}")
                # 导出失败，已记录到日志
    
    def delete_selected_record(self):
        """删除选中的记录"""
        if not self.selected_record:
            # 请先选择要删除的记录，记录到日志
            logger.warning("请先选择要删除的记录")
            return
        
        # 直接删除，不再确认
        if True:  # 移除确认弹窗，直接执行删除
            if self.history_manager.delete_record(self.selected_record.id):
                # 记录删除成功，记录到日志
                logger.info("记录已删除")
                self.refresh_records()
                
                # 清空选中记录
                self.selected_record = None
    
    # 记录详情显示方法已移除
    
    def export_records(self):
        """导出记录"""
        if not self.current_records:
            # 没有可导出的记录，记录到日志
            logger.warning("没有可导出的记录")
            return
        
        # 选择导出格式
        format_dialog = ctk.CTkInputDialog(
            text="选择导出格式 (json/csv):",
            title="导出格式"
        )
        export_format = format_dialog.get_input()
        
        if not export_format or export_format.lower() not in ["json", "csv"]:
            return
        
        # 选择保存位置
        file_extension = export_format.lower()
        filename = filedialog.asksaveasfilename(
            title="保存导出文件",
            defaultextension=f".{file_extension}",
            filetypes=[(f"{file_extension.upper()} files", f"*.{file_extension}")]
        )
        
        if filename:
            try:
                content = self.history_manager.export_records(self.current_records, export_format.lower())
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 导出成功，记录到日志
                logger.info(f"已导出 {len(self.current_records)} 条记录到 {filename}")
                logger.info(f"导出 {len(self.current_records)} 条记录到 {filename}")
            except Exception as e:
                logger.error(f"导出记录失败: {e}")
                # 导出失败，已记录到日志
    
    def clear_all_records(self):
        """清空所有历史记录"""
        try:
            if self.history_manager.clear_all_records():
                self.refresh_records()
                self.selected_record = None
                
                logger.info("所有历史记录已清空")
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            IOSMessageBox.show_error(self, "错误", f"清空失败: {e}")
    

    
    def update_theme(self):
        """更新主题颜色"""
        try:
            from config.ui_config import get_ui_settings
            # 更新UI设置
            ui_settings = get_ui_settings()
            colors = ui_settings['colors']
            
            # 更新主框架背景色
            self.configure(fg_color=colors['card_bg'])
            
            # 更新所有子框架的背景色
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    # 检查是否是搜索框架或操作框架（使用gray_1背景）
                    if hasattr(child, '_fg_color') and child._fg_color == UI_SETTINGS['colors']['gray_1']:
                        child.configure(fg_color=colors['gray_1'])
                    else:
                        child.configure(fg_color=colors['card_bg'])
            
            # 更新搜索输入框
            if hasattr(self, 'search_entry'):
                self.search_entry.configure(
                    fg_color=colors['bg_color'],
                    text_color=colors['text_color']
                )
            
            # 更新下拉框
            if hasattr(self, 'method_combobox'):
                self.method_combobox.configure(
                    fg_color=colors['bg_color'],
                    text_color=colors['text_color'],
                    dropdown_fg_color=colors['card_bg'],
                    dropdown_text_color=colors['text_color']
                )
            
            if hasattr(self, 'date_combobox'):
                self.date_combobox.configure(
                    fg_color=colors['bg_color'],
                    text_color=colors['text_color'],
                    dropdown_fg_color=colors['card_bg'],
                    dropdown_text_color=colors['text_color']
                )
            
            # 更新详情文本框
            if hasattr(self, 'detail_text'):
                self.detail_text.configure(
                    fg_color=colors['bg_color'],
                    text_color=colors['text_color']
                )
            
            # 更新Treeview样式（需要通过ttk.Style）
            if hasattr(self, 'records_tree'):
                try:
                    style = ttk.Style()
                    style.theme_use('clam')  # 使用clam主题以支持更多自定义
                    
                    # 设置Treeview的背景色和前景色
                    style.configure('Treeview',
                                  background=colors['bg_color'],
                                  foreground=colors['text_color'],
                                  fieldbackground=colors['bg_color'],
                                  borderwidth=0)
                    
                    # 设置Treeview标题的样式
                    style.configure('Treeview.Heading',
                                  background=colors['gray_1'],
                                  foreground=colors['text_color'],
                                  borderwidth=1,
                                  relief='solid')
                    
                    # 设置选中行的样式
                    style.map('Treeview',
                             background=[('selected', colors['primary_alpha_20'])],
                             foreground=[('selected', colors['text_color'])])
                    
                except Exception as e:
                    logger.warning(f"更新Treeview样式时出错: {e}")
            
            logger.debug("HistoryFrame主题已更新")
        except Exception as e:
            logger.error(f"更新HistoryFrame主题时出错: {e}")