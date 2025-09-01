# -*- coding: utf-8 -*-
"""
自动化应用服务层
提供游戏检测和自动化操作的应用层业务逻辑
"""

import uuid
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from src.services.base_async_service import BaseAsyncService
from src.services.event_bus import EventBus, AutomationEvent, AutomationEventType
from src.automation.game_detector import GameDetector, GameWindow, DetectionResult
from src.automation.automation_controller import AutomationController, AutomationAction, ActionType, TaskResult
from src.models.task_models import TaskStatus
from src.core.logger import get_logger
from src.exceptions import AutomationError, ServiceError

logger = get_logger(__name__)


# ==================== 异常定义 ====================




# ==================== 请求数据类 ====================

@dataclass
class GameDetectionRequest:
    """游戏检测请求"""
    game_title: Optional[str] = None
    process_name: Optional[str] = None
    window_class: Optional[str] = None
    timeout_seconds: int = 30


@dataclass
class ScreenshotRequest:
    """截图请求"""
    region: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    save_path: Optional[str] = None
    format: str = "PNG"


@dataclass
class TemplateSearchRequest:
    """模板搜索请求"""
    template_name: str
    region: Optional[Tuple[int, int, int, int]] = None
    confidence: float = 0.8
    timeout_seconds: int = 10


@dataclass
class AutomationSequenceRequest:
    """自动化序列请求"""
    actions: List[Dict[str, Any]]
    task_name: str = "自动化任务"
    safe_mode: bool = True
    click_delay: float = 0.5
    random_delay: bool = True


# ==================== 响应数据类 ====================

@dataclass
class GameDetectionResponse:
    """游戏检测响应"""
    success: bool
    game_window: Optional[GameWindow] = None
    message: str = ""
    detection_time: float = 0.0


@dataclass
class ScreenshotResponse:
    """截图响应"""
    success: bool
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    message: str = ""
    capture_time: float = 0.0


@dataclass
class TemplateSearchResponse:
    """模板搜索响应"""
    success: bool
    found: bool = False
    location: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    message: str = ""
    search_time: float = 0.0


@dataclass
class AutomationExecutionResponse:
    """自动化执行响应"""
    success: bool
    task_id: Optional[str] = None
    result: Optional[TaskResult] = None
    message: str = ""
    execution_time: float = 0.0


# ==================== 主服务类 ====================

