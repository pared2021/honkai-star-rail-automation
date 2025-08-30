import sys
sys.path.insert(0, '.')

try:
    from src.core.task_manager import TaskConfig
    print("TaskConfig imported successfully")
except Exception as e:
    print(f"Error importing TaskConfig: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.models.task_model import TaskType, TaskPriority
    print("TaskType and TaskPriority imported successfully")
except Exception as e:
    print(f"Error importing TaskType/TaskPriority: {e}")
    import traceback
    traceback.print_exc()

try:
    config = TaskConfig(
        task_name='test',
        task_type=TaskType.CUSTOM,
        priority=TaskPriority.MEDIUM
    )
    print("TaskConfig created successfully")
except Exception as e:
    print(f"Error creating TaskConfig: {e}")
    import traceback
    traceback.print_exc()