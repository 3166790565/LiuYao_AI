# -*- coding: utf-8 -*-

import tkinter as tk

import customtkinter as ctk

from config.ui_config import get_ui_settings
from utils.config_manager import config_manager
from utils.logger import setup_logger
from utils.ui_components import ThemeableWidget

# 设置日志记录器
logger = setup_logger(__name__)

# 自定义模型管理器已移除

class SettingsFrame(ThemeableWidget, ctk.CTkFrame):
    """设置界面框架"""
    
    def __init__(self, parent, **kwargs):
        ThemeableWidget.__init__(self)
        ctk.CTkFrame.__init__(self, parent, **kwargs)
        
        # 获取UI设置
        self.ui_settings = get_ui_settings()
        
        # 设置框架属性
        self.configure(
            fg_color=self.get_color("card_bg"),
            corner_radius=0
        )
        
        # 配置网格权重
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 创建界面组件
        self.create_widgets()
        
        # 应用主题
        self.update_theme()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建滚动框架
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.get_color("card_bg"),
            corner_radius=0
        )
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # 创建模型设置
        self.create_model_settings()
        
        # 创建RAG设置
        self.create_rag_settings()
        
        # 创建保存按钮
        self.create_save_button()
    
    def create_model_settings(self):
        """创建模型设置"""
        # 模型设置区域
        model_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.get_color("card_bg")
        )
        model_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        model_frame.grid_columnconfigure(1, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            model_frame,
            text="AI模型设置",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=16,
                weight="bold"
            )
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))
        
        # 默认模型选择
        model_label = ctk.CTkLabel(
            model_frame,
            text="默认模型:",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=14
            )
        )
        model_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # 获取可用模型列表
        from config.settings import SUPPORTED_MODELS, DEFAULT_MODEL
        
        # 默认模型下拉框
        self.default_model_var = tk.StringVar(value=config_manager.get('default_model', DEFAULT_MODEL))
        self.default_model_combobox = ctk.CTkComboBox(
            model_frame,
            values=SUPPORTED_MODELS,
            variable=self.default_model_var,
            state="readonly",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=12
            ),
            height=35,
            width=300
        )
        self.default_model_combobox.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # 说明文字
        desc_label = ctk.CTkLabel(
            model_frame,
            text="选择在起卦分析时默认使用的AI模型",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=12
            ),
            text_color=self.get_color("secondary_text")
        )
        desc_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15))
    
    def create_rag_settings(self):
        """创建RAG知识库配置设置"""
        # RAG配置设置区域
        rag_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.get_color("card_bg")
        )
        rag_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
        rag_frame.grid_columnconfigure(1, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            rag_frame,
            text="知识库检索配置",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=16,
                weight="bold"
            )
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))
        
        # 搜索结果数量设置
        result_count_label = ctk.CTkLabel(
            rag_frame,
            text="搜索结果数量:",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=14
            )
        )
        result_count_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # 搜索结果数量输入框
        self.rag_result_count_var = tk.StringVar(value=str(config_manager.get('rag_result_count', 3)))
        self.rag_result_count_entry = ctk.CTkEntry(
            rag_frame,
            textvariable=self.rag_result_count_var,
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=12
            ),
            height=35,
            width=100
        )
        self.rag_result_count_entry.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # 搜索结果数量说明
        result_count_desc = ctk.CTkLabel(
            rag_frame,
            text="若匹配数过大可能导致程序分析缓慢，最大为10",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=11
            ),
            text_color="#FF4444"  # 红色警告文字
        )
        result_count_desc.grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))
        
        # 匹配度阈值设置
        threshold_label = ctk.CTkLabel(
            rag_frame,
            text="匹配度阈值:",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=14
            )
        )
        threshold_label.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        
        # 匹配度阈值下拉框
        threshold_options = ["宽松的", "平衡的（推荐）", "严格的"]
        current_threshold = config_manager.get('rag_threshold', 0.5)
        
        # 根据当前阈值确定默认选项
        if current_threshold == 0.3:
            default_threshold = "宽松的"
        elif current_threshold == 0.7:
            default_threshold = "严格的"
        else:
            default_threshold = "平衡的（推荐）"
        
        self.rag_threshold_var = tk.StringVar(value=default_threshold)
        self.rag_threshold_combobox = ctk.CTkComboBox(
            rag_frame,
            values=threshold_options,
            variable=self.rag_threshold_var,
            state="readonly",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=12
            ),
            height=35,
            width=200
        )
        self.rag_threshold_combobox.grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
        # 匹配度阈值说明
        threshold_desc = ctk.CTkLabel(
            rag_frame,
            text="控制知识库搜索的匹配严格程度，推荐使用平衡模式",
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=12
            ),
            text_color=self.get_color("secondary_text")
        )
        threshold_desc.grid(row=4, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15))
        
        # 绑定输入验证
        self.rag_result_count_entry.bind('<KeyRelease>', self._validate_result_count)
        self.rag_result_count_entry.bind('<FocusOut>', self._validate_result_count)
    
    def _validate_result_count(self, event=None):
        """验证搜索结果数量输入"""
        try:
            value = self.rag_result_count_var.get().strip()
            if value:
                num = int(value)
                if num < 1:
                    self.rag_result_count_var.set("1")
                elif num > 10:
                    self.rag_result_count_var.set("10")
        except ValueError:
            # 如果输入不是数字，恢复为默认值
             self.rag_result_count_var.set("3")
    
    def create_save_button(self):
        """创建保存按钮"""
        # 保存按钮区域
        save_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="transparent"
        )
        save_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(20, 10))
        save_frame.grid_columnconfigure(0, weight=1)
        
        # 保存按钮
        save_btn = ctk.CTkButton(
            save_frame,
            text="保存设置",
            command=self.save_all_settings,
            width=120,
            height=40,
            font=ctk.CTkFont(
                family=self.ui_settings['font_family'],
                size=14,
                weight="bold"
            ),
            fg_color=self.get_color("primary_color"),
            hover_color=self.get_color("primary_alpha_20")
        )
        save_btn.grid(row=0, column=0, pady=10)
    
    def save_all_settings(self):
        """保存所有设置"""
        try:
            # 保存默认模型设置
            default_model = self.default_model_var.get()
            config_manager.set('default_model', default_model)
            
            # 保存RAG配置
            rag_saved = self.save_rag_settings()
            
            # 保存配置文件
            config_saved = config_manager.save_config()
            
            if rag_saved and config_saved:
                # 显示成功消息
                from utils.ui_components import IOSMessageBox
                IOSMessageBox.show_success(
                    self,
                    "保存成功",
                    "所有设置已成功保存！"
                )
                logger.info("所有设置已成功保存")
            else:
                # 显示错误消息
                from utils.ui_components import IOSMessageBox
                IOSMessageBox.show_error(
                    self,
                    "保存失败",
                    "保存设置时出现错误，请检查日志。"
                )
                logger.error("保存设置时出现错误")
                
        except Exception as e:
            logger.error(f"保存设置时出错: {e}")
            from utils.ui_components import IOSMessageBox
            IOSMessageBox.show_error(
                self,
                "保存失败",
                f"保存设置时出现错误: {str(e)}"
            )
    
    def save_rag_settings(self):
        """保存RAG配置设置"""
        try:
            # 保存搜索结果数量
            if hasattr(self, 'rag_result_count_var'):
                result_count = int(self.rag_result_count_var.get())
                config_manager.set('rag_result_count', result_count)
                logger.info(f"RAG搜索结果数量已设置为: {result_count}")
            
            # 保存匹配度阈值
            if hasattr(self, 'rag_threshold_var'):
                threshold_text = self.rag_threshold_var.get()
                # 将文本转换为数值
                if threshold_text == "宽松的":
                    threshold_value = 0.3
                elif threshold_text == "严格的":
                    threshold_value = 0.7
                else:  # 平衡的（推荐）
                    threshold_value = 0.5
                
                config_manager.set('rag_threshold', threshold_value)
                logger.info(f"RAG匹配度阈值已设置为: {threshold_value} ({threshold_text})")
            
            return True
        except Exception as e:
            logger.error(f"保存RAG配置时出错: {e}")
            return False
    
    def get_rag_result_count(self) -> int:
        """获取RAG搜索结果数量"""
        try:
            if hasattr(self, 'rag_result_count_var'):
                return int(self.rag_result_count_var.get())
            return config_manager.get('rag_result_count', 3)
        except Exception as e:
            logger.error(f"获取RAG搜索结果数量时出错: {e}")
            return 3
    
    def get_rag_threshold(self) -> float:
        """获取RAG匹配度阈值"""
        try:
            if hasattr(self, 'rag_threshold_var'):
                threshold_text = self.rag_threshold_var.get()
                if threshold_text == "宽松的":
                    return 0.3
                elif threshold_text == "严格的":
                    return 0.7
                else:  # 平衡的（推荐）
                    return 0.5
            return config_manager.get('rag_threshold', 0.5)
        except Exception as e:
            logger.error(f"获取RAG匹配度阈值时出错: {e}")
            return 0.5
    
    def update_theme(self):
        """更新主题"""
        try:
            # 调用父类的update_theme方法更新颜色配置
            super().update_theme()
            
            # 更新主框架颜色
            self.configure(fg_color=self.get_color("card_bg"))
            
            # 更新滚动框架颜色
            if hasattr(self, 'scroll_frame'):
                self.scroll_frame.configure(fg_color=self.get_color("card_bg"))
            
            # 递归更新所有子组件的主题
            self._update_child_themes(self)
            
            logger.info("SettingsFrame主题更新完成")
        except Exception as e:
            logger.error(f"更新SettingsFrame主题时出错: {e}")
    
    def _update_child_themes(self, widget):
        """递归更新子组件主题"""
        try:
            # 更新当前组件
            if hasattr(widget, 'configure'):
                # 更新CTkFrame组件
                if isinstance(widget, ctk.CTkFrame):
                    # 检查当前背景色是否为透明
                    try:
                        current_fg_color = widget.cget("fg_color")
                        # 只有当前背景色为透明时才不更新
                        if current_fg_color == "transparent":
                            # 透明背景保持不变
                            pass
                        else:
                            # 对于非透明背景的框架，都更新为主题背景色
                            widget.configure(fg_color=self.get_color("card_bg"))
                    except:
                        # 如果无法获取当前颜色，尝试更新为主题背景色
                        try:
                            widget.configure(fg_color=self.get_color("card_bg"))
                        except:
                            pass
                # 更新CTkLabel组件
                elif isinstance(widget, ctk.CTkLabel):
                    # 检查是否是标题标签（通过字体大小判断）
                    try:
                        font_obj = widget.cget("font")
                        if hasattr(font_obj, 'cget') and font_obj.cget("size") >= 16:
                            # 标题标签使用主文本色
                            widget.configure(text_color=self.get_color("text_color"))
                        else:
                            # 检查当前文本颜色，如果是次要文本色则保持，否则使用主文本色
                            try:
                                current_color = widget.cget("text_color")
                                # 如果当前是次要文本色，保持不变
                                if current_color == self.get_color("secondary_text"):
                                    widget.configure(text_color=self.get_color("secondary_text"))
                                else:
                                    # 否则使用主文本色
                                    widget.configure(text_color=self.get_color("text_color"))
                            except:
                                # 如果无法获取当前颜色，使用主文本色
                                widget.configure(text_color=self.get_color("text_color"))
                    except:
                        # 如果无法获取字体信息，默认使用主文本色
                        widget.configure(text_color=self.get_color("text_color"))
                # 更新CTkButton组件
                elif isinstance(widget, ctk.CTkButton):
                    # 检查按钮文本，跳过有特殊颜色需求的按钮
                    button_text = widget.cget("text") if hasattr(widget, 'cget') else ""
                    if button_text not in ["删除", "测试", "取消", "测试连接"]:
                        widget.configure(
                            fg_color=self.get_color("primary_color"),
                            text_color=self.get_color("text_color"),
                            hover_color=self.get_color("primary_alpha_20")
                        )
                # 更新CTkComboBox组件
                elif isinstance(widget, ctk.CTkComboBox):
                    widget.configure(
                        fg_color=self.get_color("card_bg"),
                        text_color=self.get_color("text_color"),
                        border_color=self.get_color("separator")
                    )
                # 更新CTkScrollableFrame组件
                elif isinstance(widget, ctk.CTkScrollableFrame):
                    widget.configure(
                        fg_color=self.get_color("card_bg"),
                        label_text_color=self.get_color("text_color")
                    )
                # 更新CTkEntry组件
                elif isinstance(widget, ctk.CTkEntry):
                    widget.configure(
                        fg_color=self.get_color("card_bg"),
                        text_color=self.get_color("text_color"),
                        border_color=self.get_color("separator")
                    )
                # 更新CTkTextbox组件
                elif isinstance(widget, ctk.CTkTextbox):
                    widget.configure(
                        fg_color=self.get_color("card_bg"),
                        text_color=self.get_color("text_color"),
                        border_color=self.get_color("separator")
                    )
            
            # 递归处理子组件
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    self._update_child_themes(child)
                    
        except Exception as e:
            logger.error(f"更新子组件主题时出错: {e}")
    
    def refresh_model_list(self):
        """刷新模型列表（自定义模型功能已移除，仅更新内置模型）"""
        try:
            from config.settings import SUPPORTED_MODELS
            
            # 获取内置模型列表
            model_list = list(SUPPORTED_MODELS)
            
            # 更新默认模型下拉框
            if hasattr(self, 'default_model_var'):
                current_value = self.default_model_var.get()
                self.default_model_combobox.configure(values=model_list)
                
                # 如果当前选择的模型还在列表中，保持选择
                if current_value in model_list:
                    self.default_model_var.set(current_value)
                elif model_list:
                    self.default_model_var.set(model_list[0])
                    
            logger.info("模型列表已刷新")
        except Exception as e:
            logger.error(f"刷新模型列表时出错: {e}")
    
    def get_default_model(self):
        """获取默认模型"""
        try:
            if hasattr(self, 'default_model_var'):
                return self.default_model_var.get()
            else:
                from config.settings import DEFAULT_MODEL
                return DEFAULT_MODEL
        except Exception as e:
            logger.error(f"获取默认模型时出错: {e}")
            from config.settings import DEFAULT_MODEL
            return DEFAULT_MODEL
    
    def set_default_model(self, model):
        """设置默认模型"""
        try:
            if hasattr(self, 'default_model_var'):
                self.default_model_var.set(model)
                # 同时更新配置
                config_manager.set('default_model', model)
                logger.info(f"默认模型已设置为: {model}")
            else:
                logger.warning("默认模型变量未初始化")
        except Exception as e:
            logger.error(f"设置默认模型时出错: {e}")