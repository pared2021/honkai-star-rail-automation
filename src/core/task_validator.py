# -*- coding: utf-8 -*-
"""
任务验证器 - 负责验证任务配置的正确性和完整性
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from .task_manager import TaskConfig
from .enums import TaskType, TaskPriority, ActionType


class ValidationLevel(Enum):
    """验证级别枚举"""
    ERROR = "error"  # 错误，必须修复
    WARNING = "warning"  # 警告，建议修复
    INFO = "info"  # 信息，可选修复


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    level: ValidationLevel
    field: str
    message: str
    suggestion: Optional[str] = None


class TaskValidator:
    """任务验证器类"""
    
    def __init__(self):
        """初始化验证器"""
        # 任务名称规则
        self.task_name_pattern = re.compile(r'^[\u4e00-\u9fa5a-zA-Z0-9_\-\s]{1,50}$')
        
        # 时间格式规则
        self.time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        # 有效的星期
        self.valid_weekdays = {
            'monday', 'tuesday', 'wednesday', 'thursday', 
            'friday', 'saturday', 'sunday'
        }
        
        # 操作参数验证规则
        self.action_param_rules = {
            ActionType.CLICK: ['x', 'y'],
            ActionType.KEY_PRESS: ['key'],
            ActionType.WAIT: ['duration'],
            ActionType.SCREENSHOT: ['path'],
            ActionType.CUSTOM: ['action_name']
        }
        
        logger.info("任务验证器初始化完成")
    
    def validate_task_config(self, config: TaskConfig) -> List[ValidationResult]:
        """验证任务配置
        
        Args:
            config: 任务配置
            
        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []
        
        # 验证基本信息
        results.extend(self._validate_basic_info(config))
        
        # 验证执行配置
        results.extend(self._validate_execution_config(config))
        
        # 验证调度配置
        results.extend(self._validate_schedule_config(config))
        
        # 验证操作序列
        results.extend(self._validate_actions(config))
        
        # 验证自定义参数
        results.extend(self._validate_custom_params(config))
        
        return results
    
    def _validate_basic_info(self, config: TaskConfig) -> List[ValidationResult]:
        """验证基本信息"""
        results = []
        
        # 验证任务名称
        if not config.task_name:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="task_name",
                message="任务名称不能为空",
                suggestion="请输入有效的任务名称"
            ))
        elif not self.task_name_pattern.match(config.task_name):
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="task_name",
                message="任务名称格式不正确",
                suggestion="任务名称只能包含中文、英文、数字、下划线、连字符和空格，长度1-50字符"
            ))
        
        # 验证任务类型
        if not isinstance(config.task_type, TaskType):
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="task_type",
                message="任务类型无效",
                suggestion=f"请选择有效的任务类型: {', '.join([t.value for t in TaskType])}"
            ))
        
        # 验证优先级
        if not isinstance(config.priority, TaskPriority):
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="priority",
                message="任务优先级无效",
                suggestion=f"请选择有效的优先级: {', '.join([p.value for p in TaskPriority])}"
            ))
        
        # 验证描述长度
        if len(config.description) > 500:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field="description",
                message="任务描述过长",
                suggestion="建议将描述控制在500字符以内"
            ))
        
        return results
    
    def _validate_execution_config(self, config: TaskConfig) -> List[ValidationResult]:
        """验证执行配置"""
        results = []
        
        # 验证重试次数
        if config.max_retry_count < 0:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="max_retry_count",
                message="重试次数不能为负数",
                suggestion="请设置0或正整数"
            ))
        elif config.max_retry_count > 10:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field="max_retry_count",
                message="重试次数过多",
                suggestion="建议将重试次数控制在10次以内"
            ))
        
        # 验证超时时间
        if config.timeout_seconds <= 0:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field="timeout_seconds",
                message="超时时间必须大于0",
                suggestion="请设置合理的超时时间（秒）"
            ))
        elif config.timeout_seconds > 3600:  # 1小时
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field="timeout_seconds",
                message="超时时间过长",
                suggestion="建议将超时时间控制在1小时以内"
            ))
        
        return results
    
    def _validate_schedule_config(self, config: TaskConfig) -> List[ValidationResult]:
        """验证调度配置"""
        results = []
        
        if config.schedule_enabled:
            # 验证调度时间
            if not config.schedule_time:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field="schedule_time",
                    message="启用调度时必须设置调度时间",
                    suggestion="请设置HH:MM格式的时间"
                ))
            elif not self.time_pattern.match(config.schedule_time):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field="schedule_time",
                    message="调度时间格式不正确",
                    suggestion="请使用HH:MM格式，如：09:30"
                ))
            
            # 验证调度日期
            if not config.schedule_days:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field="schedule_days",
                    message="未设置调度日期",
                    suggestion="建议设置具体的调度日期"
                ))
            else:
                invalid_days = [day for day in config.schedule_days if day.lower() not in self.valid_weekdays]
                if invalid_days:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        field="schedule_days",
                        message=f"无效的调度日期: {', '.join(invalid_days)}",
                        suggestion=f"请使用有效的星期名称: {', '.join(self.valid_weekdays)}"
                    ))
        
        return results
    
    def _validate_actions(self, config: TaskConfig) -> List[ValidationResult]:
        """验证操作序列"""
        results = []
        
        if not config.actions:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field="actions",
                message="任务没有定义操作序列",
                suggestion="请添加至少一个操作"
            ))
            return results
        
        for i, action_data in enumerate(config.actions):
            action_results = self._validate_single_action(action_data, i)
            results.extend(action_results)
        
        return results
    
    def _validate_single_action(self, action_data: Dict[str, Any], index: int) -> List[ValidationResult]:
        """验证单个操作"""
        results = []
        field_prefix = f"actions[{index}]"
        
        # 验证操作类型
        if 'action_type' not in action_data:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field=f"{field_prefix}.action_type",
                message="操作类型缺失",
                suggestion="请指定操作类型"
            ))
            return results
        
        try:
            action_type = ActionType(action_data['action_type'])
        except ValueError:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field=f"{field_prefix}.action_type",
                message=f"无效的操作类型: {action_data['action_type']}",
                suggestion=f"请使用有效的操作类型: {', '.join([t.value for t in ActionType])}"
            ))
            return results
        
        # 验证操作参数
        params = action_data.get('params', {})
        required_params = self.action_param_rules.get(action_type, [])
        
        # 检查必需参数
        for param in required_params:
            if param not in params:
                # 对于坐标类操作，可以使用template替代x,y
                if param in ['x', 'y'] and 'template' in params:
                    continue
                if param == 'template' and 'x' in params and 'y' in params:
                    continue
                
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.{param}",
                    message=f"缺少必需参数: {param}",
                    suggestion=f"请为{action_type.value}操作提供{param}参数"
                ))
        
        # 验证具体参数值
        results.extend(self._validate_action_params(action_type, params, field_prefix))
        
        return results
    
    def _validate_action_params(self, action_type: ActionType, params: Dict[str, Any], field_prefix: str) -> List[ValidationResult]:
        """验证操作参数值"""
        results = []
        
        # 验证坐标参数
        for coord in ['x', 'y', 'start_x', 'start_y', 'end_x', 'end_y']:
            if coord in params:
                if not isinstance(params[coord], (int, float)) or params[coord] < 0:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        field=f"{field_prefix}.params.{coord}",
                        message=f"坐标{coord}必须是非负数",
                        suggestion="请提供有效的屏幕坐标"
                    ))
        
        # 验证等待时间
        if 'duration' in params:
            if not isinstance(params['duration'], (int, float)) or params['duration'] <= 0:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.duration",
                    message="等待时间必须是正数",
                    suggestion="请设置合理的等待时间（秒）"
                ))
            elif params['duration'] > 60:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field=f"{field_prefix}.params.duration",
                    message="等待时间过长",
                    suggestion="建议将等待时间控制在60秒以内"
                ))
        
        # 验证超时时间
        if 'timeout' in params:
            if not isinstance(params['timeout'], (int, float)) or params['timeout'] <= 0:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.timeout",
                    message="超时时间必须是正数",
                    suggestion="请设置合理的超时时间（秒）"
                ))
        
        # 验证模板名称
        if 'template' in params:
            template_name = params['template']
            if not isinstance(template_name, str) or not template_name.strip():
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.template",
                    message="模板名称不能为空",
                    suggestion="请提供有效的模板名称"
                ))
        
        # 验证按键
        if 'key' in params:
            key = params['key']
            if not isinstance(key, str) or not key.strip():
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.key",
                    message="按键不能为空",
                    suggestion="请提供有效的按键名称"
                ))
        
        # 验证组合键
        if 'keys' in params:
            keys = params['keys']
            if not isinstance(keys, list) or not keys:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.keys",
                    message="组合键必须是非空列表",
                    suggestion="请提供有效的按键组合"
                ))
        
        # 验证文本
        if 'text' in params:
            text = params['text']
            if not isinstance(text, str):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    field=f"{field_prefix}.params.text",
                    message="文本必须是字符串",
                    suggestion="请提供有效的文本内容"
                ))
        
        return results
    
    def _validate_custom_params(self, config: TaskConfig) -> List[ValidationResult]:
        """验证自定义参数"""
        results = []
        
        if config.custom_params:
            # 检查参数名称
            for key in config.custom_params.keys():
                if not isinstance(key, str) or not key.strip():
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        field=f"custom_params.{key}",
                        message="自定义参数名称不能为空",
                        suggestion="请使用有效的参数名称"
                    ))
        
        return results
    
    def is_config_valid(self, config: TaskConfig) -> Tuple[bool, List[ValidationResult]]:
        """检查配置是否有效
        
        Args:
            config: 任务配置
            
        Returns:
            Tuple[bool, List[ValidationResult]]: (是否有效, 验证结果列表)
        """
        results = self.validate_task_config(config)
        
        # 检查是否有错误级别的问题
        has_errors = any(result.level == ValidationLevel.ERROR for result in results)
        
        return not has_errors, results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """获取验证结果摘要
        
        Args:
            results: 验证结果列表
            
        Returns:
            Dict[str, Any]: 验证摘要
        """
        summary = {
            'total_issues': len(results),
            'errors': 0,
            'warnings': 0,
            'infos': 0,
            'is_valid': True,
            'issues_by_field': {}
        }
        
        for result in results:
            # 统计各级别问题数量
            if result.level == ValidationLevel.ERROR:
                summary['errors'] += 1
                summary['is_valid'] = False
            elif result.level == ValidationLevel.WARNING:
                summary['warnings'] += 1
            elif result.level == ValidationLevel.INFO:
                summary['infos'] += 1
            
            # 按字段分组
            field = result.field
            if field not in summary['issues_by_field']:
                summary['issues_by_field'][field] = []
            summary['issues_by_field'][field].append({
                'level': result.level.value,
                'message': result.message,
                'suggestion': result.suggestion
            })
        
        return summary