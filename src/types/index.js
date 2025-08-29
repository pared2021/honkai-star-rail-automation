// 核心类型定义
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
