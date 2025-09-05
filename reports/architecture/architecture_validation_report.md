# 架构验证报告

**一致性分数**: 0%

**总违规数**: 156
**错误**: 0
**警告**: 84

## 违规详情

### Naming Convention

- **INFO**: UI文件 monitoring_dashboard 建议使用MVP命名约定
  - 文件: src\ui\monitoring_dashboard.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 automation_settings_mvp 建议使用MVP命名约定
  - 文件: src\ui\automation_settings\automation_settings_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 ui_components 建议使用MVP命名约定
  - 文件: src\ui\common\ui_components.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 game_settings_mvp 建议使用MVP命名约定
  - 文件: src\ui\game_settings\game_settings_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 main_window_mvp 建议使用MVP命名约定
  - 文件: src\ui\main_window\main_window_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 task_creation_mvp 建议使用MVP命名约定
  - 文件: src\ui\task_creation\task_creation_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 task_execution_history_mvp 建议使用MVP命名约定
  - 文件: src\ui\task_execution_history\task_execution_history_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

- **INFO**: UI文件 task_list_mvp 建议使用MVP命名约定
  - 文件: src\ui\task_list\task_list_mvp.py
  - 建议: 文件名应包含 _view、_presenter 或 _model 后缀

### Solid Principle

- **INFO**: 函数 _normalize_enum_values 过长(51行)
  - 文件: src\adapters\model_adapter.py
  - 行号: 144
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(631行)，可能违反单一职责原则
  - 文件: src\adapters\task_manager_adapter.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskManagerAdapter 有太多方法(25)，可能违反单一职责原则
  - 文件: src\adapters\task_manager_adapter.py
  - 行号: 21
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(756行)，可能违反单一职责原则
  - 文件: src\application\automation_service.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(614行)，可能违反单一职责原则
  - 文件: src\application\error_handling_service.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 __init__ 过长(52行)
  - 文件: src\application\error_handling_service.py
  - 行号: 105
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(1259行)，可能违反单一职责原则
  - 文件: src\application\task_service.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(583行)，可能违反单一职责原则
  - 文件: src\automation\automation_controller.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 AutomationController 有太多方法(23)，可能违反单一职责原则
  - 文件: src\automation\automation_controller.py
  - 行号: 45
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _execute_task 过长(69行)
  - 文件: src\automation\automation_controller.py
  - 行号: 212
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(562行)，可能违反单一职责原则
  - 文件: src\config\error_recovery_strategies.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _init_default_strategies 过长(363行)
  - 文件: src\config\error_recovery_strategies.py
  - 行号: 78
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(822行)，可能违反单一职责原则
  - 文件: src\core\action_executor.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(1280行)，可能违反单一职责原则
  - 文件: src\core\config_manager.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 ConfigManager 有太多方法(37)，可能违反单一职责原则
  - 文件: src\core\config_manager.py
  - 行号: 321
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 import_config 过长(69行)
  - 文件: src\core\config_manager.py
  - 行号: 399
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 validate_config 过长(67行)
  - 文件: src\core\config_manager.py
  - 行号: 470
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(596行)，可能违反单一职责原则
  - 文件: src\core\error_handling.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(704行)，可能违反单一职责原则
  - 文件: src\core\error_recovery_coordinator.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(604行)，可能违反单一职责原则
  - 文件: src\core\exception_recovery.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _execute_recovery 过长(85行)
  - 文件: src\core\exception_recovery.py
  - 行号: 325
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(621行)，可能违反单一职责原则
  - 文件: src\core\game_detector.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(676行)，可能违反单一职责原则
  - 文件: src\core\game_operations.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(563行)，可能违反单一职责原则
  - 文件: src\core\intelligent_scheduler.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 IntelligentScheduler 有太多方法(21)，可能违反单一职责原则
  - 文件: src\core\intelligent_scheduler.py
  - 行号: 77
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _task_execution_wrapper 过长(67行)
  - 文件: src\core\intelligent_scheduler.py
  - 行号: 386
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 setup_logger 过长(94行)
  - 文件: src\core\logger.py
  - 行号: 36
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(585行)，可能违反单一职责原则
  - 文件: src\core\performance_monitor.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 get_performance_summary 过长(52行)
  - 文件: src\core\performance_monitor.py
  - 行号: 416
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 get_optimization_recommendations 过长(65行)
  - 文件: src\core\performance_monitor.py
  - 行号: 470
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(1437行)，可能违反单一职责原则
  - 文件: src\core\sync_adapter.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 SyncAdapter 有太多方法(34)，可能违反单一职责原则
  - 文件: src\core\sync_adapter.py
  - 行号: 170
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 run_async 过长(93行)
  - 文件: src\core\sync_adapter.py
  - 行号: 520
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_action 过长(76行)
  - 文件: src\core\task_actions.py
  - 行号: 360
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(597行)，可能违反单一职责原则
  - 文件: src\core\task_executor.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(2902行)，可能违反单一职责原则
  - 文件: src\core\task_manager.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskManager 有太多方法(42)，可能违反单一职责原则
  - 文件: src\core\task_manager.py
  - 行号: 155
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 __init__ 过长(62行)
  - 文件: src\core\task_manager.py
  - 行号: 158
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 get_task_sync 过长(54行)
  - 文件: src\core\task_manager.py
  - 行号: 1142
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 list_tasks_sync 过长(76行)
  - 文件: src\core\task_manager.py
  - 行号: 1489
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 update_task_action 过长(56行)
  - 文件: src\core\task_manager.py
  - 行号: 1714
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_task_sync 过长(76行)
  - 文件: src\core\task_manager.py
  - 行号: 1849
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(549行)，可能违反单一职责原则
  - 文件: src\core\task_retry_manager.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 schedule_retry 过长(59行)
  - 文件: src\core\task_retry_manager.py
  - 行号: 168
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(552行)，可能违反单一职责原则
  - 文件: src\core\task_validator.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _validate_basic_info 过长(62行)
  - 文件: src\core\task_validator.py
  - 行号: 98
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _validate_schedule_config 过长(55行)
  - 文件: src\core\task_validator.py
  - 行号: 212
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _validate_single_action 过长(60行)
  - 文件: src\core\task_validator.py
  - 行号: 291
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _validate_action_params 过长(118行)
  - 文件: src\core\task_validator.py
  - 行号: 353
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(913行)，可能违反单一职责原则
  - 文件: src\database\db_manager.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 DatabaseManager 有太多方法(29)，可能违反单一职责原则
  - 文件: src\database\db_manager.py
  - 行号: 16
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 initialize_database 过长(133行)
  - 文件: src\database\db_manager.py
  - 行号: 131
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_task 过长(59行)
  - 文件: src\database\db_manager.py
  - 行号: 288
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_task_action 过长(55行)
  - 文件: src\database\db_manager.py
  - 行号: 601
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(522行)，可能违反单一职责原则
  - 文件: src\infrastructure\architecture_validator.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _validate_solid_principles 过长(54行)
  - 文件: src\infrastructure\architecture_validator.py
  - 行号: 318
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(501行)，可能违反单一职责原则
  - 文件: src\middleware\error_handling_middleware.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 ErrorHandlingMiddleware 有太多方法(25)，可能违反单一职责原则
  - 文件: src\middleware\error_handling_middleware.py
  - 行号: 24
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 handle_error 过长(85行)
  - 文件: src\middleware\error_handling_middleware.py
  - 行号: 114
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(851行)，可能违反单一职责原则
  - 文件: src\monitoring\alert_manager.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 AlertManager 有太多方法(30)，可能违反单一职责原则
  - 文件: src\monitoring\alert_manager.py
  - 行号: 364
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 create_alert 过长(62行)
  - 文件: src\monitoring\alert_manager.py
  - 行号: 465
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(939行)，可能违反单一职责原则
  - 文件: src\monitoring\health_checker.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _perform_check 过长(66行)
  - 文件: src\monitoring\health_checker.py
  - 行号: 150
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _perform_check 过长(69行)
  - 文件: src\monitoring\health_checker.py
  - 行号: 222
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _perform_check 过长(71行)
  - 文件: src\monitoring\health_checker.py
  - 行号: 301
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _perform_check 过长(73行)
  - 文件: src\monitoring\health_checker.py
  - 行号: 382
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _process_check_result 过长(66行)
  - 文件: src\monitoring\health_checker.py
  - 行号: 788
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(933行)，可能违反单一职责原则
  - 文件: src\monitoring\logging_monitoring_service.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 LoggingMonitoringService 有太多方法(25)，可能违反单一职责原则
  - 文件: src\monitoring\logging_monitoring_service.py
  - 行号: 117
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 __init__ 过长(52行)
  - 文件: src\monitoring\logging_monitoring_service.py
  - 行号: 126
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 add_log_entry 过长(54行)
  - 文件: src\monitoring\logging_monitoring_service.py
  - 行号: 220
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 get_dashboard_data 过长(72行)
  - 文件: src\monitoring\logging_monitoring_service.py
  - 行号: 488
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _collect_system_metrics 过长(70行)
  - 文件: src\monitoring\logging_monitoring_service.py
  - 行号: 666
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _monitor_task 过长(60行)
  - 文件: src\monitoring\task_monitor.py
  - 行号: 216
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 build 过长(57行)
  - 文件: src\repositories\base_repository.py
  - 行号: 182
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(608行)，可能违反单一职责原则
  - 文件: src\repositories\execution_repository.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(919行)，可能违反单一职责原则
  - 文件: src\repositories\sqlite_task_repository.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(555行)，可能违反单一职责原则
  - 文件: src\repositories\task_repository.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 _task_to_row 过长(57行)
  - 文件: src\repositories\task_repository.py
  - 行号: 107
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(993行)，可能违反单一职责原则
  - 文件: src\services\base_async_service.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(1171行)，可能违反单一职责原则
  - 文件: src\services\event_bus.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(834行)，可能违反单一职责原则
  - 文件: src\ui\monitoring_dashboard.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 create_overview_tab 过长(55行)
  - 文件: src\ui\monitoring_dashboard.py
  - 行号: 572
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 update_dashboard 过长(70行)
  - 文件: src\ui\monitoring_dashboard.py
  - 行号: 752
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(561行)，可能违反单一职责原则
  - 文件: src\utils\helpers.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **INFO**: 函数 get_system_info 过长(58行)
  - 文件: src\utils\helpers.py
  - 行号: 150
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_backup 过长(54行)
  - 文件: src\utils\helpers.py
  - 行号: 428
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(745行)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_model.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 AutomationSettingsModel 有太多方法(80)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_model.py
  - 行号: 14
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 load_settings 过长(52行)
  - 文件: src\ui\automation_settings\automation_settings_model.py
  - 行号: 462
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 reset_to_defaults 过长(54行)
  - 文件: src\ui\automation_settings\automation_settings_model.py
  - 行号: 547
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 AutomationSettingsMVP 有太多方法(53)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_mvp.py
  - 行号: 15
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 AutomationSettingsPresenter 有太多方法(26)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_presenter.py
  - 行号: 16
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _apply_imported_settings 过长(90行)
  - 文件: src\ui\automation_settings\automation_settings_presenter.py
  - 行号: 299
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(822行)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 AutomationSettingsView 有太多方法(51)，可能违反单一职责原则
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 20
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 create_operation_tab 过长(106行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 109
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_safety_tab 过长(84行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 217
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_performance_tab 过长(88行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 303
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_task_tab 过长(98行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 393
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 connect_signals 过长(61行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 512
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 get_current_values 过长(52行)
  - 文件: src\ui\automation_settings\automation_settings_view.py
  - 行号: 763
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 create_button_layout 过长(55行)
  - 文件: src\ui\common\ui_components.py
  - 行号: 152
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 GameSettingsModel 有太多方法(36)，可能违反单一职责原则
  - 文件: src\ui\game_settings\game_settings_model.py
  - 行号: 14
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 GameSettingsMVP 有太多方法(47)，可能违反单一职责原则
  - 文件: src\ui\game_settings\game_settings_mvp.py
  - 行号: 16
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 GameSettingsPresenter 有太多方法(33)，可能违反单一职责原则
  - 文件: src\ui\game_settings\game_settings_presenter.py
  - 行号: 14
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 GameSettingsView 有太多方法(31)，可能违反单一职责原则
  - 文件: src\ui\game_settings\game_settings_view.py
  - 行号: 19
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 LogViewerModel 有太多方法(29)，可能违反单一职责原则
  - 文件: src\ui\log_viewer\log_viewer_model.py
  - 行号: 111
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 LogViewerMVP 有太多方法(42)，可能违反单一职责原则
  - 文件: src\ui\log_viewer\log_viewer_mvp.py
  - 行号: 15
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 LogViewerPresenter 有太多方法(38)，可能违反单一职责原则
  - 文件: src\ui\log_viewer\log_viewer_presenter.py
  - 行号: 12
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(640行)，可能违反单一职责原则
  - 文件: src\ui\log_viewer\log_viewer_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 LogViewerView 有太多方法(41)，可能违反单一职责原则
  - 文件: src\ui\log_viewer\log_viewer_view.py
  - 行号: 91
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _create_control_panel 过长(78行)
  - 文件: src\ui\log_viewer\log_viewer_view.py
  - 行号: 242
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 MainWindowModel 有太多方法(25)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_model.py
  - 行号: 19
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 MainWindowMVP 有太多方法(45)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_mvp.py
  - 行号: 23
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(585行)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_presenter.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 MainWindowPresenter 有太多方法(45)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_presenter.py
  - 行号: 22
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(670行)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 MainWindowView 有太多方法(38)，可能违反单一职责原则
  - 文件: src\ui\main_window\main_window_view.py
  - 行号: 27
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _create_left_panel 过长(71行)
  - 文件: src\ui\main_window\main_window_view.py
  - 行号: 141
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 BasePresenter 有太多方法(24)，可能违反单一职责原则
  - 文件: src\ui\mvp\base_presenter.py
  - 行号: 26
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 BaseView 有太多方法(23)，可能违反单一职责原则
  - 文件: src\ui\mvp\base_view.py
  - 行号: 26
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 TaskCreationModel 有太多方法(23)，可能违反单一职责原则
  - 文件: src\ui\task_creation\task_creation_model.py
  - 行号: 18
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 load_task_for_edit 过长(61行)
  - 文件: src\ui\task_creation\task_creation_model.py
  - 行号: 212
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(506行)，可能违反单一职责原则
  - 文件: src\ui\task_creation\task_creation_presenter.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskCreationPresenter 有太多方法(24)，可能违反单一职责原则
  - 文件: src\ui\task_creation\task_creation_presenter.py
  - 行号: 21
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(668行)，可能违反单一职责原则
  - 文件: src\ui\task_creation\task_creation_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskCreationView 有太多方法(27)，可能违反单一职责原则
  - 文件: src\ui\task_creation\task_creation_view.py
  - 行号: 40
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _setup_ui 过长(54行)
  - 文件: src\ui\task_creation\task_creation_view.py
  - 行号: 70
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _connect_internal_signals 过长(71行)
  - 文件: src\ui\task_creation\task_creation_view.py
  - 行号: 320
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 TaskExecutionHistoryMVP 有太多方法(37)，可能违反单一职责原则
  - 文件: src\ui\task_execution_history\task_execution_history_mvp.py
  - 行号: 18
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 TaskExecutionHistoryPresenter 有太多方法(37)，可能违反单一职责原则
  - 文件: src\ui\task_execution_history\task_execution_history_presenter.py
  - 行号: 16
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(519行)，可能违反单一职责原则
  - 文件: src\ui\task_execution_history\task_execution_history_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskExecutionHistoryView 有太多方法(21)，可能违反单一职责原则
  - 文件: src\ui\task_execution_history\task_execution_history_view.py
  - 行号: 36
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 display_execution_records 过长(59行)
  - 文件: src\ui\task_execution_history\task_execution_history_view.py
  - 行号: 290
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 display_execution_details 过长(53行)
  - 文件: src\ui\task_execution_history\task_execution_history_view.py
  - 行号: 351
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 类 TaskListModel 有太多方法(25)，可能违反单一职责原则
  - 文件: src\ui\task_list\task_list_model.py
  - 行号: 15
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 TaskListMVP 有太多方法(35)，可能违反单一职责原则
  - 文件: src\ui\task_list\task_list_mvp.py
  - 行号: 17
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 类 TaskListPresenter 有太多方法(42)，可能违反单一职责原则
  - 文件: src\ui\task_list\task_list_presenter.py
  - 行号: 15
  - 建议: 考虑将类拆分为多个更小的类

- **WARNING**: 文件过长(828行)，可能违反单一职责原则
  - 文件: src\ui\task_list\task_list_view.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 类 TaskListView 有太多方法(36)，可能违反单一职责原则
  - 文件: src\ui\task_list\task_list_view.py
  - 行号: 22
  - 建议: 考虑将类拆分为多个更小的类

- **INFO**: 函数 _create_button_area 过长(121行)
  - 文件: src\ui\task_list\task_list_view.py
  - 行号: 162
  - 建议: 考虑将函数拆分为多个更小的函数

- **INFO**: 函数 _show_task_details 过长(51行)
  - 文件: src\ui\task_list\task_list_view.py
  - 行号: 601
  - 建议: 考虑将函数拆分为多个更小的函数

- **WARNING**: 文件过长(525行)，可能违反单一职责原则
  - 文件: src\interfaces\infrastructure\messaging_interface.py
  - 建议: 考虑将文件拆分为多个更小的模块

- **WARNING**: 文件过长(675行)，可能违反单一职责原则
  - 文件: src\interfaces\infrastructure\security_interface.py
  - 建议: 考虑将文件拆分为多个更小的模块

### Architecture Pattern

- **WARNING**: UI组件 common 缺少完整的MVP结构
  - 文件: src\ui\common
  - 建议: 确保每个UI组件都有对应的View和Presenter

- **WARNING**: UI组件 __pycache__ 缺少完整的MVP结构
  - 文件: src\ui\__pycache__
  - 建议: 确保每个UI组件都有对应的View和Presenter