class AutomationApplicationService(BaseAsyncService):
    """自动化应用服务"""
    
    def __init__(
        self,
        game_detector: GameDetector,
        automation_controller: AutomationController,
        event_bus: EventBus
    ):
        from src.services.base_async_service import ServiceConfig
        
        # 创建服务配置
        config = ServiceConfig(
            name="AutomationApplicationService",
            version="1.0.0",
            description="自动化应用服务",
            auto_start=True
        )
        
        super().__init__(config)
        self.game_detector = game_detector
        self.automation_controller = automation_controller
        self.event_bus = event_bus
        self._initialized = False
        
        # 注册事件监听器
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        # 这里可以注册需要监听的事件
        pass
    
    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        
        try:
            logger.info("初始化AutomationApplicationService...")
            
            # 初始化游戏检测器
            # game_detector 通常不需要异步初始化
            
            # 初始化自动化控制器
            # automation_controller 通常不需要异步初始化
            
            self._initialized = True
            logger.info("AutomationApplicationService初始化完成")
            
        except Exception as e:
            logger.error(f"AutomationApplicationService初始化失败: {e}")
            raise ServiceError(f"初始化失败: {e}", original_error=e)
    
    async def close(self) -> None:
        """关闭服务"""
        if not self._initialized:
            return
        
        try:
            logger.info("关闭AutomationApplicationService...")
            
            # 停止所有正在运行的自动化任务
            if self.automation_controller.get_task_status() in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
                await self.stop_automation()
            
            self._initialized = False
            logger.info("AutomationApplicationService关闭完成")
            
        except Exception as e:
            logger.error(f"AutomationApplicationService关闭失败: {e}")
            raise ServiceError(f"关闭失败: {e}", original_error=e)
    
    # ==================== 游戏检测操作 ====================
    
    async def detect_game_window(self, request: GameDetectionRequest) -> GameDetectionResponse:
        """
        检测游戏窗口
        
        Args:
            request: 游戏检测请求
            
        Returns:
            GameDetectionResponse: 检测结果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"开始检测游戏窗口: {request.game_title or request.process_name}")
            
            # 查找游戏窗口
            game_windows = self.game_detector.find_game_windows(
                title=request.game_title,
                process_name=request.process_name,
                window_class=request.window_class
            )
            
            if not game_windows:
                return GameDetectionResponse(
                    success=False,
                    message="未找到游戏窗口",
                    detection_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 选择第一个找到的窗口
            game_window = game_windows[0]
            
            # 发布游戏检测事件
            event = AutomationEvent(
                event_type=AutomationEventType.GAME_DETECTED,
                automation_id=str(uuid.uuid4()),
                data={"game_window": game_window}
            )
            await self.event_bus.publish(event)
            
            logger.info(f"成功检测到游戏窗口: {game_window.title}")
            
            return GameDetectionResponse(
                success=True,
                game_window=game_window,
                message=f"成功检测到游戏窗口: {game_window.title}",
                detection_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"游戏窗口检测失败: {e}")
            return GameDetectionResponse(
                success=False,
                message=f"检测失败: {str(e)}",
                detection_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def is_game_running(self, game_title: str = None, process_name: str = None) -> bool:
        """
        检查游戏是否正在运行
        
        Args:
            game_title: 游戏窗口标题
            process_name: 进程名称
            
        Returns:
            bool: 游戏是否正在运行
        """
        try:
            return self.game_detector.is_game_running(title=game_title, process_name=process_name)
        except Exception as e:
            logger.error(f"检查游戏运行状态失败: {e}")
            return False
    
    async def activate_game_window(self) -> bool:
        """
        激活游戏窗口
        
        Returns:
            bool: 是否成功激活
        """
        try:
            return self.game_detector.activate_game_window()
        except Exception as e:
            logger.error(f"激活游戏窗口失败: {e}")
            return False
    
    async def is_game_detected(self) -> bool:
        """
        检查是否检测到游戏
        
        Returns:
            bool: 是否检测到游戏
        """
        try:
            return self.game_detector.is_game_detected()
        except Exception as e:
            logger.error(f"检查游戏检测状态失败: {e}")
            return False
    
    async def get_game_info(self) -> Dict[str, Any]:
        """
        获取游戏信息
        
        Returns:
            Dict: 游戏信息
        """
        try:
            game_window = self.game_detector.get_current_game_window()
            if game_window:
                return {
                    'window_title': game_window.title,
                    'process_name': game_window.process_name,
                    'window_handle': game_window.handle
                }
            return {}
        except Exception as e:
            logger.error(f"获取游戏信息失败: {e}")
            return {}
    
    async def is_automation_running(self) -> bool:
        """
        检查自动化是否正在运行
        
        Returns:
            bool: 自动化是否正在运行
        """
        try:
            return self.automation_controller.is_running
        except Exception as e:
            logger.error(f"检查自动化运行状态失败: {e}")
            return False
    
    async def get_last_run_time(self) -> Optional[datetime]:
        """
        获取最后运行时间
        
        Returns:
            Optional[datetime]: 最后运行时间
        """
        try:
            return self.automation_controller.get_last_run_time()
        except Exception as e:
            logger.error(f"获取最后运行时间失败: {e}")
            return None
    
    # ==================== 截图操作 ====================
    
    async def capture_screenshot(self, request: ScreenshotRequest) -> ScreenshotResponse:
        """
        截取屏幕截图
        
        Args:
            request: 截图请求
            
        Returns:
            ScreenshotResponse: 截图结果
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"开始截图: region={request.region}")
            
            # 截取屏幕
            screenshot = self.game_detector.capture_screen(region=request.region)
            
            if screenshot is None:
                return ScreenshotResponse(
                    success=False,
                    message="截图失败",
                    capture_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 保存截图
            image_path = None
            image_data = None
            
            if request.save_path:
                screenshot.save(request.save_path, request.format)
                image_path = request.save_path
            else:
                # 转换为字节数据
                import io
                img_buffer = io.BytesIO()
                screenshot.save(img_buffer, format=request.format)
                image_data = img_buffer.getvalue()
            
            logger.debug("截图完成")
            
            return ScreenshotResponse(
                success=True,
                image_path=image_path,
                image_data=image_data,
                message="截图成功",
                capture_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ScreenshotResponse(
                success=False,
                message=f"截图失败: {str(e)}",
                capture_time=(datetime.now() - start_time).total_seconds()
            )
    
    # ==================== 模板搜索操作 ====================
    
    async def find_template(self, request: TemplateSearchRequest) -> TemplateSearchResponse:
        """
        查找模板
        
        Args:
            request: 模板搜索请求
            
        Returns:
            TemplateSearchResponse: 搜索结果
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"开始查找模板: {request.template_name}")
            
            # 查找模板
            result = self.game_detector.find_template(
                template_name=request.template_name,
                region=request.region,
                confidence=request.confidence
            )
            
            logger.debug(f"模板查找完成: found={result.found}, confidence={result.confidence}")
            
            return TemplateSearchResponse(
                success=True,
                found=result.found,
                location=result.location,
                confidence=result.confidence,
                message="查找完成" if result.found else "未找到模板",
                search_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"模板查找失败: {e}")
            return TemplateSearchResponse(
                success=False,
                found=False,
                message=f"查找失败: {str(e)}",
                search_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def wait_for_template(self, request: TemplateSearchRequest) -> TemplateSearchResponse:
        """
        等待模板出现
        
        Args:
            request: 模板搜索请求
            
        Returns:
            TemplateSearchResponse: 搜索结果
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"开始等待模板: {request.template_name}")
            
            # 等待模板出现
            result = self.game_detector.wait_for_template(
                template_name=request.template_name,
                timeout=request.timeout_seconds,
                region=request.region,
                confidence=request.confidence
            )
            
            logger.debug(f"模板等待完成: found={result.found}")
            
            return TemplateSearchResponse(
                success=True,
                found=result.found,
                location=result.location,
                confidence=result.confidence,
                message="找到模板" if result.found else "等待超时",
                search_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"等待模板失败: {e}")
            return TemplateSearchResponse(
                success=False,
                found=False,
                message=f"等待失败: {str(e)}",
                search_time=(datetime.now() - start_time).total_seconds()
            )
    
    # ==================== 自动化操作 ====================
    
    async def execute_automation_sequence(self, request: AutomationSequenceRequest) -> AutomationExecutionResponse:
        """
        执行自动化操作序列
        
        Args:
            request: 自动化序列请求
            
        Returns:
            AutomationExecutionResponse: 执行结果
        """
        start_time = datetime.now()
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"开始执行自动化序列: {request.task_name}")
            
            # 配置自动化控制器
            self.automation_controller.click_delay = request.click_delay
            self.automation_controller.random_delay = request.random_delay
            self.automation_controller.safe_mode = request.safe_mode
            
            # 创建自动化操作
            actions = []
            for action_data in request.actions:
                action = AutomationAction(
                    action_type=ActionType(action_data['action_type']),
                    params=action_data.get('params', {}),
                    description=action_data.get('description', ''),
                    retry_count=action_data.get('retry_count', 3),
                    timeout=action_data.get('timeout', 10.0)
                )
                actions.append(action)
            
            # 发布自动化开始事件
            start_event = AutomationEvent(
                event_type=AutomationEventType.AUTOMATION_STARTED,
                automation_id=task_id,
                task_name=request.task_name,
                data={"task_name": request.task_name}
            )
            await self.event_bus.publish(start_event)
            
            # 启动自动化任务
            success = self.automation_controller.start_task(task_id, actions)
            
            if not success:
                return AutomationExecutionResponse(
                    success=False,
                    task_id=task_id,
                    message="启动自动化任务失败",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 等待任务完成
            while self.automation_controller.get_task_status() in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
                await asyncio.sleep(0.1)
            
            # 获取执行结果
            stats = self.automation_controller.get_stats()
            task_status = self.automation_controller.get_task_status()
            
            # 创建任务结果
            result = TaskResult(
                success=task_status == TaskStatus.COMPLETED,
                message=f"任务{task_status.value}",
                execution_time=(datetime.now() - start_time).total_seconds(),
                actions_completed=stats['stats'].get('actions_executed', 0),
                actions_failed=stats['stats'].get('actions_failed', 0)
            )
            
            # 发布自动化完成事件
            complete_event = AutomationEvent(
                event_type=AutomationEventType.AUTOMATION_COMPLETED,
                automation_id=task_id,
                data={"result": result}
            )
            await self.event_bus.publish(complete_event)
            
            logger.info(f"自动化序列执行完成: {result.message}")
            
            return AutomationExecutionResponse(
                success=result.success,
                task_id=task_id,
                result=result,
                message=result.message,
                execution_time=result.execution_time
            )
            
        except Exception as e:
            logger.error(f"自动化序列执行失败: {e}")
            return AutomationExecutionResponse(
                success=False,
                task_id=task_id,
                message=f"执行失败: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def stop_automation(self) -> bool:
        """
        停止当前自动化任务
        
        Returns:
            bool: 是否成功停止
        """
        try:
            logger.info("停止自动化任务")
            return self.automation_controller.stop_task()
        except Exception as e:
            logger.error(f"停止自动化任务失败: {e}")
            return False
    
    async def pause_automation(self) -> bool:
        """
        暂停当前自动化任务
        
        Returns:
            bool: 是否成功暂停
        """
        try:
            logger.info("暂停自动化任务")
            return self.automation_controller.pause_task()
        except Exception as e:
            logger.error(f"暂停自动化任务失败: {e}")
            return False
    
    async def resume_automation(self) -> bool:
        """
        恢复当前自动化任务
        
        Returns:
            bool: 是否成功恢复
        """
        try:
            logger.info("恢复自动化任务")
            return self.automation_controller.resume_task()
        except Exception as e:
            logger.error(f"恢复自动化任务失败: {e}")
            return False
    
    # ==================== 便捷操作方法 ====================
    
    async def click_at_position(self, x: int, y: int) -> bool:
        """
        在指定位置点击
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 是否成功
        """
        try:
            action = AutomationAction(
                action_type=ActionType.CLICK,
                params={'x': x, 'y': y},
                description=f"点击位置({x}, {y})"
            )
            
            request = AutomationSequenceRequest(
                actions=[{
                    'action_type': action.action_type.value,
                    'params': action.params,
                    'description': action.description
                }],
                task_name="单次点击"
            )
            
            response = await self.execute_automation_sequence(request)
            return response.success
            
        except Exception as e:
            logger.error(f"点击操作失败: {e}")
            return False
    
    async def click_template(self, template_name: str, region: Tuple[int, int, int, int] = None) -> bool:
        """
        点击模板
        
        Args:
            template_name: 模板名称
            region: 搜索区域
            
        Returns:
            bool: 是否成功
        """
        try:
            action = AutomationAction(
                action_type=ActionType.CLICK,
                params={'template': template_name, 'region': region},
                description=f"点击模板: {template_name}"
            )
            
            request = AutomationSequenceRequest(
                actions=[{
                    'action_type': action.action_type.value,
                    'params': action.params,
                    'description': action.description
                }],
                task_name="模板点击"
            )
            
            response = await self.execute_automation_sequence(request)
            return response.success
            
        except Exception as e:
            logger.error(f"模板点击失败: {e}")
            return False
    
    async def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间隔
            
        Returns:
            bool: 是否成功
        """
        try:
            action = AutomationAction(
                action_type=ActionType.TYPE_TEXT,
                params={'text': text, 'interval': interval},
                description=f"输入文本: {text}"
            )
            
            request = AutomationSequenceRequest(
                actions=[{
                    'action_type': action.action_type.value,
                    'params': action.params,
                    'description': action.description
                }],
                task_name="文本输入"
            )
            
            response = await self.execute_automation_sequence(request)
            return response.success
            
        except Exception as e:
            logger.error(f"文本输入失败: {e}")
            return False
    
    async def press_key(self, key: str) -> bool:
        """
        按键
        
        Args:
            key: 按键名称
            
        Returns:
            bool: 是否成功
        """
        try:
            action = AutomationAction(
                action_type=ActionType.KEY_PRESS,
                params={'key': key},
                description=f"按键: {key}"
            )
            
            request = AutomationSequenceRequest(
                actions=[{
                    'action_type': action.action_type.value,
                    'params': action.params,
                    'description': action.description
                }],
                task_name="按键操作"
            )
            
            response = await self.execute_automation_sequence(request)
            return response.success
            
        except Exception as e:
            logger.error(f"按键操作失败: {e}")
            return False
    
    # ==================== 状态查询 ====================
    
    async def get_automation_status(self) -> Dict[str, Any]:
        """
        获取自动化状态
        
        Returns:
            Dict: 状态信息
        """
        try:
            stats = self.automation_controller.get_stats()
            
            return {
                'status': 'success',
                'automation_status': stats['task_status'],
                'current_task_id': stats['current_task_id'],
                'queue_size': stats['queue_size'],
                'statistics': stats['stats'],
                'configuration': stats['config'],
                'game_active': self.game_detector.is_game_active(),
                'detection_stats': self.game_detector.get_detection_stats()
            }
            
        except Exception as e:
            logger.error(f"获取自动化状态失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康状态
        """
        try:
            # 检查各组件状态
            game_detector_ok = self.game_detector is not None
            automation_controller_ok = self.automation_controller is not None
            
            # 检查游戏检测功能
            try:
                self.game_detector.find_game_windows()
                game_detection_ok = True
            except Exception:
                game_detection_ok = False
            
            all_ok = game_detector_ok and automation_controller_ok and game_detection_ok
            
            return {
                'status': 'healthy' if all_ok else 'unhealthy',
                'components': {
                    'game_detector': 'ok' if game_detector_ok else 'error',
                    'automation_controller': 'ok' if automation_controller_ok else 'error',
                    'game_detection': 'ok' if game_detection_ok else 'error'
                },
                'initialized': self._initialized,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # ==================== BaseAsyncService抽象方法实现 ====================
    
    async def _startup(self) -> None:
        """服务启动"""
        await self.initialize()
        logger.info("AutomationApplicationService启动完成")
    
    async def _shutdown(self) -> None:
        """服务关闭"""
        await self.close()
        logger.info("AutomationApplicationService关闭完成")
    
    async def _health_check(self) -> bool:
        """健康检查"""
        health_result = await self.health_check()
        return health_result['status'] == 'healthy'