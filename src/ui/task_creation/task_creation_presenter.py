"""任务创建展示器模块..

实现任务创建界面的展示器逻辑。
"""

from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os

from .task_creation_model import TaskCreationModel, TaskTemplate
from .task_creation_view import TaskCreationView
from ...core.enhanced_task_executor import TaskConfig, TaskExecutor


class TaskCreationPresenter(QObject):
    """任务创建控制器。"""
    
    # 信号定义
    taskCreated = pyqtSignal(object)  # TaskConfig
    taskUpdated = pyqtSignal(object)  # TaskConfig
    templateLoaded = pyqtSignal(str)  # 模板名称
    templateSaved = pyqtSignal(str)  # 文件路径
    errorOccurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, view: TaskCreationView, model: TaskCreationModel, 
                 task_executor: TaskExecutor = None, parent=None):
        """初始化任务创建控制器。
        
        Args:
            view: 任务创建视图
            model: 任务创建模型
            task_executor: 任务执行器
            parent: 父对象
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.task_executor = task_executor
        self.current_task_config = None
        self.edit_mode = False
        
        self._connect_signals()
        self._setup_initial_data()
        
    def _connect_signals(self):
        """连接信号和槽。"""
        # 视图信号
        self.view.taskCreated.connect(self._handle_task_creation)
        self.view.taskSaved.connect(self._handle_task_save)
        self.view.templateLoaded.connect(self._handle_template_load)
        self.view.templateSaved.connect(self._handle_template_save)
        self.view.formValidated.connect(self._handle_form_validation)
        
        # 模型信号
        self.model.templateLoaded.connect(self._on_template_loaded)
        self.model.templateSaved.connect(self._on_template_saved)
        self.model.taskValidated.connect(self._on_task_validated)
        
    def _setup_initial_data(self):
        """设置初始数据。"""
        # 设置任务类型选项
        task_types = self.model.get_task_type_options()
        self.view.set_task_type_options(task_types)
        
        # 设置优先级选项
        priorities = self.model.get_priority_options()
        self.view.set_priority_options(priorities)
        
        # 加载可用模板
        self._load_available_templates()
        
        # 设置默认值
        self._load_default_template()
        
    def _load_available_templates(self):
        """加载可用模板列表。"""
        try:
            templates = self.model.get_available_templates()
            template_names = []
            
            for template_path in templates:
                template_name = os.path.splitext(os.path.basename(template_path))[0]
                template_names.append((template_name, template_path))
                
            self.view.set_available_templates(template_names)
            
        except Exception as e:
            self.errorOccurred.emit(f"加载模板列表失败: {e}")
            
    def _load_default_template(self):
        """加载默认模板。"""
        try:
            default_template = self.model.get_default_template()
            self._apply_template_to_view(default_template)
            
        except Exception as e:
            self.errorOccurred.emit(f"加载默认模板失败: {e}")
            
    def _apply_template_to_view(self, template: TaskTemplate):
        """将模板应用到视图。
        
        Args:
            template: 任务模板
        """
        try:
            # 设置基本信息
            self.view.set_task_name(template.name)
            self.view.set_task_description(template.description)
            self.view.set_task_type(template.task_type.value)
            self.view.set_task_priority(template.priority.value)
            
            # 设置高级选项
            self.view.set_retry_count(template.retry_count)
            self.view.set_timeout(template.timeout)
            self.view.set_max_concurrent(template.max_concurrent)
            
            # 设置依赖和参数
            dependencies_str = ', '.join(template.dependencies)
            self.view.set_dependencies(dependencies_str)
            
            # 设置参数（转换为JSON字符串）
            import json
            parameters_str = json.dumps(template.parameters, ensure_ascii=False, indent=2) if template.parameters else '{}'
            self.view.set_parameters(parameters_str)
            
            # 设置标签
            tags_str = ', '.join(template.tags)
            self.view.set_tags(tags_str)
            
            # 设置选项
            self.view.set_enabled(template.enabled)
            self.view.set_auto_retry(template.auto_retry)
            
        except Exception as e:
            self.errorOccurred.emit(f"应用模板失败: {e}")
            
    def _handle_task_creation(self, form_data: Dict[str, Any]):
        """处理任务创建。
        
        Args:
            form_data: 表单数据
        """
        try:
            # 创建任务配置
            task_config = self.model.create_task_config(form_data)
            if task_config is None:
                return
                
            # 如果有任务执行器，添加任务
            if self.task_executor:
                success = self.task_executor.add_task(task_config)
                if success:
                    self.taskCreated.emit(task_config)
                    self.view.show_success_message("任务创建成功")
                    self._reset_form()
                else:
                    self.errorOccurred.emit("添加任务到执行器失败")
            else:
                # 没有执行器时，只发送信号
                self.taskCreated.emit(task_config)
                self.view.show_success_message("任务配置创建成功")
                
        except Exception as e:
            self.errorOccurred.emit(f"创建任务失败: {e}")
            
    def _handle_task_save(self, form_data: Dict[str, Any]):
        """处理任务保存。
        
        Args:
            form_data: 表单数据
        """
        try:
            if self.edit_mode and self.current_task_config:
                # 更新现有任务
                task_config = self.model.create_task_config(form_data)
                if task_config is None:
                    return
                    
                # 保持原有的任务ID
                task_config.task_id = self.current_task_config.task_id
                
                if self.task_executor:
                    success = self.task_executor.update_task(task_config)
                    if success:
                        self.taskUpdated.emit(task_config)
                        self.view.show_success_message("任务更新成功")
                    else:
                        self.errorOccurred.emit("更新任务失败")
                else:
                    self.taskUpdated.emit(task_config)
                    self.view.show_success_message("任务配置更新成功")
            else:
                # 创建新任务
                self._handle_task_creation(form_data)
                
        except Exception as e:
            self.errorOccurred.emit(f"保存任务失败: {e}")
            
    def _handle_template_load(self, template_path: str):
        """处理模板加载。
        
        Args:
            template_path: 模板文件路径
        """
        try:
            success = self.model.load_template(template_path)
            if not success:
                self.errorOccurred.emit("加载模板失败")
                
        except Exception as e:
            self.errorOccurred.emit(f"加载模板失败: {e}")
            
    def _handle_template_save(self, form_data: Dict[str, Any]):
        """处理模板保存。
        
        Args:
            form_data: 表单数据
        """
        try:
            # 弹出文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "保存任务模板",
                f"{form_data.get('name', '新模板')}.json",
                "JSON文件 (*.json)"
            )
            
            if file_path:
                success = self.model.save_template(form_data, file_path)
                if success:
                    self.view.show_success_message(f"模板已保存到: {file_path}")
                    self._load_available_templates()  # 刷新模板列表
                else:
                    self.errorOccurred.emit("保存模板失败")
                    
        except Exception as e:
            self.errorOccurred.emit(f"保存模板失败: {e}")
            
    def _handle_form_validation(self, form_data: Dict[str, Any]):
        """处理表单验证。
        
        Args:
            form_data: 表单数据
        """
        try:
            is_valid, error_msg = self.model.validate_task_data(form_data)
            self.view.set_validation_result(is_valid, error_msg)
            
        except Exception as e:
            self.view.set_validation_result(False, f"验证失败: {e}")
            
    def _on_template_loaded(self, template: TaskTemplate):
        """模板加载完成。
        
        Args:
            template: 加载的模板
        """
        self._apply_template_to_view(template)
        self.templateLoaded.emit(template.name)
        
    def _on_template_saved(self, file_path: str):
        """模板保存完成。
        
        Args:
            file_path: 保存的文件路径
        """
        self.templateSaved.emit(file_path)
        
    def _on_task_validated(self, is_valid: bool, error_msg: str):
        """任务验证完成。
        
        Args:
            is_valid: 是否有效
            error_msg: 错误信息
        """
        self.view.set_validation_result(is_valid, error_msg)
        
    def _reset_form(self):
        """重置表单。"""
        try:
            self._load_default_template()
            self.edit_mode = False
            self.current_task_config = None
            self.view.set_edit_mode(False)
            
        except Exception as e:
            self.errorOccurred.emit(f"重置表单失败: {e}")
            
    def load_task_for_edit(self, task_config: TaskConfig):
        """加载任务进行编辑。
        
        Args:
            task_config: 要编辑的任务配置
        """
        try:
            self.current_task_config = task_config
            self.edit_mode = True
            
            # 从任务配置创建模板并应用到视图
            template = self.model.create_template_from_config(task_config)
            self._apply_template_to_view(template)
            
            # 设置编辑模式
            self.view.set_edit_mode(True)
            
        except Exception as e:
            self.errorOccurred.emit(f"加载任务编辑失败: {e}")
            
    def create_new_task(self):
        """创建新任务。"""
        self._reset_form()
        
    def get_current_form_data(self) -> Dict[str, Any]:
        """获取当前表单数据。
        
        Returns:
            Dict[str, Any]: 表单数据
        """
        try:
            return self.view.get_form_data()
        except Exception as e:
            self.errorOccurred.emit(f"获取表单数据失败: {e}")
            return {}
            
    def validate_current_form(self) -> bool:
        """验证当前表单。
        
        Returns:
            bool: 是否有效
        """
        try:
            form_data = self.get_current_form_data()
            is_valid, _ = self.model.validate_task_data(form_data)
            return is_valid
        except Exception as e:
            self.errorOccurred.emit(f"验证表单失败: {e}")
            return False
            
    def set_task_executor(self, task_executor: TaskExecutor):
        """设置任务执行器。
        
        Args:
            task_executor: 任务执行器
        """
        self.task_executor = task_executor
        
    def refresh_templates(self):
        """刷新模板列表。"""
        self._load_available_templates()
        
    def cleanup(self):
        """清理资源。"""
        try:
            # 断开信号连接
            self.view.taskCreated.disconnect()
            self.view.taskSaved.disconnect()
            self.view.templateLoaded.disconnect()
            self.view.templateSaved.disconnect()
            self.view.formValidated.disconnect()
            
            self.model.templateLoaded.disconnect()
            self.model.templateSaved.disconnect()
            self.model.taskValidated.disconnect()
            
        except Exception as e:
            print(f"清理任务创建控制器资源失败: {e}")
