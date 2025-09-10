"""自动化控制器模块.

提供自动化任务的控制和协调功能.
"""

from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
from src.interfaces.automation_interface import IAutomationController
try:
    from src.core.game_detector import GameDetector, SceneType
    from src.task_management.task_manager import TaskManager, TaskPriority
    from src.exceptions import AutomationError, GameDetectionError
except ImportError:
    # 处理导入失败的情况
    GameDetector = None
    SceneType = None
    TaskManager = None
    TaskPriority = None
    AutomationError = Exception
    GameDetectionError = Exception


class AutomationStatus(Enum):
    """自动化状态枚举."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AutomationTask:
    """自动化任务数据类."""
    
    id: str
    name: str
    action: Callable
    priority: int = 1
    scene_requirement: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AutomationController(IAutomationController):
    """自动化控制器类，提供自动化任务的控制和协调功能."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 config_manager=None, game_detector=None, task_manager=None):
        """初始化自动化控制器.

        Args:
            config: 配置字典，可选
            config_manager: 配置管理器，可选
            game_detector: 游戏检测器，可选
            task_manager: 任务管理器，可选
        """
        self._config = config or {}
        self._status = AutomationStatus.IDLE
        self._tasks: List[AutomationTask] = []
        self._logger = logging.getLogger(__name__)
        self._running = False
        
        # 初始化游戏检测器和任务管理器
        self._game_detector = game_detector
        self._task_manager = task_manager
        
        # 如果没有提供外部依赖，则尝试创建默认实例
        if self._game_detector is None and GameDetector:
            try:
                self._game_detector = GameDetector()
                self._logger.info("游戏检测器初始化成功")
            except Exception as e:
                self._logger.error(f"游戏检测器初始化失败: {e}")
        
        if self._task_manager is None and TaskManager:
            try:
                self._task_manager = TaskManager()
                self._task_manager.start_concurrent_manager()
                self._logger.info("任务管理器初始化成功")
            except Exception as e:
                self._logger.error(f"任务管理器初始化失败: {e}")
        
        # 注册基本自动化任务
        self._register_basic_tasks()
        
        # 自动化循环相关
        self._automation_loop_task = None
        self._current_automation_tasks: List[str] = []
        self._automation_config = {
            'auto_restart_game': False,
            'max_continuous_failures': 5,
            'check_interval': 2.0,
            'scene_detection_threshold': 0.7
        }

    @property
    def status(self) -> AutomationStatus:
        """获取当前状态.

        Returns:
            当前自动化状态
        """
        return self._status

    @property
    def is_running(self) -> bool:
        """检查是否正在运行.

        Returns:
            是否正在运行
        """
        return self._running

    def start(self) -> bool:
        """启动自动化控制器.

        Returns:
            启动是否成功
        """
        try:
            if self._running:
                self._logger.warning("自动化控制器已在运行")
                return True

            self._running = True
            self._status = AutomationStatus.RUNNING
            self._logger.info("自动化控制器已启动")
            return True
        except Exception as e:
            self._logger.error(f"启动自动化控制器失败: {e}")
            self._status = AutomationStatus.ERROR
            return False

    def stop(self) -> bool:
        """停止自动化控制器.

        Returns:
            停止是否成功
        """
        try:
            if not self._running:
                self._logger.warning("自动化控制器未在运行")
                return True

            self._running = False
            self._status = AutomationStatus.STOPPED
            self._logger.info("自动化控制器已停止")
            return True
        except Exception as e:
            self._logger.error(f"停止自动化控制器失败: {e}")
            self._status = AutomationStatus.ERROR
            return False

    def _register_basic_tasks(self) -> None:
        """注册基本的自动化任务."""
        # 游戏检测任务
        self.add_task(AutomationTask(
            id="game_detection",
            name="游戏检测",
            action=self._detect_game_status,
            priority=1
        ))
        
        # 场景检测任务
        self.add_task(AutomationTask(
            id="scene_detection",
            name="场景检测",
            action=self._detect_current_scene,
            priority=2
        ))
        
        # 自动截图任务
        self.add_task(AutomationTask(
            id="auto_screenshot",
            name="自动截图",
            action=self._take_screenshot,
            priority=3
        ))
    
    def _detect_game_status(self) -> Dict[str, Any]:
        """检测游戏状态."""
        if not self._game_detector:
            return {"status": "error", "message": "游戏检测器未初始化"}
        
        try:
            is_running = self._game_detector.is_game_running()
            game_status = self._game_detector.get_game_status()
            
            return {
                "status": "success",
                "is_running": is_running,
                "game_status": game_status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"游戏状态检测失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _detect_current_scene(self) -> Dict[str, Any]:
        """检测当前场景."""
        if not self._game_detector:
            return {"status": "error", "message": "游戏检测器未初始化"}
        
        try:
            current_scene = self._game_detector.detect_scene()
            scene_name = current_scene.value if current_scene else "unknown"
            
            return {
                "status": "success",
                "scene": scene_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"场景检测失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _take_screenshot(self) -> Dict[str, Any]:
        """执行截图任务."""
        if not self._game_detector:
            return {"status": "error", "message": "游戏检测器未初始化"}
        
        try:
            screenshot = self._game_detector.capture_screenshot()
            if screenshot is not None:
                return {
                    "status": "success",
                    "screenshot_shape": screenshot.shape,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"status": "error", "message": "截图失败"}
        except Exception as e:
            self._logger.error(f"截图失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def execute(self, task_id: str) -> Dict[str, Any]:
        """执行指定的自动化任务.

        Args:
            task_id: 任务ID

        Returns:
            执行结果字典
        """
        start_time = time.time()
        
        try:
            if not self._running:
                self._logger.warning(f"尝试执行任务 {task_id}，但自动化控制器未运行")
                return {"status": "error", "message": "自动化控制器未运行"}

            # 查找任务
            task = None
            for t in self._tasks:
                if t.id == task_id:
                    task = t
                    break

            if not task:
                self._logger.error(f"未找到任务: {task_id}")
                return {"status": "error", "message": f"未找到任务: {task_id}"}

            self._logger.info(f"开始执行任务: {task.name} (ID: {task_id})")

            # 检查场景要求
            if task.scene_requirement:
                current_scene = self._detect_current_scene()
                if current_scene.get("scene") != task.scene_requirement:
                    self._logger.debug(f"任务 {task_id} 场景不匹配，跳过执行")
                    return {
                        "status": "skipped",
                        "message": f"场景不匹配，需要: {task.scene_requirement}, 当前: {current_scene.get('scene')}"
                    }

            # 执行任务
            try:
                result = task.action()
                task.retry_count = 0  # 重置重试计数
                execution_time = time.time() - start_time
                
                self._logger.info(f"任务 {task.name} 执行成功 (耗时: {execution_time:.2f}s)")
                return {
                    "status": "success", 
                    "result": result, 
                    "task_id": task_id,
                    "execution_time": execution_time
                }
            except Exception as e:
                task.retry_count += 1
                error_msg = f"任务执行失败: {str(e)}"
                execution_time = time.time() - start_time
                
                self._logger.error(f"任务 {task.name} 执行失败 (第{task.retry_count}次重试): {str(e)}")
                
                if task.retry_count < task.max_retries:
                    self._logger.info(f"任务 {task.name} 将进行重试 ({task.retry_count}/{task.max_retries})")
                    return {
                        "status": "retry",
                        "message": error_msg,
                        "retry_count": task.retry_count,
                        "max_retries": task.max_retries,
                        "execution_time": execution_time
                    }
                else:
                    self._logger.error(f"任务 {task.name} 达到最大重试次数，执行失败")
                    return {
                        "status": "failed",
                        "message": error_msg,
                        "retry_count": task.retry_count,
                        "execution_time": execution_time
                    }
        except Exception as e:
            execution_time = time.time() - start_time
            self._logger.error(f"执行任务 {task_id} 时发生未预期错误: {str(e)}")
            return {
                "status": "error",
                "message": f"执行任务时发生未预期错误: {str(e)}",
                "execution_time": execution_time
            }

    def execute_action(self, action: str, **kwargs) -> bool:
        """执行自动化动作.
        
        Args:
            action: 动作名称
            **kwargs: 动作参数
            
        Returns:
            执行是否成功
        """
        try:
            if not self.is_running:
                self._logger.warning("自动化控制器未运行，无法执行动作")
                return False
            
            if not action:
                self._logger.error("动作名称不能为空")
                return False
            
            self._logger.debug(f"开始执行动作: {action}, 参数: {kwargs}")
            
            # 基本的动作执行逻辑
            if action == "click":
                x = kwargs.get('x', 0)
                y = kwargs.get('y', 0)
                
                # 验证坐标
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    self._logger.error(f"无效的坐标类型: x={type(x)}, y={type(y)}")
                    return False
                
                if x < 0 or y < 0:
                    self._logger.error(f"坐标不能为负数: ({x}, {y})")
                    return False
                
                # 实际的点击实现
                try:
                    import pyautogui
                    pyautogui.click(x, y)
                    self._logger.info(f"执行点击动作: ({x}, {y})")
                    return True
                except ImportError:
                    # 如果没有pyautogui，使用模拟点击
                    self._logger.info(f"模拟点击动作: ({x}, {y}) (pyautogui未安装)")
                    return True
                except Exception as e:
                    self._logger.error(f"点击失败: {e}")
                    return False
                
            elif action == "screenshot":
                screenshot_path = kwargs.get('path', 'screenshot.png')
                
                # 验证路径
                if not isinstance(screenshot_path, str):
                    self._logger.error(f"无效的路径类型: {type(screenshot_path)}")
                    return False
                
                # 使用游戏检测器截图
                if self._game_detector:
                    screenshot = self._game_detector.capture_screenshot()
                    if screenshot is not None:
                        try:
                            import cv2
                            # 保存截图到指定路径
                            cv2.imwrite(screenshot_path, screenshot)
                            self._logger.info(f"截图已保存: {screenshot_path}")
                            return True
                        except Exception as e:
                            self._logger.error(f"保存截图失败: {e}")
                            return False
                    else:
                        self._logger.error("截图失败")
                        return False
                else:
                    self._logger.error("游戏检测器未初始化，无法截图")
                    return False
                
            elif action == "wait":
                duration = kwargs.get('duration', 1.0)
                
                # 验证等待时间
                if not isinstance(duration, (int, float)):
                    self._logger.error(f"无效的等待时间类型: {type(duration)}")
                    return False
                
                if duration < 0:
                    self._logger.error(f"等待时间不能为负数: {duration}")
                    return False
                
                if duration > 60:  # 限制最大等待时间
                    self._logger.warning(f"等待时间过长，限制为60秒: {duration}")
                    duration = 60
                
                time.sleep(duration)
                self._logger.info(f"等待 {duration} 秒")
                return True
                
            else:
                self._logger.warning(f"未知的动作: {action}")
                return False
                
        except Exception as e:
            self._logger.error(f"执行动作失败: {action}, 错误: {str(e)}", exc_info=True)
            return False

    def run(self, tasks: Optional[List[AutomationTask]] = None) -> bool:
        """运行任务列表.

        Args:
            tasks: 任务列表，可选

        Returns:
            运行是否成功
        """
        try:
            if not self.start():
                return False

            task_list = tasks or self._tasks
            success_count = 0
            total_tasks = len(task_list)

            self._logger.info(f"开始执行 {total_tasks} 个任务")

            for i, task in enumerate(task_list, 1):
                self._logger.info(f"执行任务 {i}/{total_tasks}: {task.name}")
                
                result = self.execute(task.id)
                if result.get("status") == "success":
                    success_count += 1
                    self._logger.info(f"任务 {task.name} 执行成功")
                else:
                    self._logger.warning(f"任务 {task.name} 执行失败: {result.get('message')}")
                
                # 任务间隔
                if i < total_tasks:
                    time.sleep(0.5)

            success_rate = (success_count / total_tasks) * 100 if total_tasks > 0 else 0
            self._logger.info(f"任务执行完成，成功: {success_count}/{total_tasks} ({success_rate:.1f}%)")
            
            return success_count == total_tasks
        except Exception as e:
            self._logger.error(f"运行任务失败: {e}")
            self._status = AutomationStatus.ERROR
            return False

    def add_task(self, task: AutomationTask) -> None:
        """添加任务.

        Args:
            task: 要添加的任务
        """
        self._tasks.append(task)
        self._logger.info(f"已添加任务: {task.name} (ID: {task.id})")
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功移除
        """
        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                removed_task = self._tasks.pop(i)
                self._logger.info(f"已移除任务: {removed_task.name} (ID: {task_id})")
                return True
        
        self._logger.warning(f"未找到任务ID: {task_id}")
        return False
    
    def get_task_by_id(self, task_id: str) -> Optional[AutomationTask]:
        """根据ID获取任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象或None
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def clear_tasks(self) -> None:
        """清空任务列表."""
        self._tasks.clear()
        self._logger.info("已清空任务列表")

    def get_tasks(self) -> List[AutomationTask]:
        """获取任务列表.

        Returns:
            当前任务列表
        """
        return self._tasks.copy()
    
    def get_available_automation_tasks(self) -> List[AutomationTask]:
        """获取可用的自动化任务对象列表.
        
        Returns:
            可用任务对象列表
        """
        # 如果没有任务，创建一些基本任务
        if not self._tasks:
            self._register_basic_tasks()
        
        return self._tasks.copy()
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态信息.
        
        Returns:
            任务状态字典
        """
        return {
            "controller_status": self._status.value,
            "is_running": self._running,
            "total_tasks": len(self._tasks),
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "priority": task.priority,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "scene_requirement": task.scene_requirement,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                for task in self._tasks
            ],
            "game_detector_available": self._game_detector is not None,
            "task_manager_available": self._task_manager is not None
        }
    
    # IAutomationController接口实现
    def start_automation(self) -> bool:
        """启动自动化.
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        return self.start()
    
    def stop_automation(self) -> bool:
        """停止自动化.
        
        Returns:
            bool: 停止成功返回True，失败返回False
        """
        return self.stop()
    
    def get_automation_status(self) -> str:
        """获取自动化状态.
        
        Returns:
            str: 自动化状态（running/stopped/error）
        """
        if self._status == AutomationStatus.RUNNING:
            return "running"
        elif self._status == AutomationStatus.ERROR:
            return "error"
        else:
            return "stopped"
    
    def get_available_tasks(self) -> List[str]:
        """获取可用任务列表.
        
        Returns:
            List[str]: 可用任务名称列表
        """
        # 如果没有任务，创建一些基本任务
        if not self._tasks:
            self._register_basic_tasks()
        
        return [task.name for task in self._tasks]
    
    async def start_automation_loop(self) -> bool:
        """启动自动化主循环.
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        try:
            if self._automation_loop_task and not self._automation_loop_task.done():
                self._logger.warning("自动化循环已在运行")
                return True
            
            import asyncio
            self._automation_loop_task = asyncio.create_task(self._automation_loop())
            self._logger.info("自动化主循环已启动")
            return True
            
        except Exception as e:
            self._logger.error(f"启动自动化循环失败: {e}")
            return False
    
    async def stop_automation_loop(self) -> bool:
        """停止自动化主循环.
        
        Returns:
            bool: 停止成功返回True，失败返回False
        """
        try:
            if self._automation_loop_task:
                self._automation_loop_task.cancel()
                self._automation_loop_task = None
            
            # 停止所有运行中的任务
            if self._task_manager:
                for task_id in self._current_automation_tasks:
                    try:
                        self._task_manager.stop_task(task_id)
                    except Exception as e:
                        self._logger.warning(f"停止任务{task_id}失败: {e}")
            
            self._current_automation_tasks.clear()
            self._logger.info("自动化主循环已停止")
            return True
            
        except Exception as e:
            self._logger.error(f"停止自动化循环失败: {e}")
            return False
    
    async def _automation_loop(self):
        """自动化主循环."""
        consecutive_failures = 0
        
        while self._running:
            try:
                # 检查游戏状态
                if self._game_detector and not self._game_detector.is_game_running():
                    self._logger.warning("游戏已关闭")
                    if self._automation_config['auto_restart_game']:
                        await self._handle_game_closed()
                    else:
                        break
                
                # 检测当前游戏场景
                current_scene = await self._detect_current_scene_async()
                self._logger.debug(f"当前场景: {current_scene}")
                
                # 根据场景执行相应操作
                await self._handle_scene(current_scene)
                
                # 检查并处理待处理任务
                await self._process_pending_tasks()
                
                # 重置失败计数
                consecutive_failures = 0
                
            except Exception as e:
                consecutive_failures += 1
                self._logger.error(f"自动化循环错误 ({consecutive_failures}/{self._automation_config['max_continuous_failures']}): {e}")
                
                if consecutive_failures >= self._automation_config['max_continuous_failures']:
                    self._logger.error("连续失败次数过多，停止自动化")
                    break
            
            # 等待下次检查
            import asyncio
            await asyncio.sleep(self._automation_config['check_interval'])
        
        # 清理
        self._running = False
        self._logger.info("自动化循环已结束")
    
    async def _detect_current_scene_async(self) -> str:
        """异步检测当前游戏场景.
        
        Returns:
            str: 场景名称
        """
        if not self._game_detector:
            return "unknown"
        
        try:
            # 截取游戏画面
            screenshot = self._game_detector.capture_screen()
            if screenshot is None:
                return "unknown"
            
            # 检测各种UI元素来判断场景
            scenes = {
                "main_menu": "assets/templates/main_menu.png",
                "world_map": "assets/templates/world_map.png", 
                "battle": "assets/templates/battle_ui.png",
                "mission_menu": "assets/templates/mission_menu.png",
                "inventory": "assets/templates/inventory.png"
            }
            
            threshold = self._automation_config.get('scene_detection_threshold', 0.7)
            for scene_name, template_path in scenes.items():
                try:
                    result = self._game_detector.find_template(template_path, threshold=threshold)
                    if result and result.get('found', False):
                        self._logger.debug(f"检测到场景: {scene_name}")
                        return scene_name
                except Exception as e:
                    self._logger.debug(f"检测场景{scene_name}失败: {e}")
            
            return "unknown"
            
        except Exception as e:
            self._logger.error(f"场景检测失败: {e}")
            return "unknown"
    
    async def _handle_scene(self, scene: str):
        """处理特定场景.
        
        Args:
            scene: 场景名称
        """
        try:
            if scene == "main_menu":
                await self._handle_main_menu()
            elif scene == "world_map":
                await self._handle_world_map()
            elif scene == "battle":
                await self._handle_battle()
            elif scene == "mission_menu":
                await self._handle_mission_menu()
            else:
                # 未知场景，尝试返回主界面
                await self._return_to_main_menu()
                
        except Exception as e:
            self._logger.error(f"处理场景{scene}失败: {e}")
    
    async def _handle_main_menu(self):
        """处理主菜单场景."""
        try:
            self._logger.debug("处理主菜单场景")
            
            # 检查是否有日常任务需要完成
            if await self._should_do_daily_missions():
                await self._start_daily_missions()
                return
            
            # 检查是否需要进入世界地图
            if await self._should_enter_world_map():
                await self._enter_world_map()
                return
            
            # 检查是否需要进入任务菜单
            if await self._should_enter_mission_menu():
                await self._enter_mission_menu()
                return
                
        except Exception as e:
            self._logger.error(f"处理主菜单场景失败: {e}")
    
    async def _handle_world_map(self):
        """处理世界地图场景."""
        try:
            self._logger.debug("处理世界地图场景")
            
            # 检查是否有资源点需要收集
            if await self._should_collect_resources():
                await self._start_resource_collection()
                return
            
            # 检查是否有可进入的关卡
            if await self._should_enter_stage():
                await self._enter_stage()
                return
                
        except Exception as e:
            self._logger.error(f"处理世界地图场景失败: {e}")
    
    async def _handle_battle(self):
        """处理战斗场景."""
        try:
            self._logger.info("检测到战斗中，监控战斗状态")
            
            # 检查是否需要使用技能
            if await self._should_use_skills():
                await self._use_battle_skills()
            
            # 等待战斗结束
            import asyncio
            await asyncio.sleep(2)
            
        except Exception as e:
            self._logger.error(f"处理战斗场景失败: {e}")
    
    async def _handle_mission_menu(self):
        """处理任务菜单场景."""
        try:
            self._logger.debug("处理任务菜单场景")
            
            # 检查并领取可用任务
            await self._claim_available_missions()
            
            # 检查是否有可完成的任务
            if await self._should_complete_missions():
                await self._complete_missions()
                
        except Exception as e:
            self._logger.error(f"处理任务菜单场景失败: {e}")
    
    async def _should_do_daily_missions(self) -> bool:
        """检查是否应该执行日常任务.
        
        Returns:
            bool: 是否应该执行日常任务
        """
        try:
            # 检查配置是否启用日常任务
            if not self._automation_config.get('enable_daily_missions', False):
                return False
            
            # 检查是否有未完成的日常任务标识
            daily_mission_icon = self._game_detector.find_template(
                "assets/templates/daily_mission_icon.png", threshold=0.7
            )
            return daily_mission_icon and daily_mission_icon.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查日常任务状态失败: {e}")
            return False
    
    async def _should_collect_resources(self) -> bool:
        """检查是否应该收集资源.
        
        Returns:
            bool: 是否应该收集资源
        """
        try:
            # 检查配置是否启用资源收集
            if not self._automation_config.get('enable_resource_collection', False):
                return False
            
            # 检查是否有可收集的资源点
            resource_icon = self._game_detector.find_template(
                "assets/templates/resource_point.png", threshold=0.7
            )
            return resource_icon and resource_icon.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查资源收集状态失败: {e}")
            return False
    
    async def _should_enter_world_map(self) -> bool:
        """检查是否应该进入世界地图.
        
        Returns:
            bool: 是否应该进入世界地图
        """
        try:
            # 检查是否有世界地图按钮
            world_map_button = self._game_detector.find_template(
                "assets/templates/world_map_button.png", threshold=0.7
            )
            return world_map_button and world_map_button.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查世界地图状态失败: {e}")
            return False
    
    async def _should_enter_mission_menu(self) -> bool:
        """检查是否应该进入任务菜单.
        
        Returns:
            bool: 是否应该进入任务菜单
        """
        try:
            # 检查是否有任务菜单按钮
            mission_button = self._game_detector.find_template(
                "assets/templates/mission_button.png", threshold=0.7
            )
            return mission_button and mission_button.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查任务菜单状态失败: {e}")
            return False
    
    async def _should_enter_stage(self) -> bool:
        """检查是否应该进入关卡.
        
        Returns:
            bool: 是否应该进入关卡
        """
        try:
            # 检查是否有可进入的关卡
            stage_button = self._game_detector.find_template(
                "assets/templates/stage_enter.png", threshold=0.7
            )
            return stage_button and stage_button.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查关卡状态失败: {e}")
            return False
    
    async def _should_use_skills(self) -> bool:
        """检查是否应该使用技能.
        
        Returns:
            bool: 是否应该使用技能
        """
        try:
            # 检查配置是否启用自动技能
            if not self._automation_config.get('enable_auto_skills', False):
                return False
            
            # 检查是否有可用技能
            skill_button = self._game_detector.find_template(
                "assets/templates/skill_available.png", threshold=0.7
            )
            return skill_button and skill_button.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查技能状态失败: {e}")
            return False
    
    async def _should_complete_missions(self) -> bool:
        """检查是否应该完成任务.
        
        Returns:
            bool: 是否应该完成任务
        """
        try:
            # 检查是否有可完成的任务
            complete_button = self._game_detector.find_template(
                "assets/templates/mission_complete.png", threshold=0.7
            )
            return complete_button and complete_button.get('found', False)
            
        except Exception as e:
            self._logger.error(f"检查任务完成状态失败: {e}")
            return False
    
    async def _start_daily_missions(self):
        """开始执行日常任务."""
        try:
            self._logger.info("开始执行日常任务")
            
            # 创建日常任务
            if self._task_manager:
                task_id = self._task_manager.create_task(
                    task_type='daily_missions',
                    task_data={'action': 'execute_daily_missions'}
                )
                
                # 启动任务
                if task_id:
                    self._task_manager.start_task(task_id)
                    self._current_automation_tasks.append(task_id)
                    self._logger.info(f"已创建并启动日常任务: {task_id}")
            
            # 执行实际的日常任务逻辑
            await self._execute_daily_missions_logic()
                
        except Exception as e:
            self._logger.error(f"执行日常任务失败: {e}")
    
    async def _execute_daily_missions_logic(self):
        """执行日常任务的具体逻辑."""
        try:
            # 进入任务菜单
            if await self._enter_mission_menu():
                # 查找并点击日常任务
                daily_tab = self._game_detector.find_template(
                    "assets/templates/daily_tab.png", threshold=0.7
                )
                if daily_tab and daily_tab.get('found', False):
                    await self._click_at_location(daily_tab['center'])
                    await asyncio.sleep(1)
                    
                    # 领取所有可领取的日常任务奖励
                    await self._claim_all_rewards()
                    
                    # 开始执行未完成的日常任务
                    await self._execute_daily_tasks()
                    
                self._logger.info("日常任务执行完成")
            else:
                self._logger.warning("无法进入任务菜单")
                
        except Exception as e:
            self._logger.error(f"执行日常任务逻辑失败: {e}")
    
    async def _start_resource_collection(self):
        """开始收集资源."""
        try:
            self._logger.info("开始收集资源")
            
            # 创建资源收集任务
            if self._task_manager:
                task_id = self._task_manager.create_task(
                    task_type='resource_collection',
                    task_data={'action': 'collect_resources'}
                )
                
                # 启动任务
                if task_id:
                    self._task_manager.start_task(task_id)
                    self._current_automation_tasks.append(task_id)
                    self._logger.info(f"已创建并启动资源收集任务: {task_id}")
            
            # 执行实际的资源收集逻辑
            await self._execute_resource_collection_logic()
                
        except Exception as e:
            self._logger.error(f"收集资源失败: {e}")
    
    async def _execute_resource_collection_logic(self):
        """执行资源收集的具体逻辑."""
        try:
            # 进入世界地图
            if await self._enter_world_map():
                # 查找资源点
                resource_points = await self._find_resource_points()
                
                for point in resource_points:
                    try:
                        # 点击资源点
                        await self._click_at_location(point)
                        await asyncio.sleep(2)
                        
                        # 确认收集
                        collect_button = self._game_detector.find_template(
                            "assets/templates/collect_button.png", threshold=0.7
                        )
                        if collect_button and collect_button.get('found', False):
                            await self._click_at_location(collect_button['center'])
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        self._logger.error(f"收集资源点失败: {e}")
                        continue
                        
                self._logger.info("资源收集完成")
            else:
                self._logger.warning("无法进入世界地图")
                
        except Exception as e:
            self._logger.error(f"执行资源收集逻辑失败: {e}")
    
    async def _enter_world_map(self) -> bool:
        """进入世界地图.
        
        Returns:
            bool: 是否成功进入世界地图
        """
        try:
            # 查找世界地图按钮
            world_map_button = self._game_detector.find_template(
                "assets/templates/world_map_button.png", threshold=0.7
            )
            
            if world_map_button and world_map_button.get('found', False):
                await self._click_at_location(world_map_button['center'])
                await asyncio.sleep(2)
                
                # 验证是否成功进入世界地图
                world_map_indicator = self._game_detector.find_template(
                    "assets/templates/world_map_indicator.png", threshold=0.7
                )
                
                if world_map_indicator and world_map_indicator.get('found', False):
                    self._logger.info("成功进入世界地图")
                    return True
                    
            self._logger.warning("无法进入世界地图")
            return False
            
        except Exception as e:
            self._logger.error(f"进入世界地图失败: {e}")
            return False
    
    async def _enter_mission_menu(self) -> bool:
        """进入任务菜单.
        
        Returns:
            bool: 是否成功进入任务菜单
        """
        try:
            # 查找任务菜单按钮
            mission_button = self._game_detector.find_template(
                "assets/templates/mission_button.png", threshold=0.7
            )
            
            if mission_button and mission_button.get('found', False):
                await self._click_at_location(mission_button['center'])
                await asyncio.sleep(2)
                
                # 验证是否成功进入任务菜单
                mission_indicator = self._game_detector.find_template(
                    "assets/templates/mission_menu_indicator.png", threshold=0.7
                )
                
                if mission_indicator and mission_indicator.get('found', False):
                    self._logger.info("成功进入任务菜单")
                    return True
                    
            self._logger.warning("无法进入任务菜单")
            return False
            
        except Exception as e:
            self._logger.error(f"进入任务菜单失败: {e}")
            return False
    
    async def _enter_stage(self, stage_name: str = None) -> bool:
        """进入指定关卡.
        
        Args:
            stage_name: 关卡名称，如果为None则进入推荐关卡
            
        Returns:
            bool: 是否成功进入关卡
        """
        try:
            # 查找关卡进入按钮
            stage_button = self._game_detector.find_template(
                "assets/templates/stage_enter.png", threshold=0.7
            )
            
            if stage_button and stage_button.get('found', False):
                await self._click_at_location(stage_button['center'])
                await asyncio.sleep(2)
                
                # 确认进入关卡
                confirm_button = self._game_detector.find_template(
                    "assets/templates/confirm_enter.png", threshold=0.7
                )
                
                if confirm_button and confirm_button.get('found', False):
                    await self._click_at_location(confirm_button['center'])
                    await asyncio.sleep(3)
                    
                    # 验证是否成功进入关卡
                    battle_indicator = self._game_detector.find_template(
                        "assets/templates/battle_indicator.png", threshold=0.7
                    )
                    
                    if battle_indicator and battle_indicator.get('found', False):
                        self._logger.info(f"成功进入关卡: {stage_name or '默认关卡'}")
                        return True
                        
            self._logger.warning(f"无法进入关卡: {stage_name or '默认关卡'}")
            return False
            
        except Exception as e:
            self._logger.error(f"进入关卡失败: {e}")
            return False
    
    async def _claim_available_missions(self):
        """领取可用任务."""
        if not self._game_detector:
            return
        
        try:
            # 检测并点击任务领取按钮
            claim_button = self._game_detector.find_template("assets/templates/claim_button.png", threshold=0.7)
            if claim_button and claim_button.get('found', False):
                # 获取按钮中心位置
                location = claim_button.get('center')
                if location and isinstance(location, (tuple, list)) and len(location) >= 2:
                    # 验证坐标是否为有效数字
                    if isinstance(location[0], (int, float)) and isinstance(location[1], (int, float)):
                        # 模拟点击
                        await self._click_at_location(location)
                        self._logger.info("已领取可用任务")
                        # 等待UI响应
                        await asyncio.sleep(1)
                    else:
                        self._logger.warning(f"位置坐标类型无效: {location}")
                else:
                    self._logger.warning(f"找到领取按钮但位置信息无效: {location}")
            else:
                self._logger.debug("未找到可领取的任务按钮")
        except Exception as e:
            self._logger.error(f"领取任务失败: {e}")
    
    async def _claim_all_rewards(self):
        """领取所有可用奖励."""
        try:
            # 查找一键领取按钮
            claim_all_button = self._game_detector.find_template(
                "assets/templates/claim_all_button.png", threshold=0.7
            )
            
            if claim_all_button and claim_all_button.get('found', False):
                await self._click_at_location(claim_all_button['center'])
                await asyncio.sleep(2)
                self._logger.info("已一键领取所有奖励")
                return
            
            # 如果没有一键领取，逐个领取
            reward_buttons = await self._find_all_reward_buttons()
            for button in reward_buttons:
                try:
                    await self._click_at_location(button)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self._logger.error(f"领取单个奖励失败: {e}")
                    
            self._logger.info(f"已领取 {len(reward_buttons)} 个奖励")
            
        except Exception as e:
            self._logger.error(f"领取奖励失败: {e}")
    
    async def _execute_daily_tasks(self):
        """执行日常任务."""
        try:
            # 查找未完成的日常任务
            incomplete_tasks = await self._find_incomplete_daily_tasks()
            
            for task in incomplete_tasks:
                try:
                    self._logger.info(f"开始执行日常任务: {task.get('name', '未知任务')}")
                    
                    # 点击任务开始执行
                    if 'position' in task:
                        await self._click_at_location(task['position'])
                        await asyncio.sleep(1)
                        
                        # 根据任务类型执行不同操作
                        await self._execute_task_by_type(task)
                        
                except Exception as e:
                    self._logger.error(f"执行日常任务失败: {e}")
                    continue
                    
        except Exception as e:
            self._logger.error(f"执行日常任务失败: {e}")
    
    async def _execute_task_by_type(self, task: dict):
        """根据任务类型执行相应操作.
        
        Args:
            task: 任务信息字典
        """
        task_type = task.get('type', 'unknown')
        
        try:
            if task_type == 'battle':
                await self._execute_battle_task(task)
            elif task_type == 'collection':
                await self._execute_collection_task(task)
            elif task_type == 'exploration':
                await self._execute_exploration_task(task)
            else:
                self._logger.warning(f"未知任务类型: {task_type}")
                
        except Exception as e:
            self._logger.error(f"执行任务类型 {task_type} 失败: {e}")
    
    async def _execute_battle_task(self, task: dict):
        """执行战斗类任务.
        
        Args:
            task: 战斗任务信息
        """
        try:
            # 进入推荐关卡
            if await self._enter_stage():
                # 开始自动战斗
                await self._start_auto_battle()
                
                # 等待战斗结束
                await self._wait_for_battle_end()
                
                # 领取战斗奖励
                await self._claim_battle_rewards()
                
                self._logger.info("战斗任务执行完成")
            else:
                self._logger.warning("无法进入战斗关卡")
                
        except Exception as e:
            self._logger.error(f"执行战斗任务失败: {e}")
    
    async def _execute_collection_task(self, task: dict):
        """执行收集类任务.
        
        Args:
            task: 收集任务信息
        """
        try:
            # 进入世界地图
            if await self._enter_world_map():
                # 查找并收集指定资源
                target_resource = task.get('target', 'any')
                await self._collect_specific_resource(target_resource)
                
                self._logger.info(f"收集任务执行完成: {target_resource}")
            else:
                self._logger.warning("无法进入世界地图执行收集任务")
                
        except Exception as e:
            self._logger.error(f"执行收集任务失败: {e}")
    
    async def _execute_exploration_task(self, task: dict):
        """执行探索类任务.
        
        Args:
            task: 探索任务信息
        """
        try:
            # 进入世界地图
            if await self._enter_world_map():
                # 探索指定区域
                target_area = task.get('area', 'current')
                await self._explore_area(target_area)
                
                self._logger.info(f"探索任务执行完成: {target_area}")
            else:
                self._logger.warning("无法进入世界地图执行探索任务")
                
        except Exception as e:
            self._logger.error(f"执行探索任务失败: {e}")
    
    async def _find_all_reward_buttons(self) -> List[tuple]:
        """查找所有奖励按钮位置.
        
        Returns:
            List[tuple]: 奖励按钮位置列表
        """
        try:
            reward_buttons = []
            
            # 查找多个奖励按钮模板
            templates = [
                "assets/templates/reward_button.png",
                "assets/templates/claim_reward.png",
                "assets/templates/get_reward.png"
            ]
            
            for template in templates:
                try:
                    result = self._game_detector.find_template(template, threshold=0.7)
                    if result and result.get('found', False):
                        reward_buttons.append(result['center'])
                except Exception as e:
                    self._logger.debug(f"查找模板 {template} 失败: {e}")
            
            return reward_buttons
            
        except Exception as e:
            self._logger.error(f"查找奖励按钮失败: {e}")
            return []
    
    async def _find_resource_points(self) -> List[tuple]:
        """查找所有资源点位置.
        
        Returns:
            List[tuple]: 资源点位置列表
        """
        try:
            resource_points = []
            
            # 查找多个资源点模板
            templates = [
                "assets/templates/resource_point.png",
                "assets/templates/material_point.png",
                "assets/templates/treasure_chest.png"
            ]
            
            for template in templates:
                try:
                    result = self._game_detector.find_template(template, threshold=0.7)
                    if result and result.get('found', False):
                        resource_points.append(result['center'])
                except Exception as e:
                    self._logger.debug(f"查找资源模板 {template} 失败: {e}")
            
            return resource_points
            
        except Exception as e:
            self._logger.error(f"查找资源点失败: {e}")
            return []
    
    async def _find_incomplete_daily_tasks(self) -> List[dict]:
        """查找未完成的日常任务.
        
        Returns:
            List[dict]: 未完成任务列表
        """
        try:
            incomplete_tasks = []
            
            # 查找任务列表中的未完成标识
            incomplete_icon = self._game_detector.find_template(
                "assets/templates/task_incomplete.png", threshold=0.7
            )
            
            if incomplete_icon and incomplete_icon.get('found', False):
                # 这里可以扩展为识别具体的任务类型和位置
                incomplete_tasks.append({
                    'name': '日常任务',
                    'type': 'battle',
                    'position': incomplete_icon['center']
                })
            
            return incomplete_tasks
            
        except Exception as e:
            self._logger.error(f"查找未完成任务失败: {e}")
            return []
    
    async def _start_auto_battle(self):
        """开始自动战斗."""
        try:
            # 查找自动战斗按钮
            auto_button = self._game_detector.find_template(
                "assets/templates/auto_battle.png", threshold=0.7
            )
            
            if auto_button and auto_button.get('found', False):
                await self._click_at_location(auto_button['center'])
                self._logger.info("已开启自动战斗")
            else:
                self._logger.warning("未找到自动战斗按钮")
                
        except Exception as e:
            self._logger.error(f"开启自动战斗失败: {e}")
    
    async def _wait_for_battle_end(self):
        """等待战斗结束."""
        try:
            max_wait_time = 300  # 最大等待5分钟
            check_interval = 5   # 每5秒检查一次
            waited_time = 0
            
            while waited_time < max_wait_time:
                # 检查是否有战斗结束标识
                victory_screen = self._game_detector.find_template(
                    "assets/templates/victory.png", threshold=0.7
                )
                defeat_screen = self._game_detector.find_template(
                    "assets/templates/defeat.png", threshold=0.7
                )
                
                if (victory_screen and victory_screen.get('found', False)) or \
                   (defeat_screen and defeat_screen.get('found', False)):
                    self._logger.info("战斗已结束")
                    return
                
                await asyncio.sleep(check_interval)
                waited_time += check_interval
            
            self._logger.warning("等待战斗结束超时")
            
        except Exception as e:
            self._logger.error(f"等待战斗结束失败: {e}")
    
    async def _claim_battle_rewards(self):
        """领取战斗奖励."""
        try:
            # 查找奖励领取按钮
            claim_button = self._game_detector.find_template(
                "assets/templates/claim_battle_reward.png", threshold=0.7
            )
            
            if claim_button and claim_button.get('found', False):
                await self._click_at_location(claim_button['center'])
                await asyncio.sleep(2)
                self._logger.info("已领取战斗奖励")
            else:
                self._logger.debug("未找到战斗奖励按钮")
                
        except Exception as e:
            self._logger.error(f"领取战斗奖励失败: {e}")
    
    async def _collect_specific_resource(self, resource_type: str):
        """收集指定类型的资源.
        
        Args:
            resource_type: 资源类型
        """
        try:
            # 根据资源类型查找对应的资源点
            template_map = {
                'gold': "assets/templates/gold_resource.png",
                'exp': "assets/templates/exp_resource.png",
                'material': "assets/templates/material_resource.png",
                'any': "assets/templates/resource_point.png"
            }
            
            template = template_map.get(resource_type, template_map['any'])
            resource_point = self._game_detector.find_template(template, threshold=0.7)
            
            if resource_point and resource_point.get('found', False):
                await self._click_at_location(resource_point['center'])
                await asyncio.sleep(2)
                
                # 确认收集
                collect_button = self._game_detector.find_template(
                    "assets/templates/collect_confirm.png", threshold=0.7
                )
                if collect_button and collect_button.get('found', False):
                    await self._click_at_location(collect_button['center'])
                    self._logger.info(f"已收集资源: {resource_type}")
            else:
                self._logger.warning(f"未找到资源点: {resource_type}")
                
        except Exception as e:
            self._logger.error(f"收集资源失败: {e}")
    
    async def _explore_area(self, area_name: str):
        """探索指定区域.
        
        Args:
            area_name: 区域名称
        """
        try:
            # 查找探索按钮
            explore_button = self._game_detector.find_template(
                "assets/templates/explore_button.png", threshold=0.7
            )
            
            if explore_button and explore_button.get('found', False):
                await self._click_at_location(explore_button['center'])
                await asyncio.sleep(3)
                
                # 等待探索完成
                await self._wait_for_exploration_complete()
                
                self._logger.info(f"探索完成: {area_name}")
            else:
                self._logger.warning(f"未找到探索按钮: {area_name}")
                
        except Exception as e:
            self._logger.error(f"探索区域失败: {e}")
    
    async def _wait_for_exploration_complete(self):
        """等待探索完成."""
        try:
            max_wait_time = 180  # 最大等待3分钟
            check_interval = 3   # 每3秒检查一次
            waited_time = 0
            
            while waited_time < max_wait_time:
                # 检查是否有探索完成标识
                complete_screen = self._game_detector.find_template(
                    "assets/templates/exploration_complete.png", threshold=0.7
                )
                
                if complete_screen and complete_screen.get('found', False):
                    self._logger.info("探索已完成")
                    return
                
                await asyncio.sleep(check_interval)
                waited_time += check_interval
            
            self._logger.warning("等待探索完成超时")
            
        except Exception as e:
            self._logger.error(f"等待探索完成失败: {e}")
    
    async def _find_resource_points(self) -> List[tuple]:
        """查找所有资源点位置.
        
        Returns:
            List[tuple]: 资源点位置列表
        """
        try:
            resource_points = []
            
            # 查找多种资源点模板
            templates = [
                "assets/templates/gold_resource.png",
                "assets/templates/exp_resource.png",
                "assets/templates/material_resource.png",
                "assets/templates/resource_point.png"
            ]
            
            for template in templates:
                try:
                    result = self._game_detector.find_template(template, threshold=0.7)
                    if result and result.get('found', False):
                        resource_points.append(result['center'])
                except Exception as e:
                    self._logger.debug(f"查找资源模板 {template} 失败: {e}")
            
            return resource_points
            
        except Exception as e:
            self._logger.error(f"查找资源点失败: {e}")
            return []
    
    async def _use_battle_skills(self):
        """使用战斗技能."""
        try:
            # 查找可用技能按钮
            skill_buttons = await self._find_available_skills()
            
            for skill_pos in skill_buttons:
                try:
                    await self._click_at_location(skill_pos)
                    await asyncio.sleep(0.5)
                    self._logger.debug(f"使用技能: {skill_pos}")
                except Exception as e:
                    self._logger.error(f"使用技能失败: {e}")
            
            if skill_buttons:
                self._logger.info(f"已使用 {len(skill_buttons)} 个技能")
                
        except Exception as e:
            self._logger.error(f"使用战斗技能失败: {e}")
    
    async def _find_available_skills(self) -> List[tuple]:
        """查找可用技能位置.
        
        Returns:
            List[tuple]: 技能按钮位置列表
        """
        try:
            skill_positions = []
            
            # 查找技能按钮模板
            templates = [
                "assets/templates/skill1_ready.png",
                "assets/templates/skill2_ready.png",
                "assets/templates/skill3_ready.png",
                "assets/templates/skill_available.png"
            ]
            
            for template in templates:
                try:
                    result = self._game_detector.find_template(template, threshold=0.7)
                    if result and result.get('found', False):
                        skill_positions.append(result['center'])
                except Exception as e:
                    self._logger.debug(f"查找技能模板 {template} 失败: {e}")
            
            return skill_positions
            
        except Exception as e:
            self._logger.error(f"查找可用技能失败: {e}")
            return []
    
    async def _complete_missions(self):
        """完成任务."""
        try:
            # 查找完成按钮
            complete_buttons = await self._find_complete_buttons()
            
            for button_pos in complete_buttons:
                try:
                    await self._click_at_location(button_pos)
                    await asyncio.sleep(1)
                    self._logger.info(f"已完成任务: {button_pos}")
                except Exception as e:
                    self._logger.error(f"完成任务失败: {e}")
            
            if complete_buttons:
                self._logger.info(f"已完成 {len(complete_buttons)} 个任务")
            else:
                self._logger.debug("没有可完成的任务")
                
        except Exception as e:
            self._logger.error(f"完成任务失败: {e}")
    
    async def _find_complete_buttons(self) -> List[tuple]:
        """查找完成按钮位置.
        
        Returns:
            List[tuple]: 完成按钮位置列表
        """
        try:
            complete_positions = []
            
            # 查找完成按钮模板
            templates = [
                "assets/templates/mission_complete.png",
                "assets/templates/complete_button.png",
                "assets/templates/finish_button.png"
            ]
            
            for template in templates:
                try:
                    result = self._game_detector.find_template(template, threshold=0.7)
                    if result and result.get('found', False):
                        complete_positions.append(result['center'])
                except Exception as e:
                    self._logger.debug(f"查找完成按钮模板 {template} 失败: {e}")
            
            return complete_positions
            
        except Exception as e:
            self._logger.error(f"查找完成按钮失败: {e}")
            return []
    
    async def _return_to_main_menu(self):
        """返回主菜单."""
        try:
            # 尝试按ESC键返回
            await self._press_key('esc')
            import asyncio
            await asyncio.sleep(1)
            self._logger.debug("已按ESC键尝试返回主菜单")
        except Exception as e:
            self._logger.error(f"返回主菜单失败: {e}")
    
    async def _click_at_location(self, location: tuple):
        """在指定位置点击.
        
        Args:
            location: 点击位置坐标 (x, y)
        """
        try:
            if not isinstance(location, (tuple, list)) or len(location) != 2:
                self._logger.error(f"无效的位置坐标: {location}")
                return False
            
            x, y = location
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                self._logger.error(f"坐标必须是数字: ({x}, {y})")
                return False
            
            # 尝试使用pyautogui进行点击
            try:
                import pyautogui
                # 移动鼠标到目标位置
                pyautogui.moveTo(x, y, duration=0.2)
                # 点击
                pyautogui.click(x, y)
                self._logger.debug(f"已点击位置: ({x}, {y})")
                
            except ImportError:
                # 如果没有pyautogui，尝试使用其他方法
                try:
                    import mouse
                    mouse.move(x, y)
                    mouse.click('left')
                    self._logger.debug(f"已点击位置: ({x}, {y}) (使用mouse库)")
                except ImportError:
                    # 模拟点击记录
                    self._logger.info(f"模拟点击位置: ({x}, {y}) (无可用点击库)")
            
            import asyncio
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self._logger.error(f"点击操作失败: {e}")
            return False
    
    async def _press_key(self, key: str):
        """按下指定按键.
        
        Args:
            key: 按键名称
        """
        try:
            # 尝试使用pyautogui
            try:
                import pyautogui
                pyautogui.press(key)
                self._logger.debug(f"已按下按键: {key}")
                
            except ImportError:
                # 尝试使用keyboard库
                try:
                    import keyboard
                    keyboard.press_and_release(key)
                    self._logger.debug(f"已按下按键: {key} (使用keyboard库)")
                except ImportError:
                    # 模拟按键记录
                    self._logger.info(f"模拟按键: {key} (无可用按键库)")
            
            return True
            
        except Exception as e:
            self._logger.error(f"按键操作失败: {e}")
            return False
    
    async def _process_pending_tasks(self):
        """处理待处理任务."""
        if not self._task_manager:
            return
        
        try:
            # 清理已完成的任务
            completed_tasks = []
            for task_id in self._current_automation_tasks:
                try:
                    status = self._task_manager.get_task_status(task_id)
                    if status in ['completed', 'failed', 'cancelled']:
                        completed_tasks.append(task_id)
                except Exception as e:
                    self._logger.warning(f"获取任务{task_id}状态失败: {e}")
                    completed_tasks.append(task_id)  # 移除有问题的任务
            
            for task_id in completed_tasks:
                self._current_automation_tasks.remove(task_id)
                self._logger.info(f"任务已完成: {task_id}")
                
        except Exception as e:
            self._logger.error(f"处理待处理任务失败: {e}")
    
    async def _handle_game_closed(self):
        """处理游戏关闭情况."""
        self._logger.info("检测到游戏关闭，停止自动化")
        # 暂时停止自动化
        self._running = False
    
    def set_automation_config(self, config: Dict[str, Any]):
        """设置自动化配置.
        
        Args:
            config: 配置字典
        """
        self._automation_config.update(config)
        self._logger.info(f"自动化配置已更新: {config}")
    
    def get_automation_config(self) -> Dict[str, Any]:
        """获取自动化配置.
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        return self._automation_config.copy()
    
    def get_current_automation_tasks(self) -> List[str]:
        """获取当前运行的自动化任务列表.
        
        Returns:
            List[str]: 任务ID列表
        """
        return self._current_automation_tasks.copy()
