# -*- coding: utf-8 -*-
# 应用文本配置

# 应用文本字典（简体中文）
TEXTS = {
    # 应用基础信息
    "app_name": "AI易学分析系统",
    "app_version": "版本",
    
    # 菜单和导航
    "menu_file": "文件",
    "menu_edit": "编辑",
    "menu_view": "查看",
    "menu_tools": "工具",
    "menu_help": "帮助",
    "menu_language": "语言",
    "menu_theme": "主题",
    "menu_settings": "设置",
    "menu_about": "关于",
    "menu_exit": "退出",
    
    # 按钮文本
    "btn_ok": "确定",
    "btn_cancel": "取消",
    "btn_yes": "是",
    "btn_no": "否",
    "btn_save": "保存",
    "btn_load": "加载",
    "btn_export": "导出",
    "btn_import": "导入",
    "btn_delete": "删除",
    "btn_clear": "清空",
    "btn_send": "发送",
    "btn_analyze": "分析",
    "btn_refresh": "刷新",
    "btn_search": "搜索",
    "btn_close": "关闭",
    
    # 输入框和标签
    "label_question": "请输入您的问题",
    "label_divination_method": "起卦方式",
    "label_model": "选择模型",
    "label_history": "历史记录",
    "label_result": "分析结果",
    "label_status": "状态",
    
    # 输入区域标签
    "input_question_label": "问题",
    "input_question_placeholder": "请输入您要咨询的问题...",
    "input_divination_label": "起卦方式",
    "input_model_label": "模型选择",
    
    # 标签页标题
    "tab_hexagram": "卦象信息",
    "tab_result": "解读结果",
    "tab_chat": "对话交流",
    "tab_history": "历史记录",
    "tab_settings": "设置",
    
    # 卦象说明
    "hexagram_instruction": "请在下方输入卦象信息",
    
    # 占卜方式
    "divination_liuyao": "六爻",
    "divination_qimen": "奇门遁甲",
    "divination_daliuren": "大六壬",
    "divination_jinkoujue": "金口诀",
    "divination_bazi": "八字",
    "divination_heluo": "河洛理数",
    "divination_xuankong": "玄空择日",
    "divination_ziwei": "紫微斗数",
    "divination_meihua": "梅花易数",
    "divination_taiyi": "太乙神数",
    
    # 解读结果提示语
    "result_welcome_text": "📖 解读结果\n\n欢迎使用AI易学解读功能！\n\n使用步骤：\n1. 在左侧输入您要咨询的问题\n2. 选择合适的易学体系\n3. 点击开始分析按钮\n4. 等待AI分析完成\n5. 解读结果将在此处显示\n\n✨ 开始您的易学探索之旅",
    
    # 状态信息
    "status_ready": "就绪",
    "status_analyzing": "分析中...",
    "status_completed": "分析完成",
    "status_error": "发生错误",
    "status_connecting": "连接中...",
    "status_connected": "已连接",
    "status_disconnected": "连接中断",
    
    # 消息提示
    "msg_success": "成功",
    "msg_error": "错误",
    "msg_warning": "警告",
    "msg_info": "信息",
    "msg_confirm": "确认",
    "msg_question": "询问",
    
    # 历史记录
    "history_title": "历史记录",
    "history_empty": "暂无历史记录",
    "history_export_success": "历史记录导出成功",
    "history_export_error": "历史记录导出失败",
    "history_delete_success": "记录删除成功",
    "history_delete_error": "记录删除失败",
    "history_delete_confirm": "确定要删除这条记录吗？",
    "history_clear_success": "历史记录清空成功",
    "history_clear_error": "历史记录清空失败",
    "history_clear_confirm": "确定要清空所有历史记录吗？",
    "history_search_label": "搜索:",
    "history_search_placeholder": "输入关键词搜索问题、结果或标签...",
    "history_method_label": "方式:",
    "history_date_label": "日期:",
    "history_list_title": "历史记录列表",
    "history_detail_title": "记录详情",
    "history_detail_placeholder": "请选择一条历史记录查看详情...",
    "history_stats_total": "总记录数:",
    "history_stats_showing": "显示记录数:",
    "history_export_btn": "导出记录",
    "history_delete_btn": "删除记录",
    "history_clear_btn": "清空所有",
    "history_column_time": "时间",
    "history_column_question": "问题",
    "history_column_method": "起卦方式",
    "history_column_model": "模型",
    "history_filter_all": "全部",
    "history_filter_today": "今天",
    "history_filter_week": "最近7天",
    "history_filter_month": "最近30天",
    "history_filter_custom": "自定义",
    
    # 设置界面
    "settings_title": "设置",
    "settings_general": "常规",
    "settings_appearance": "外观",
    "settings_language": "语言",
    "settings_theme": "主题",
    "settings_font": "字体",
    "settings_api": "API设置",
    "settings_advanced": "高级",
    
    # 主题选项
    "theme_light": "浅色主题",
    "theme_dark": "深色主题",
    "theme_auto": "跟随系统",
    
    # 错误信息
    "error_network": "网络连接错误",
    "error_api": "API调用失败",
    "error_file": "文件操作失败",
    "error_invalid_input": "输入内容无效",
    "error_unknown": "未知错误",
    
    # 帮助信息
    "help_about": "关于软件",
    "help_usage": "使用说明",
    "help_contact": "联系我们",
    "help_version": "版本信息",
    
    # 聊天相关
    "chat_welcome_text": "💬 对话交流\n\n欢迎使用AI对话功能！\n\n在这里您可以：\n1. 与AI进行深入的易学讨论\n2. 询问关于卦象的详细解释\n3. 探讨占卜结果的具体含义\n4. 获得个性化的建议和指导\n\n✨ 开始您的智慧对话之旅",
    "chat_model_label": "模型选择",
    "chat_input_placeholder": "请输入您的问题或想法..."
}

# 获取文本的函数
def get_text(key: str) -> str:
    """获取指定键的文本"""
    return TEXTS.get(key, key)

# 兼容性函数（保持与原有代码的兼容性）
def t(key: str) -> str:
    """翻译文本的便捷函数"""
    return get_text(key)