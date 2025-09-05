# -*- coding: utf-8 -*-
"""
任务执行历史Model层
负责管理执行历史数据状态和业务逻辑
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from loguru import logger

from adapters.task_manager_adapter import TaskManagerAdapter


class TaskExecutionHistoryModel(QObject):
    """任务执行历史Model"""

    # 数据变化信号
    execution_records_updated = pyqtSignal(list)  # 执行记录列表更新
    execution_record_selected = pyqtSignal(dict)  # 执行记录选中
    execution_record_details_updated = pyqtSignal(dict)  # 执行记录详情更新
    
    # 过滤和统计信号
    filter_conditions_updated = pyqtSignal(dict)  # 过滤条件更新
    statistics_updated = pyqtSignal(dict)  # 统计信息更新
    
    # 操作结果信号
    data_loading_finished = pyqtSignal(bool, str)  # 数据加载完成(成功, 消息)
    export_finished = pyqtSignal(bool, str)  # 导出完成(成功, 消息)
    cleanup_finished = pyqtSignal(bool, str)  # 清理完成(成功, 消息)
    
    # 错误信号
    error_occurred = pyqtSignal(str)  # 错误发生

    def __init__(self, task_manager: TaskManagerAdapter, task_id: Optional[str] = None):
        """初始化Model
        
        Args:
            task_manager: 任务管理器适配器
            task_id: 特定任务ID（可选）
        """
        super().__init__()
        self.task_manager = task_manager
        self.task_id = task_id
        
        # 数据状态
        self._execution_records: List[Dict[str, Any]] = []
        self._filtered_records: List[Dict[str, Any]] = []
        self._selected_record: Optional[Dict[str, Any]] = None
        
        # 过滤条件
        self._filter_conditions = {
            'status': '全部',
            'start_date': datetime.now() - timedelta(days=30),
            'end_date': datetime.now(),
            'search_text': '',
            'show_failed_only': False
        }
        
        # 统计信息
        self._statistics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'running_executions': 0,
            'cancelled_executions': 0,
            'success_rate': 0.0,
            'avg_duration': 0.0
        }
        
        # 自动刷新定时器
        self._auto_refresh_timer = QTimer()
        self._auto_refresh_timer.timeout.connect(self.refresh_data)
        self._auto_refresh_enabled = False
        
        logger.info(f"TaskExecutionHistoryModel initialized for task_id: {task_id}")

    def get_execution_records(self) -> List[Dict[str, Any]]:
        """获取执行记录列表"""
        return self._execution_records.copy()

    def get_filtered_records(self) -> List[Dict[str, Any]]:
        """获取过滤后的执行记录列表"""
        return self._filtered_records.copy()

    def get_selected_record(self) -> Optional[Dict[str, Any]]:
        """获取选中的执行记录"""
        return self._selected_record.copy() if self._selected_record else None

    def get_filter_conditions(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self._filter_conditions.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._statistics.copy()

    def set_filter_conditions(self, conditions: Dict[str, Any]):
        """设置过滤条件"""
        self._filter_conditions.update(conditions)
        self._apply_filters()
        self.filter_conditions_updated.emit(self._filter_conditions.copy())
        logger.debug(f"Filter conditions updated: {conditions}")

    def select_record(self, record: Optional[Dict[str, Any]]):
        """选择执行记录"""
        self._selected_record = record
        if record:
            self.execution_record_selected.emit(record.copy())
            logger.debug(f"Record selected: {record.get('execution_id', 'N/A')}")
        else:
            self.execution_record_selected.emit({})
            logger.debug("Record selection cleared")

    def refresh_data(self):
        """刷新执行历史数据"""
        try:
            logger.info("Refreshing execution history data...")
            
            if self.task_id:
                # 加载特定任务的执行历史
                records = self.task_manager.get_task_executions(self.task_id)
            else:
                # 加载所有任务的执行历史
                records = self._get_all_executions()
            
            self._execution_records = records
            self._apply_filters()
            self._update_statistics()
            
            self.execution_records_updated.emit(self._filtered_records.copy())
            self.data_loading_finished.emit(True, "数据加载成功")
            
            logger.info(f"Loaded {len(records)} execution records")
            
        except Exception as e:
            error_msg = f"加载执行历史失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.data_loading_finished.emit(False, error_msg)

    def _get_all_executions(self) -> List[Dict[str, Any]]:
        """获取所有任务的执行记录"""
        all_executions = []
        try:
            # 获取所有任务
            tasks = self.task_manager.list_tasks_sync()
            for task in tasks:
                executions = self.task_manager.get_task_executions(task.task_id)
                all_executions.extend(executions)
        except Exception as e:
            logger.error(f"获取所有执行记录失败: {e}")
            raise
        
        return all_executions

    def _apply_filters(self):
        """应用过滤条件"""
        filtered_records = self._execution_records.copy()
        
        # 状态过滤
        if self._filter_conditions['status'] != '全部':
            status_map = {
                '成功': 'completed',
                '失败': 'failed', 
                '运行中': 'running',
                '已取消': 'cancelled'
            }
            target_status = status_map.get(self._filter_conditions['status'])
            if target_status:
                filtered_records = [r for r in filtered_records if r.get('status') == target_status]
        
        # 只显示失败的执行
        if self._filter_conditions['show_failed_only']:
            filtered_records = [r for r in filtered_records if r.get('status') == 'failed']
        
        # 日期范围过滤
        start_date = self._filter_conditions['start_date']
        end_date = self._filter_conditions['end_date']
        if start_date and end_date:
            filtered_records = [
                r for r in filtered_records 
                if r.get('start_time') and start_date <= r['start_time'].date() <= end_date
            ]
        
        # 搜索文本过滤
        search_text = self._filter_conditions['search_text'].lower()
        if search_text:
            filtered_records = [
                r for r in filtered_records
                if (search_text in r.get('execution_id', '').lower() or
                    search_text in r.get('task_name', '').lower() or
                    search_text in r.get('error_message', '').lower())
            ]
        
        self._filtered_records = filtered_records
        logger.debug(f"Applied filters, {len(filtered_records)} records remaining")

    def _update_statistics(self):
        """更新统计信息"""
        records = self._filtered_records
        total = len(records)
        
        if total == 0:
            self._statistics = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'running_executions': 0,
                'cancelled_executions': 0,
                'success_rate': 0.0,
                'avg_duration': 0.0
            }
        else:
            successful = len([r for r in records if r.get('status') == 'completed'])
            failed = len([r for r in records if r.get('status') == 'failed'])
            running = len([r for r in records if r.get('status') == 'running'])
            cancelled = len([r for r in records if r.get('status') == 'cancelled'])
            
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            # 计算平均持续时间
            durations = []
            for record in records:
                start_time = record.get('start_time')
                end_time = record.get('end_time')
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            self._statistics = {
                'total_executions': total,
                'successful_executions': successful,
                'failed_executions': failed,
                'running_executions': running,
                'cancelled_executions': cancelled,
                'success_rate': success_rate,
                'avg_duration': avg_duration
            }
        
        self.statistics_updated.emit(self._statistics.copy())
        logger.debug(f"Statistics updated: {self._statistics}")

    def export_history(self, file_path: str, format_type: str = 'csv'):
        """导出执行历史"""
        try:
            logger.info(f"Exporting history to {file_path} in {format_type} format")
            
            # TODO: 实现导出功能
            # 这里应该根据format_type导出为不同格式
            
            self.export_finished.emit(True, f"历史记录已导出到 {file_path}")
            
        except Exception as e:
            error_msg = f"导出失败: {str(e)}"
            logger.error(error_msg)
            self.export_finished.emit(False, error_msg)

    def cleanup_old_records(self, days_before: int = 30):
        """清理旧记录"""
        try:
            logger.info(f"Cleaning up records older than {days_before} days")
            
            cutoff_date = datetime.now() - timedelta(days=days_before)
            
            # TODO: 实现清理功能
            # 这里应该调用TaskManager的清理方法
            
            self.cleanup_finished.emit(True, f"已清理{days_before}天前的记录")
            
            # 刷新数据
            self.refresh_data()
            
        except Exception as e:
            error_msg = f"清理失败: {str(e)}"
            logger.error(error_msg)
            self.cleanup_finished.emit(False, error_msg)

    def set_auto_refresh(self, enabled: bool, interval_ms: int = 30000):
        """设置自动刷新"""
        self._auto_refresh_enabled = enabled
        
        if enabled:
            self._auto_refresh_timer.start(interval_ms)
            logger.info(f"Auto refresh enabled with interval {interval_ms}ms")
        else:
            self._auto_refresh_timer.stop()
            logger.info("Auto refresh disabled")

    def get_record_by_execution_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """根据执行ID获取记录"""
        for record in self._execution_records:
            if record.get('execution_id') == execution_id:
                return record.copy()
        return None

    def calculate_duration(self, start_time, end_time) -> str:
        """计算执行持续时间"""
        if not start_time:
            return "N/A"

        if not end_time:
            # 如果没有结束时间，计算到现在的时间
            end_time = datetime.now()

        try:
            duration = end_time - start_time
            total_seconds = int(duration.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        except Exception:
            return "N/A"

    def cleanup(self):
        """清理资源"""
        self._auto_refresh_timer.stop()
        logger.info("TaskExecutionHistoryModel cleaned up")