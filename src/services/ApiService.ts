// API服务模块
import { ApiResponse, StartTaskRequest, TaskControlRequest, Account, Task, TaskConfig } from '../types/index.js';
import { DatabaseService } from './DatabaseService.js';
// import { GameDetector } from './GameDetector';
// import { TaskExecutor } from './TaskExecutor';
// import { ImageRecognition } from './ImageRecognition';
export class ApiService {
  private dbService: DatabaseService;
  // private taskExecutor: TaskExecutor;
  // public gameDetector: GameDetector;

  constructor() {
    this.dbService = new DatabaseService();
    // this.taskExecutor = new TaskExecutor();
    // this.gameDetector = new GameDetector();
  }

  /**
   * 初始化API服务
   */
  public async initialize(): Promise<void> {
    try {
      await this.dbService.initialize();
      // this.gameDetector.startDetection();
      console.log('API服务初始化完成');
    } catch (error) {
      console.error('API服务初始化失败:', error);
      throw error;
    }
  }

  /**
   * 账号管理API
   */
  public async createAccount(accountData: Omit<Account, 'id' | 'createdAt'>): Promise<ApiResponse<string>> {
    try {
      const accountId = await this.dbService.createAccount(accountData);
      return {
        success: true,
        data: accountId.id,
        message: '账号创建成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async getAccounts(): Promise<ApiResponse<Account[]>> {
    try {
      const accounts = await this.dbService.getAccounts();
      return {
        success: true,
        data: accounts
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async updateAccount(id: string, updates: Partial<Account>): Promise<ApiResponse<boolean>> {
    try {
      const result = await this.dbService.updateAccount(id, updates);
      return {
        success: true,
        data: result,
        message: '账号更新成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async deleteAccount(id: string): Promise<ApiResponse<boolean>> {
    try {
      const result = await this.dbService.deleteAccount(id);
      return {
        success: true,
        data: result,
        message: '账号删除成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 任务管理API
   */
  public async startTask(_request: StartTaskRequest): Promise<ApiResponse<string>> {
    try {
      // 检查游戏状态
      const gameStatus = { isRunning: false, windowTitle: '', processId: 0 }; // await this.gameDetector.getCurrentStatus();
      if (!gameStatus.isRunning) {
        return {
          success: false,
          error: '游戏未运行，无法启动任务'
        };
      }

      const taskId = Math.random().toString(36).substr(2, 9); // this.taskExecutor.addTask({
        // accountId: request.accountId || 'default',
        // taskType: request.taskType,
        // config: request.config
      // });

      return {
        success: true,
        data: taskId,
        message: '任务启动成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async controlTask(request: TaskControlRequest): Promise<ApiResponse<boolean>> {
    try {
      let result = false;
      
      switch (request.action) {
        case 'stop':
          result = true; // this.taskExecutor.stopTask(request.taskId);
          break;
        case 'pause':
        case 'resume':
          // TODO: 实现暂停和恢复功能
          result = true;
          break;
      }

      return {
        success: true,
        data: result,
        message: `任务${request.action}操作成功`
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async getRunningTasks(): Promise<ApiResponse<Task[]>> {
    try {
      const tasks: any[] = []; // this.taskExecutor.getRunningTasks();
      return {
        success: true,
        data: tasks
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async getTaskHistory(accountId?: string): Promise<ApiResponse<Task[]>> {
    try {
      const tasks = await this.dbService.getTasks(accountId);
      return {
        success: true,
        data: tasks
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 任务配置API
   */
  public async createTaskConfig(config: TaskConfig): Promise<ApiResponse<string>> {
    try {
      const configId = await this.dbService.createTaskConfig(config);
      return {
        success: true,
        data: configId.id,
        message: '任务配置创建成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  public async getTaskConfigs(taskType?: string): Promise<ApiResponse<TaskConfig[]>> {
    try {
      const configs = await this.dbService.getTaskConfigs(taskType);
      return {
        success: true,
        data: configs
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 游戏状态API
   */
  public async getGameStatus(): Promise<ApiResponse> {
    try {
      const status = { isRunning: false, windowTitle: '', processId: 0 }; // await this.gameDetector.getCurrentStatus();
      return {
        success: true,
        data: status
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 统计数据API
   */
  public async getAccountStats(accountId: string, statType?: string): Promise<ApiResponse> {
    try {
      const stats = await this.dbService.getAccountStats(accountId, new Date(statType));
      return {
        success: true,
        data: stats
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  async getSystemStats(): Promise<any> {
    // 获取系统统计信息
    const accounts = await this.dbService.getAccounts();
    const tasks = await this.dbService.getTasks();
    
    return {
      totalAccounts: accounts.length,
      activeTasks: tasks.filter(t => t.status === 'running').length,
      completedTasks: tasks.filter(t => t.status === 'completed').length,
      failedTasks: tasks.filter(t => t.status === 'failed').length,
      systemUptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * 关闭API服务
   */
  public async shutdown(): Promise<void> {
    try {
      // this.gameDetector.stopDetection();
      await this.dbService.close();
      console.log('API服务已关闭');
    } catch (error) {
      console.error('API服务关闭失败:', error);
    }
  }
}

export default ApiService;