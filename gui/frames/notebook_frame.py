# gui/frames/notebook_frame.py

import tkinter as tk
from tkinter import scrolledtext

import customtkinter as ctk

from config.languages import t
from config.settings import DEFAULT_MODEL, SUPPORTED_MODELS
from config.ui_config import UI_SETTINGS
from utils.animation import typing_animation
from utils.logger import setup_logger
from .history_frame import HistoryFrame

logger = setup_logger(__name__)

class NotebookFrame(ctk.CTkFrame):
    """应用程序选项卡区域，包含卦象信息、解读结果和对话选项卡"""
    
    def __init__(self, master, on_tab_changed=None, **kwargs):
        super().__init__(
            master, 
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            **kwargs
        )
        
        # 保存回调函数
        self.on_tab_changed_callback = on_tab_changed
        
        # 配置网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 创建选项卡区域组件
        self.create_widgets()
    
    def create_widgets(self):
        """创建选项卡区域的组件"""
        # 创建选项卡控件
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            segmented_button_fg_color=UI_SETTINGS['colors']['gray_2'],
            segmented_button_selected_color=UI_SETTINGS['colors']['primary_color'],
            segmented_button_selected_hover_color=UI_SETTINGS['colors']['primary_alpha_20'],
            segmented_button_unselected_color=UI_SETTINGS['colors']['gray_2'],
            segmented_button_unselected_hover_color=UI_SETTINGS['colors']['gray_3'],
            text_color=UI_SETTINGS['colors']['text_color'],
            text_color_disabled=UI_SETTINGS['colors']['secondary_text']
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # 创建选项卡
        self.hexagram_tab = self.tabview.add(t("tab_hexagram"))
        self.result_tab = self.tabview.add(t("tab_result"))
        self.chat_tab = self.tabview.add(t("tab_chat"))
        self.history_tab = self.tabview.add(t("tab_history"))
        self.settings_tab = self.tabview.add(t("tab_settings"))
        
        # 配置选项卡的网格布局
        for tab in [self.hexagram_tab, self.result_tab, self.chat_tab, self.history_tab, self.settings_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)  # 让文本区域可以扩展
        
        # 1. 卦象信息选项卡
        # 卦象输入说明
        self.hexagram_instruction_var = tk.StringVar(value=t("hexagram_instruction"))
        self.hexagram_instruction = ctk.CTkLabel(
            self.hexagram_tab,
            textvariable=self.hexagram_instruction_var,
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=14  # 调整字体大小为14
            ),
            anchor="w",
            wraplength=0  # 自适应宽度
        )
        self.hexagram_instruction.grid(row=0, column=0, sticky="ew", padx=0, pady=0)  # 完全去除上下间距
        
        # 卦象文本框
        self.hexagram_text = scrolledtext.ScrolledText(
            self.hexagram_tab,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg=UI_SETTINGS['colors']['card_bg'],
            fg=UI_SETTINGS['colors']['text_color'],
            insertbackground=UI_SETTINGS['colors']['text_color'],  # 光标颜色
            selectbackground=UI_SETTINGS['colors']['primary_color'],
            selectforeground=UI_SETTINGS['colors']['text_color'],
            relief="solid",
            bd=1,
            highlightbackground=UI_SETTINGS['colors']['gray_3'],
            highlightcolor=UI_SETTINGS['colors']['primary_color'],
            highlightthickness=1,
            padx=10,
            pady=10,
            height=20
        )
        self.hexagram_text.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 2. 解读结果选项卡
        self.result_text = scrolledtext.ScrolledText(
            self.result_tab,
            wrap=tk.WORD,
            font=(UI_SETTINGS['font_family'], 12),
            bg=UI_SETTINGS['colors']['card_bg'],
            fg=UI_SETTINGS['colors']['text_color'],
            insertbackground=UI_SETTINGS['colors']['text_color'],
            selectbackground=UI_SETTINGS['colors']['primary_color'],
            selectforeground=UI_SETTINGS['colors']['text_color'],
            relief="solid",
            bd=1,
            highlightbackground=UI_SETTINGS['colors']['gray_3'],
            highlightcolor=UI_SETTINGS['colors']['primary_color'],
            highlightthickness=1,
            padx=10,
            pady=10,
            height=15
        )
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 配置解读结果文本框的标签样式
        self.result_text.tag_configure('main_text', foreground=UI_SETTINGS['colors']['text_color'])
        self.result_text.tag_configure('explanation', foreground=UI_SETTINGS['colors']['gray_5'])  # 括号内容：淡灰色
        self.result_text.tag_configure('aspect_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=UI_SETTINGS['colors']['primary_color'])  # 方面标题：加粗变色
        self.result_text.tag_configure('conclusion_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=UI_SETTINGS['colors']['danger_color'])  # 结论标题：加粗变色
        self.result_text.tag_configure('question', font=(UI_SETTINGS['font_family'], 14, 'bold'))
        self.result_text.tag_configure('hexagram', font=("Consolas", 13))
        self.result_text.tag_configure('separator', foreground=UI_SETTINGS['colors']['separator'])
        self.result_text.tag_configure('error', foreground=UI_SETTINGS['colors']['danger_color'], font=(UI_SETTINGS['font_family'], 12, 'bold'))  # 错误信息样式
        self.result_text.tag_configure('welcome', font=(UI_SETTINGS['font_family'], 14), foreground=UI_SETTINGS['colors']['secondary_text'], justify='center')
        self.result_text.tag_configure('reference_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=UI_SETTINGS['colors']['primary_color'])  # 参考文献标题样式
        self.result_text.tag_configure('reference_text', foreground=UI_SETTINGS['colors']['gray_5'], font=(UI_SETTINGS['font_family'], 12))  # 参考文献内容样式
        
        # 添加初始欢迎信息
        welcome_text = t("result_welcome_text")
        
        self.result_text.insert(tk.END, welcome_text, 'welcome')
        self.result_text.config(state=tk.DISABLED)  # 设置为只读
        
        # 3. 对话选项卡
        # 创建聊天容器框架
        chat_container = ctk.CTkFrame(self.chat_tab, fg_color="transparent")
        chat_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)
        
        # 创建滚动框架用于聊天气泡
        self.chat_scrollable_frame = ctk.CTkScrollableFrame(
            chat_container,
            corner_radius=UI_SETTINGS['component']['card_corner_radius'],
            fg_color=UI_SETTINGS['colors']['card_bg'],
            scrollbar_button_color=UI_SETTINGS['colors']['gray_4'],
            scrollbar_button_hover_color=UI_SETTINGS['colors']['gray_5']
        )
        self.chat_scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.chat_scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # 聊天消息列表
        self.chat_messages = []
        
        # 添加欢迎消息
        self.add_welcome_message()
        
        # 标记是否是第一次发送消息
        self.is_first_chat_message = True
        
        # 底部输入区域
        chat_input_frame = ctk.CTkFrame(self.chat_tab, fg_color=None)
        chat_input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        chat_input_frame.grid_columnconfigure(0, weight=1)
        
        # 模型选择区域
        chat_model_frame = ctk.CTkFrame(chat_input_frame, fg_color=None)
        chat_model_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # 模型选择标签
        self.chat_model_label = ctk.CTkLabel(
            chat_model_frame,
            text=t("chat_model_label"),
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            )
        )
        self.chat_model_label.pack(side="left", padx=(0, 5))
        
        # 聊天模型选择下拉菜单
        self.chat_model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.chat_model_menu = ctk.CTkOptionMenu(
            chat_model_frame,
            values=SUPPORTED_MODELS,
            variable=self.chat_model_var,
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            ),
            dropdown_font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            ),
            width=150,
            fg_color=UI_SETTINGS['colors']['primary_color'],
            button_color=UI_SETTINGS['colors']['primary_color'],
            button_hover_color=UI_SETTINGS['colors']['primary_alpha_20']
        )
        self.chat_model_menu.pack(side="left")
        
        # 输入框和发送按钮容器
        input_container = ctk.CTkFrame(chat_input_frame, fg_color=None)
        input_container.grid(row=1, column=0, sticky="ew")
        input_container.grid_columnconfigure(0, weight=1)  # 让输入框列可以扩展
        
        # 输入框
        self.chat_entry = ctk.CTkEntry(
            input_container,
            placeholder_text=t("chat_input_placeholder"),
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=14
            ),
            height=35
        )
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.chat_entry.bind("<Return>", lambda event: self.send_chat_message())
        
        # 发送按钮
        self.send_button = ctk.CTkButton(
            input_container,
            text="发送",
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=12
            ),
            width=80,
            height=35,
            command=self.send_chat_message,
            fg_color=UI_SETTINGS['colors']['primary_color'],
            hover_color=UI_SETTINGS['colors']['primary_alpha_20']
        )
        self.send_button.grid(row=0, column=1)
        
        # 初始禁用聊天功能，直到有解读结果
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        
        # 4. 历史记录选项卡
        self.history_frame = HistoryFrame(self.history_tab)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # 5. 设置选项卡
        from .settings_frame import SettingsFrame
        self.settings_frame = SettingsFrame(self.settings_tab)
        self.settings_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # 绑定选项卡切换事件
        # 使用正确的方法绑定标签页切换事件
        self.tabview.configure(command=self._on_tab_changed)
    
    def _on_tab_changed(self):
        """选项卡切换事件内部处理"""
        if self.on_tab_changed_callback:
            current_tab = self.tabview.get()
            self.on_tab_changed_callback(current_tab)
    
    def get_current_tab(self):
        """获取当前选中的选项卡索引"""
        return self.tabview.get()
    
    def select_tab(self, index):
        """选择指定的选项卡"""
        tabs = [t("tab_hexagram"), t("tab_result"), t("tab_chat")]
        if 0 <= index < len(tabs):
            self.tabview.set(tabs[index])
    
    def update_hexagram_instruction(self, divination_method):
        """更新卦象输入说明"""
        instruction = f"请在下方输入{divination_method}信息："
        self.hexagram_instruction_var.set(instruction)
    
    def get_hexagram_content(self):
        """获取卦象文本内容"""
        return self.hexagram_text.get(1.0, tk.END).strip()
    
    def set_hexagram_content(self, content):
        """设置卦象文本内容"""
        try:
            self.hexagram_text.delete(1.0, tk.END)
            self.hexagram_text.insert(1.0, content)
        except Exception as e:
            logger.error(f"设置卦象内容时出错: {e}")
    
    def set_result_content(self, content):
        """设置解读结果内容"""
        try:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # 解析并应用格式化
            self._parse_and_format_content(content)
            
            self.result_text.config(state=tk.DISABLED)
        except Exception as e:
            logger.error(f"设置解读结果时出错: {e}")
    
    def _parse_and_format_content(self, content):
        """解析内容并应用格式化标签"""
        import re
        
        def insert_text_with_brackets(text, default_tag='main_text'):
            """处理包含括号的文本，为括号内容应用特殊格式"""
            # 处理圆括号
            if '（' in text and '）' in text:
                parts = re.split(r'(（[^）]*）)', text)
                for part in parts:
                    if part.startswith('（') and part.endswith('）'):
                        self.result_text.insert(tk.END, part, 'explanation')
                    elif part.strip():
                        self.result_text.insert(tk.END, part, default_tag)
            # 处理方括号
            elif '[' in text and ']' in text:
                parts = re.split(r'(\[[^\]]*\])', text)
                for part in parts:
                    if part.startswith('[') and part.endswith(']'):
                        self.result_text.insert(tk.END, part, 'explanation')
                    elif part.strip():
                        self.result_text.insert(tk.END, part, default_tag)
            else:
                # 没有括号，直接插入
                if text.strip():
                    self.result_text.insert(tk.END, text, default_tag)
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.result_text.insert(tk.END, '\n')
                continue

            # 检查是否是【】格式的标题（如：【用神判断】、【用神卦理分析】等）
            if re.match(r'^【[^】]*】$', line):
                title = line.replace('【', '').replace('】', '')
                self.result_text.insert(tk.END, title + '\n', 'aspect_title')
            # 检查是否是数字编号标题（如：1、当前财务状况：、2、财运的变化趋势：等）
            title_match = re.match(r'^(\d+、[^：:]*[：:])(.*)$', line)
            if title_match:
                title_part = title_match.group(1)  # 标题部分
                content_part = title_match.group(2)  # 内容部分
                self.result_text.insert(tk.END, title_part, 'aspect_title')
                if content_part.strip():
                    insert_text_with_brackets(content_part, 'main_text')
                self.result_text.insert(tk.END, '\n')
            # 检查是否是方面标题（如：**事业运势**、**感情运势**等）
            elif re.match(r'^\*\*.*\*\*$', line):
                title = line.replace('**', '')
                self.result_text.insert(tk.END, title + '\n', 'aspect_title')
            # 检查是否是结论标题（只匹配以"结论"开头且包含冒号的行）
            elif re.match(r'^结论[：:]', line):
                conclusion_match = re.match(r'^(结论[：:])(.*)$', line)
                if conclusion_match:
                    title_part = conclusion_match.group(1)  # "结论："部分
                    content_part = conclusion_match.group(2)  # 内容部分
                    self.result_text.insert(tk.END, title_part, 'conclusion_title')
                    if content_part.strip():
                        insert_text_with_brackets(content_part, 'main_text')
                    self.result_text.insert(tk.END, '\n')
                else:
                    self.result_text.insert(tk.END, line + '\n', 'conclusion_title')
            # 检查是否是参考文件标题
            elif re.match(r'^参考文件[：:]', line):
                self.result_text.insert(tk.END, line, 'reference_title')
                self.result_text.insert(tk.END, '\n')
            # 检查是否是参考文件列表项（以•开头）
            elif line.startswith('•'):
                self.result_text.insert(tk.END, line, 'reference_text')
                self.result_text.insert(tk.END, '\n')
            # 普通文本（包含括号内容的处理）
            else:
                insert_text_with_brackets(line, 'main_text')
                self.result_text.insert(tk.END, '\n')
    
    def clear_result(self):
        """清空解读结果"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        # 重新添加欢迎信息
        welcome_text = t("result_welcome_text")
        self.result_text.insert(tk.END, welcome_text, 'welcome')
        self.result_text.config(state=tk.DISABLED)
    
    def clear_all(self):
        """清空所有内容"""
        self.hexagram_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        # 禁用聊天功能
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
    
    def insert_result(self, text, tag=None):
        """插入解读结果文本"""
        self.result_text.config(state=tk.NORMAL)
        # 如果是第一次插入结果，先清空欢迎信息
        current_content = self.result_text.get(1.0, tk.END).strip()
        if "欢迎使用AI易学解读功能" in current_content:
            self.result_text.delete(1.0, tk.END)
        
        if tag:
            self.result_text.insert(tk.END, text, tag)
        else:
            self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)  # 滚动到底部
        self.result_text.config(state=tk.DISABLED)
    
    def insert_result_with_animation(self, text, tag=None, speed=30):
        """使用打字机效果插入解读结果文本"""
        typing_animation(self.result_text, text, tag, speed)
    
    def enable_chat(self):
        """启用聊天功能"""
        self.chat_entry.configure(state="normal")
        self.send_button.configure(state="normal")
    
    def send_chat_message(self):
        """发送聊天消息"""
        # 获取用户输入
        user_message = self.chat_entry.get().strip()
        if not user_message:
            return
        
        # 立即清空输入框
        self.chat_entry.delete(0, tk.END)
        
        # 禁用输入框和发送按钮
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        
        # 添加加载动画指示器
        loading_frame = ctk.CTkFrame(
            self.chat_scrollable_frame,
            fg_color="transparent"
        )
        loading_frame.grid(row=len(self.chat_messages) + 1, column=0, sticky="w", padx=10, pady=5)
        
        # 创建动态加载标签
        loading_label = ctk.CTkLabel(
            loading_frame,
            text="",  # 初始为空，将通过打字机效果填充
            font=ctk.CTkFont(family=UI_SETTINGS['font_family'], size=12),
            text_color=UI_SETTINGS['colors']['primary_color']
        )
        loading_label.grid(row=0, column=0, sticky="w", padx=5)
        
        # 创建小点指示器
        dots_frame = ctk.CTkFrame(
            loading_frame,
            fg_color="transparent"
        )
        dots_frame.grid(row=0, column=1, sticky="w")
        
        # 创建三个点
        dot_size = 6
        dot1 = ctk.CTkLabel(
            dots_frame,
            text="•",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=UI_SETTINGS['colors']['primary_color'],
            width=dot_size
        )
        dot1.grid(row=0, column=0, padx=2)
        
        dot2 = ctk.CTkLabel(
            dots_frame,
            text="•",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=UI_SETTINGS['colors']['primary_color'],
            width=dot_size
        )
        dot2.grid(row=0, column=1, padx=2)
        
        dot3 = ctk.CTkLabel(
            dots_frame,
            text="•",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=UI_SETTINGS['colors']['primary_color'],
            width=dot_size
        )
        dot3.grid(row=0, column=2, padx=2)
        
        # 保存加载动画引用以便后续移除
        self.loading_frame = loading_frame
        
        # 使用打字机效果显示文本
        from utils.animation import typing_animation, pulse_animation
        
        # 打字机效果显示"AI正在思考中"
        typing_animation(loading_label, "AI正在思考中", delay=80)
        
        # 为三个点添加脉冲动画
        def animate_dots():
            if not hasattr(self, 'loading_frame') or not self.loading_frame.winfo_exists():
                return
                
            pulse_animation(dot1, "text_color", 
                          UI_SETTINGS['colors']['primary_color'], 
                          UI_SETTINGS['colors']['secondary_color'], 
                          duration=600, repeat=1,
                          callback=lambda: pulse_animation(dot2, "text_color", 
                                                        UI_SETTINGS['colors']['primary_color'], 
                                                        UI_SETTINGS['colors']['secondary_color'], 
                                                        duration=600, repeat=1,
                                                        callback=lambda: pulse_animation(dot3, "text_color", 
                                                                                      UI_SETTINGS['colors']['primary_color'], 
                                                                                      UI_SETTINGS['colors']['secondary_color'], 
                                                                                      duration=600, repeat=1,
                                                                                      callback=lambda: self.loading_frame.after(300, animate_dots) if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists() else None)))
        
        # 开始动画
        animate_dots()
        
        # 如果是第一次发送消息，清除欢迎消息
        if self.is_first_chat_message:
            self.clear_welcome_message()
            self.is_first_chat_message = False
        
        # 添加用户消息气泡
        self.add_chat_bubble(user_message, is_user=True)
        
        # 通知主应用程序处理聊天消息
        if hasattr(self.master, "handle_chat_message"):
            self.master.handle_chat_message(user_message, self.chat_model_var.get())
    
    def add_ai_response(self, message, is_error=False):
        """添加AI回复到聊天区域"""
        # 移除加载动画
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')
        
        if is_error:
            # 错误消息使用系统样式
            self.add_chat_bubble(f"系统: {message}", is_user=False, is_error=True)
        else:
            # 添加AI消息气泡
            self.add_chat_bubble(message, is_user=False)
        
        # 重新启用输入框和发送按钮
        self.chat_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        
        # 将焦点设置回输入框
        self.chat_entry.focus_set()
    
    def add_welcome_message(self):
        """添加欢迎消息"""
        welcome_text = t("chat_welcome_text")
        welcome_frame = ctk.CTkFrame(
            self.chat_scrollable_frame,
            fg_color="transparent"
        )
        welcome_frame.grid(row=0, column=0, sticky="ew", pady=20)
        welcome_frame.grid_columnconfigure(0, weight=1)
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(
                family=UI_SETTINGS['font_family'],
                size=14
            ),
            text_color=UI_SETTINGS['colors']['secondary_text'],
            justify="center"
        )
        welcome_label.grid(row=0, column=0, sticky="ew")
        
        self.welcome_frame = welcome_frame
    
    def clear_welcome_message(self):
        """清除欢迎消息"""
        if hasattr(self, 'welcome_frame'):
            self.welcome_frame.destroy()
            delattr(self, 'welcome_frame')
    
    def clear_chat(self, add_welcome=True):
        """清空聊天消息
        
        Args:
            add_welcome: 是否添加欢迎消息，默认为True
        """
        # 删除所有聊天气泡
        for msg in self.chat_messages:
            if 'frame' in msg and msg['frame'].winfo_exists():
                msg['frame'].destroy()
        
        # 清空消息列表
        self.chat_messages = []
        
        # 重新添加欢迎消息（如果需要）
        if add_welcome:
            self.add_welcome_message()
        self.is_first_chat_message = True
    
    def add_chat_bubble(self, message, is_user=True, is_error=False, use_typing_effect=True):
        """添加聊天气泡
        
        Args:
            message: 消息内容
            is_user: 是否是用户消息
            is_error: 是否是错误消息
            use_typing_effect: 是否使用打字机效果（仅对AI消息有效）
        """

        # 创建消息容器
        message_frame = ctk.CTkFrame(
            self.chat_scrollable_frame,
            fg_color="transparent"
        )
        message_frame.grid(row=len(self.chat_messages), column=0, sticky="ew", pady=(10, 5), padx=10)
        message_frame.grid_columnconfigure(0, weight=1)
        
        # 创建主容器（包含头像、标签和气泡）
        main_container = ctk.CTkFrame(
            message_frame,
            fg_color="transparent"
        )
        
        if is_user:
            # 用户消息居右
            main_container.grid(row=0, column=0, sticky="e", padx=(50, 0))
            bubble_bg_color = UI_SETTINGS['colors']['primary_color']
            text_color = "white"
            corner_radius = 18
            label_text = "我"
            avatar_color = UI_SETTINGS['colors']['accent_color']
        else:
            # AI消息居左
            main_container.grid(row=0, column=0, sticky="w", padx=(0, 50))
            if is_error:
                bubble_bg_color = UI_SETTINGS['colors']['danger_color']
                text_color = "white"
            else:
                bubble_bg_color = UI_SETTINGS['colors']['gray_2']
                text_color = UI_SETTINGS['colors']['text_color']
            corner_radius = 18
            label_text = "AI"
            avatar_color = UI_SETTINGS['colors']['secondary_color']
        
        # 创建头像和标签容器
        header_frame = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        
        if is_user:
            # 用户：标签在左，头像在右
            header_frame.grid_columnconfigure(0, weight=1)
            
            # 标签
            label = ctk.CTkLabel(
                header_frame,
                text=label_text,
                font=ctk.CTkFont(family=UI_SETTINGS['font_family'], size=10, weight="bold"),
                text_color=UI_SETTINGS['colors']['text_color']
            )
            label.grid(row=0, column=0, sticky="e", padx=(0, 5))
            
            # 头像
            avatar = ctk.CTkFrame(
                header_frame,
                width=24,
                height=24,
                fg_color=avatar_color,
                corner_radius=12
            )
            avatar.grid(row=0, column=1, sticky="e")
            avatar.grid_propagate(False)
            
            # 头像内的文字
            avatar_label = ctk.CTkLabel(
                avatar,
                text="👤",
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            avatar_label.place(relx=0.5, rely=0.5, anchor="center")
            
        else:
            # AI：头像在左，标签在右
            header_frame.grid_columnconfigure(1, weight=1)
            
            # 头像
            avatar = ctk.CTkFrame(
                header_frame,
                width=24,
                height=24,
                fg_color=avatar_color,
                corner_radius=12
            )
            avatar.grid(row=0, column=0, sticky="w")
            avatar.grid_propagate(False)
            
            # 头像内的文字
            avatar_label = ctk.CTkLabel(
                avatar,
                text="🤖",
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            avatar_label.place(relx=0.5, rely=0.5, anchor="center")
            
            # 标签
            label = ctk.CTkLabel(
                header_frame,
                text=label_text,
                font=ctk.CTkFont(family=UI_SETTINGS['font_family'], size=10, weight="bold"),
                text_color=UI_SETTINGS['colors']['text_color']
            )
            label.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # 创建气泡容器（包含小尾巴）
        bubble_container = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        bubble_container.grid(row=1, column=0, sticky="ew")
        
        # 创建气泡
        bubble = ctk.CTkFrame(
            bubble_container,
            fg_color=bubble_bg_color,
            corner_radius=corner_radius
        )
        
        if is_user:
            # 用户气泡：小尾巴在右上角
            bubble.grid(row=0, column=0, sticky="e", padx=(15, 0), pady=(0, 5))
            # 创建小尾巴（右上角）
            tail = ctk.CTkFrame(
                bubble_container,
                width=8,
                height=8,
                fg_color=bubble_bg_color,
                corner_radius=0
            )
            tail.place(x=bubble.winfo_reqwidth()-4, y=2)
        else:
            # AI气泡：小尾巴在左上角
            bubble.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=(0, 5))
            # 创建小尾巴（左上角）
            tail = ctk.CTkFrame(
                bubble_container,
                width=8,
                height=8,
                fg_color=bubble_bg_color,
                corner_radius=0
            )
            tail.place(x=4, y=2)
        
        # 为AI消息添加CTkLabel组件（不使用富文本）
        if not is_user and not is_error:
            # 直接使用普通文本显示消息
            message_label = ctk.CTkLabel(
                bubble,
                text="",  # 初始为空，将通过打字机效果填充
                font=ctk.CTkFont(
                    family=UI_SETTINGS['font_family'],
                    size=14  # 增大AI回复的字体大小
                ),
                text_color=text_color,
                wraplength=450,  # 加宽AI回复气泡，减少换行
                justify="left",
                anchor="w"
            )
            message_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
            
            # 使用打字机效果显示AI回复（仅当use_typing_effect为True时）
            if use_typing_effect:
                from utils.animation import typing_animation
                typing_animation(message_label, message, delay=15, cursor="|", cursor_blink=True)
            else:
                # 直接显示完整消息，不使用打字机效果
                message_label.configure(text=message)
            
        else:
            # 用户消息或错误消息使用简单的Label
            message_label = ctk.CTkLabel(
                bubble,
                text=message,
                font=ctk.CTkFont(
                    family=UI_SETTINGS['font_family'],
                    size=12
                ),
                text_color=text_color,
                wraplength=300,  # 限制气泡最大宽度
                justify="left",
                anchor="w"
            )
            message_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        
        # 保存消息记录
        self.chat_messages.append({
            'frame': message_frame,
            'message': message,
            'is_user': is_user,
            'is_error': is_error
        })
        
        # 滚动到底部
        self.chat_scrollable_frame._parent_canvas.update_idletasks()
        self.chat_scrollable_frame._parent_canvas.yview_moveto(1.0)
    

    
    def _recreate_tabs(self):
        """重新创建选项卡以更新标题"""
        try:
            # 保存当前选中的选项卡
            current_tab = self.tabview.get()
            
            # 获取当前内容
            hexagram_content = self.hexagram_text.get("1.0", tk.END)
            result_content = self.result_text.get("1.0", tk.END)
            chat_content = self.chat_display.get("1.0", tk.END)
            
            # 删除所有选项卡
            for tab_name in [t("tab_hexagram"), t("tab_result"), t("tab_chat"), t("tab_history")]:
                try:
                    self.tabview.delete(tab_name)
                except:
                    pass
            
            # 重新创建选项卡
            self.hexagram_tab = self.tabview.add(t("tab_hexagram"))
            self.result_tab = self.tabview.add(t("tab_result"))
            self.chat_tab = self.tabview.add(t("tab_chat"))
            self.history_tab = self.tabview.add(t("tab_history"))
            
            # 重新创建内容（简化版本）
            self._recreate_tab_contents(hexagram_content, result_content, chat_content)
            
            # 恢复选中的选项卡
            try:
                self.tabview.set(current_tab)
            except:
                self.tabview.set(t("tab_hexagram"))
                
        except Exception as e:
            logger.error(f"重新创建选项卡时出错: {e}")
    
    def _update_tab_titles(self):
        """更新选项卡标题而不重新创建内容"""
        try:
            # 获取当前选项卡的映射
            current_tabs = list(self.tabview._tab_dict.keys())
            new_titles = [t("tab_hexagram"), t("tab_result"), t("tab_chat"), t("tab_history")]
            
            # 如果标题已经是正确的，就不需要更新
            if current_tabs == new_titles:
                return
                
            # 保存当前选中的选项卡索引
            current_index = 0
            try:
                current_tab = self.tabview.get()
                if current_tab in current_tabs:
                    current_index = current_tabs.index(current_tab)
            except:
                pass
            
            # 更新选项卡标题
            for i, (old_title, new_title) in enumerate(zip(current_tabs, new_titles)):
                if old_title != new_title and old_title in self.tabview._tab_dict:
                    # 获取选项卡内容
                    tab_frame = self.tabview._tab_dict[old_title]
                    # 删除旧标题的选项卡
                    del self.tabview._tab_dict[old_title]
                    # 添加新标题的选项卡
                    self.tabview._tab_dict[new_title] = tab_frame
                    # 更新按钮文本
                    if hasattr(self.tabview, '_segmented_button'):
                        self.tabview._segmented_button.configure(values=list(self.tabview._tab_dict.keys()))
            
            # 恢复选中的选项卡
            if current_index < len(new_titles):
                try:
                    self.tabview.set(new_titles[current_index])
                except:
                    self.tabview.set(new_titles[0])
                    
        except Exception as e:
            logger.error(f"更新选项卡标题时出错: {e}")
    
    def _recreate_tab_contents(self, hexagram_content, result_content, chat_content):
        """重新创建选项卡内容"""
        try:
            # 重新创建卦象选项卡内容
            self._create_hexagram_tab_content()
            if hexagram_content.strip():
                self.hexagram_text.delete("1.0", tk.END)
                self.hexagram_text.insert("1.0", hexagram_content)
            
            # 重新创建解读结果选项卡内容
            self._create_result_tab_content()
            if result_content.strip():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result_content)
            
            # 重新创建聊天选项卡内容
            self._create_chat_tab_content()
            # 聊天气泡会在_create_chat_tab_content中重新创建
            
            # 重新创建历史记录选项卡内容
            self._create_history_tab_content()
            
        except Exception as e:
            logger.error(f"重新创建选项卡内容时出错: {e}")
    
    def update_theme(self):
        """更新主题颜色"""
        try:
            from config.ui_config import get_ui_settings
            ui_settings = get_ui_settings()
            colors = ui_settings['colors']
            
            # 更新frame背景色
            self.configure(fg_color=colors['card_bg'])
            
            # 更新选项卡控件的颜色
            if hasattr(self, 'tabview'):
                self.tabview.configure(
                    fg_color=colors['card_bg'],
                    segmented_button_fg_color=colors['gray_2'],
                    segmented_button_selected_color=colors['primary_color'],
                    segmented_button_selected_hover_color=colors['primary_alpha_20'],
                    segmented_button_unselected_color=colors['gray_2'],
                    segmented_button_unselected_hover_color=colors['gray_3'],
                    text_color=colors['text_color'],
                    text_color_disabled=colors['secondary_text']
                )
            
            # 更新卦象信息文本框 (标准tkinter组件)
            if hasattr(self, 'hexagram_text'):
                self.hexagram_text.configure(
                    bg=colors['card_bg'],
                    fg=colors['text_color']
                )
            
            # 更新结果显示文本框 (标准tkinter组件)
            if hasattr(self, 'result_text'):
                self.result_text.configure(
                    bg=colors['card_bg'],
                    fg=colors['text_color']
                )
                # 重新配置文本标签样式
                self.result_text.tag_configure('main_text', foreground=colors['text_color'])
            self.result_text.tag_configure('explanation', foreground=colors['gray_5'])
            self.result_text.tag_configure('aspect_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=colors['primary_color'])
            self.result_text.tag_configure('conclusion_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=colors['danger_color'])
            self.result_text.tag_configure('question', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=colors['text_color'])
            self.result_text.tag_configure('hexagram', font=("Consolas", 13), foreground=colors['text_color'])
            self.result_text.tag_configure('separator', foreground=colors['separator'])
            self.result_text.tag_configure('error', foreground=colors['danger_color'], font=(UI_SETTINGS['font_family'], 12, 'bold'))
            self.result_text.tag_configure('welcome', font=(UI_SETTINGS['font_family'], 14), foreground=colors['secondary_text'], justify='center')
            self.result_text.tag_configure('reference_title', font=(UI_SETTINGS['font_family'], 14, 'bold'), foreground=colors['primary_color'])  # 参考文献标题样式
            self.result_text.tag_configure('reference_text', foreground=colors['gray_5'], font=(UI_SETTINGS['font_family'], 12))  # 参考文献内容样式
            
            # 更新聊天滚动框架
            if hasattr(self, 'chat_scrollable_frame'):
                self.chat_scrollable_frame.configure(
                    fg_color=colors['card_bg'],
                    scrollbar_button_color=colors['gray_4'],
                    scrollbar_button_hover_color=colors['gray_5']
                )
                
                # 重新创建所有聊天气泡以应用新主题
                self.refresh_chat_bubbles()
            
            # 更新聊天输入框 (customtkinter组件)
            if hasattr(self, 'chat_entry'):
                self.chat_entry.configure(
                    fg_color=colors['card_bg'],
                    text_color=colors['text_color'],
                    placeholder_text_color=colors['secondary_text']
                )
            
            # 更新发送按钮
            if hasattr(self, 'send_button'):
                self.send_button.configure(
                    fg_color=colors['primary_color'],
                    hover_color=colors['primary_alpha_20']
                )
            
            # 更新历史记录列表 (customtkinter组件)
            if hasattr(self, 'history_listbox'):
                self.history_listbox.configure(
                    fg_color=colors['card_bg'],
                    text_color=colors['text_color']
                )
            
            # 更新历史记录框架
            if hasattr(self, 'history_frame') and hasattr(self.history_frame, 'update_theme'):
                self.history_frame.update_theme()
                
            logger.debug("NotebookFrame主题已更新")
        except Exception as e:
            logger.error(f"更新NotebookFrame主题时出错: {e}")
    
    def update_chat_model_list(self):
        """更新聊天模型列表"""
        try:
            from config.settings import SUPPORTED_MODELS
            
            # 获取内置模型（自定义模型功能已移除）
            all_models = list(SUPPORTED_MODELS)
            
            # 获取当前选择的模型
            current_model = self.chat_model_var.get()
            
            # 更新下拉框选项
            self.chat_model_menu.configure(values=all_models)
            
            # 如果当前模型仍在列表中，保持选择
            if current_model in all_models:
                self.chat_model_var.set(current_model)
            else:
                # 否则选择默认模型
                self.chat_model_var.set(SUPPORTED_MODELS[0] if SUPPORTED_MODELS else "")
            
            logger.debug(f"聊天模型列表已更新，共 {len(all_models)} 个模型")
            
        except Exception as e:
            logger.error(f"更新聊天模型列表时出错: {e}")
    
    def refresh_chat_bubbles(self):
        """刷新所有聊天气泡以应用新主题"""
        try:
            if not hasattr(self, 'chat_messages') or not self.chat_messages:
                return
            
            # 保存所有消息数据
            messages_data = []
            for msg in self.chat_messages:
                messages_data.append({
                    'message': msg['message'],
                    'is_user': msg['is_user'],
                    'is_error': msg['is_error'],
                    'is_divider': msg.get('is_divider', False)  # 添加分割线标志
                })
            
            # 清除所有现有的消息框架
            for msg in self.chat_messages:
                if msg['frame'].winfo_exists():
                    msg['frame'].destroy()
            
            # 重置消息列表
            self.chat_messages = []
            
            # 重新创建所有消息气泡
            for msg_data in messages_data:
                if msg_data.get('is_divider', False):
                    self.add_history_divider()
                else:
                    self.add_chat_bubble(
                        msg_data['message'],
                        is_user=msg_data['is_user'],
                        is_error=msg_data['is_error']
                    )
            
            logger.debug(f"已刷新 {len(messages_data)} 个聊天气泡")
            
        except Exception as e:
            logger.error(f"刷新聊天气泡时出错: {e}")
    
    def add_history_divider(self):
        """添加历史记录分割线"""
        try:
            # 创建分割线容器
            divider_frame = ctk.CTkFrame(
                self.chat_scrollable_frame,
                fg_color="transparent"
            )
            divider_frame.grid(row=len(self.chat_messages), column=0, sticky="ew", pady=10, padx=10)
            divider_frame.grid_columnconfigure(0, weight=1)
            
            # 创建分割线
            divider_container = ctk.CTkFrame(
                divider_frame,
                fg_color="transparent",
                height=30
            )
            divider_container.grid(row=0, column=0, sticky="ew")
            divider_container.grid_columnconfigure(0, weight=1)
            divider_container.grid_columnconfigure(2, weight=1)
            
            # 左侧分割线
            left_line = ctk.CTkFrame(
                divider_container,
                fg_color=UI_SETTINGS['colors']['separator'],
                height=1
            )
            left_line.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(15, 0))
            
            # 中间文字
            divider_text = ctk.CTkLabel(
                divider_container,
                text="以上为历史记录",
                font=ctk.CTkFont(
                    family=UI_SETTINGS['font_family'],
                    size=12
                ),
                text_color=UI_SETTINGS['colors']['secondary_text']
            )
            divider_text.grid(row=0, column=1, pady=(10, 0))
            
            # 右侧分割线
            right_line = ctk.CTkFrame(
                divider_container,
                fg_color=UI_SETTINGS['colors']['separator'],
                height=1
            )
            right_line.grid(row=0, column=2, sticky="ew", padx=(10, 0), pady=(15, 0))
            
            # 保存分割线记录
            self.chat_messages.append({
                'frame': divider_frame,
                'message': "以上为历史记录",
                'is_user': False,
                'is_error': False,
                'is_divider': True
            })
            
            # 滚动到底部
            self.chat_scrollable_frame._parent_canvas.update_idletasks()
            self.chat_scrollable_frame._parent_canvas.yview_moveto(1.0)
            
            logger.debug("已添加历史记录分割线")
            
        except Exception as e:
            logger.error(f"添加历史记录分割线时出错: {e}")