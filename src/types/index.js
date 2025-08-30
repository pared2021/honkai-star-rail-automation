// 核心类型定义
// 任务优先级枚举
export var TaskPriority;
(function (TaskPriority) {
    TaskPriority[TaskPriority["LOW"] = 1] = "LOW";
    TaskPriority[TaskPriority["NORMAL"] = 2] = "NORMAL";
    TaskPriority[TaskPriority["HIGH"] = 3] = "HIGH";
    TaskPriority[TaskPriority["URGENT"] = 4] = "URGENT";
})(TaskPriority || (TaskPriority = {}));
// 任务相关类型
export var TaskType;
(function (TaskType) {
    TaskType["DAILY"] = "daily";
    TaskType["MAIN"] = "main";
    TaskType["SIDE"] = "side";
    TaskType["CUSTOM"] = "custom";
    TaskType["EVENT"] = "event";
    TaskType["WEEKLY"] = "weekly";
})(TaskType || (TaskType = {}));
