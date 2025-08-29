// API服务
export class ApiService {
    constructor() {
        // 初始化API服务
    }
    async getRunningTasks() {
        // 获取运行中的任务
        return [];
    }
    async startTask(taskRequest) {
        // 启动任务
        return {
            id: Date.now().toString(),
            ...taskRequest,
            status: 'running',
            createdAt: new Date().toISOString()
        };
    }
    async controlTask(request) {
        // 控制任务
        return true;
    }
}
