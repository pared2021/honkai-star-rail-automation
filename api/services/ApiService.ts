// API服务
export class ApiService {
  constructor() {
    // 初始化API服务
  }

  async getRunningTasks() {
    // 获取运行中的任务
    return [];
  }

  async startTask(taskRequest: any) {
    // 启动任务
    return {
      id: Date.now().toString(),
      ...taskRequest,
      status: 'running',
      createdAt: new Date().toISOString()
    };
  }

  async controlTask(request: { taskId: string; action: string }) {
    // 控制任务
    // TODO: 实现任务控制逻辑，使用 request.taskId 和 request.action
    return true;
  }
}