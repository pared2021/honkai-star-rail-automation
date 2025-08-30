import { Logger } from '../utils/Logger';
import { GameDetector } from './GameDetector';

/**
 * 任务执行条件类型
 */
export enum ConditionType {
  TIME = 'time',
  RESOURCE = 'resource',
  GAME_STATE = 'game_state',
  CUSTOM = 'custom',
  DEPENDENCY = 'dependency'
}

/**
 * 条件检查结果
 */
export interface ConditionResult {
  satisfied: boolean;
  message: string;
  data?: any;
}

/**
 * 时间条件配置
 */
export interface TimeCondition {
  type: ConditionType.TIME;
  startTime?: string; // HH:MM 格式
  endTime?: string; // HH:MM 格式
  daysOfWeek?: number[]; // 0-6，0为周日
  cooldownMinutes?: number; // 冷却时间（分钟）
  lastExecuted?: Date;
}

/**
 * 资源条件配置
 */
export interface ResourceCondition {
  type: ConditionType.RESOURCE;
  minCpuAvailable?: number; // 最小可用CPU百分比
  minMemoryAvailable?: number; // 最小可用内存百分比
  maxNetworkLatency?: number; // 最大网络延迟（毫秒）
  minDiskSpace?: number; // 最小磁盘空间（MB）
}

/**
 * 游戏状态条件配置
 */
export interface GameStateCondition {
  type: ConditionType.GAME_STATE;
  gameRunning: boolean;
  sceneRequired?: string; // 需要的场景
  levelRequired?: number; // 需要的等级
  energyRequired?: number; // 需要的体力
  itemsRequired?: { id: string; count: number }[]; // 需要的物品
}

/**
 * 自定义条件配置
 */
export interface CustomCondition {
  type: ConditionType.CUSTOM;
  name: string;
  checker: () => Promise<ConditionResult>;
}

/**
 * 依赖条件配置
 */
export interface DependencyCondition {
  type: ConditionType.DEPENDENCY;
  taskIds: string[];
  requireAll?: boolean; // 是否需要所有依赖都完成
}

/**
 * 任务执行条件联合类型
 */
export type TaskCondition = 
  | TimeCondition 
  | ResourceCondition 
  | GameStateCondition 
  | CustomCondition 
  | DependencyCondition;

/**
 * 条件组合逻辑
 */
export enum ConditionLogic {
  AND = 'and', // 所有条件都必须满足
  OR = 'or',   // 任一条件满足即可
  NOT = 'not'  // 条件不满足时才执行
}

/**
 * 条件组配置
 */
export interface ConditionGroup {
  logic: ConditionLogic;
  conditions: TaskCondition[];
}

/**
 * 任务条件管理器
 */
export class TaskConditionManager {
  private logger: Logger;
  private gameDetector: GameDetector;
  private completedTasks: Set<string> = new Set();
  private taskExecutionHistory: Map<string, Date> = new Map();

  constructor(gameDetector: GameDetector) {
    this.logger = Logger.getInstance();
    this.gameDetector = gameDetector;
  }

  /**
   * 检查任务是否满足执行条件
   */
  async checkConditions(
    taskId: string,
    conditions: TaskCondition[] | ConditionGroup
  ): Promise<ConditionResult> {
    try {
      if (Array.isArray(conditions)) {
        // 简单条件数组，默认使用AND逻辑
        return await this.checkConditionArray(conditions);
      } else {
        // 条件组
        return await this.checkConditionGroup(conditions);
      }
    } catch (error) {
      this.logger.error(`条件检查失败: ${error}`);
      return {
        satisfied: false,
        message: `条件检查出错: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }

  /**
   * 检查条件数组
   */
  private async checkConditionArray(conditions: TaskCondition[]): Promise<ConditionResult> {
    const results: ConditionResult[] = [];

    for (const condition of conditions) {
      const result = await this.checkSingleCondition(condition);
      results.push(result);

      if (!result.satisfied) {
        return {
          satisfied: false,
          message: `条件不满足: ${result.message}`,
          data: { failedCondition: condition, allResults: results }
        };
      }
    }

    return {
      satisfied: true,
      message: '所有条件都满足',
      data: { results }
    };
  }

  /**
   * 检查条件组
   */
  private async checkConditionGroup(group: ConditionGroup): Promise<ConditionResult> {
    const results: ConditionResult[] = [];

    for (const condition of group.conditions) {
      const result = await this.checkSingleCondition(condition);
      results.push(result);
    }

    let satisfied: boolean;
    let message: string;

    switch (group.logic) {
      case ConditionLogic.AND:
        satisfied = results.every(r => r.satisfied);
        message = satisfied ? '所有条件都满足' : '存在不满足的条件';
        break;

      case ConditionLogic.OR:
        satisfied = results.some(r => r.satisfied);
        message = satisfied ? '至少一个条件满足' : '没有条件满足';
        break;

      case ConditionLogic.NOT:
        satisfied = !results.every(r => r.satisfied);
        message = satisfied ? '条件不满足（符合NOT逻辑）' : '所有条件都满足（不符合NOT逻辑）';
        break;

      default:
        satisfied = false;
        message = '未知的条件逻辑';
    }

    return {
      satisfied,
      message,
      data: { logic: group.logic, results }
    };
  }

  /**
   * 检查单个条件
   */
  private async checkSingleCondition(condition: TaskCondition): Promise<ConditionResult> {
    switch (condition.type) {
      case ConditionType.TIME:
        return await this.checkTimeCondition(condition);

      case ConditionType.RESOURCE:
        return await this.checkResourceCondition(condition);

      case ConditionType.GAME_STATE:
        return await this.checkGameStateCondition(condition);

      case ConditionType.CUSTOM:
        return await this.checkCustomCondition(condition);

      case ConditionType.DEPENDENCY:
        return await this.checkDependencyCondition(condition);

      default:
        return {
          satisfied: false,
          message: '未知的条件类型'
        };
    }
  }

  /**
   * 检查时间条件
   */
  private async checkTimeCondition(condition: TimeCondition): Promise<ConditionResult> {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    const currentDay = now.getDay();

    // 检查星期几
    if (condition.daysOfWeek && !condition.daysOfWeek.includes(currentDay)) {
      return {
        satisfied: false,
        message: `当前星期${currentDay}不在允许的执行日期内`
      };
    }

    // 检查时间范围
    if (condition.startTime || condition.endTime) {
      const startMinutes = condition.startTime ? this.parseTime(condition.startTime) : 0;
      const endMinutes = condition.endTime ? this.parseTime(condition.endTime) : 24 * 60;

      if (currentTime < startMinutes || currentTime > endMinutes) {
        return {
          satisfied: false,
          message: `当前时间${this.formatTime(currentTime)}不在允许的执行时间范围内`
        };
      }
    }

    // 检查冷却时间
    if (condition.cooldownMinutes && condition.lastExecuted) {
      const timeSinceLastExecution = now.getTime() - condition.lastExecuted.getTime();
      const cooldownMs = condition.cooldownMinutes * 60 * 1000;

      if (timeSinceLastExecution < cooldownMs) {
        const remainingMinutes = Math.ceil((cooldownMs - timeSinceLastExecution) / 60000);
        return {
          satisfied: false,
          message: `冷却时间未结束，还需等待${remainingMinutes}分钟`
        };
      }
    }

    return {
      satisfied: true,
      message: '时间条件满足'
    };
  }

  /**
   * 检查资源条件
   */
  private async checkResourceCondition(condition: ResourceCondition): Promise<ConditionResult> {
    // 模拟系统资源检查
    const systemResources = await this.getSystemResources();

    if (condition.minCpuAvailable && systemResources.cpuAvailable < condition.minCpuAvailable) {
      return {
        satisfied: false,
        message: `CPU可用率不足，当前${systemResources.cpuAvailable}%，需要${condition.minCpuAvailable}%`
      };
    }

    if (condition.minMemoryAvailable && systemResources.memoryAvailable < condition.minMemoryAvailable) {
      return {
        satisfied: false,
        message: `内存可用率不足，当前${systemResources.memoryAvailable}%，需要${condition.minMemoryAvailable}%`
      };
    }

    if (condition.maxNetworkLatency && systemResources.networkLatency > condition.maxNetworkLatency) {
      return {
        satisfied: false,
        message: `网络延迟过高，当前${systemResources.networkLatency}ms，最大允许${condition.maxNetworkLatency}ms`
      };
    }

    return {
      satisfied: true,
      message: '资源条件满足'
    };
  }

  /**
   * 检查游戏状态条件
   */
  private async checkGameStateCondition(condition: GameStateCondition): Promise<ConditionResult> {
    // 检查游戏是否运行
    const gameRunning = this.gameDetector.isGameRunning();
    if (condition.gameRunning && !gameRunning) {
      return {
        satisfied: false,
        message: '游戏未运行'
      };
    }

    if (!condition.gameRunning && gameRunning) {
      return {
        satisfied: false,
        message: '游戏正在运行，但条件要求游戏不运行'
      };
    }

    // 检查场景（如果游戏运行）
    if (gameRunning && condition.sceneRequired) {
      // 这里需要实现场景检测逻辑
      // const currentScene = await this.gameDetector.getCurrentScene();
      // if (currentScene !== condition.sceneRequired) {
      //   return {
      //     satisfied: false,
      //     message: `当前场景${currentScene}不符合要求的场景${condition.sceneRequired}`
      //   };
      // }
    }

    return {
      satisfied: true,
      message: '游戏状态条件满足'
    };
  }

  /**
   * 检查自定义条件
   */
  private async checkCustomCondition(condition: CustomCondition): Promise<ConditionResult> {
    try {
      return await condition.checker();
    } catch (error) {
      return {
        satisfied: false,
        message: `自定义条件检查失败: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }

  /**
   * 检查依赖条件
   */
  private async checkDependencyCondition(condition: DependencyCondition): Promise<ConditionResult> {
    const completedCount = condition.taskIds.filter(id => this.completedTasks.has(id)).length;
    const requiredCount = condition.requireAll ? condition.taskIds.length : 1;

    if (completedCount >= requiredCount) {
      return {
        satisfied: true,
        message: `依赖条件满足，已完成${completedCount}/${condition.taskIds.length}个依赖任务`
      };
    } else {
      return {
        satisfied: false,
        message: `依赖条件不满足，已完成${completedCount}/${condition.taskIds.length}个依赖任务，需要${requiredCount}个`
      };
    }
  }

  /**
   * 标记任务为已完成
   */
  markTaskCompleted(taskId: string): void {
    this.completedTasks.add(taskId);
    this.taskExecutionHistory.set(taskId, new Date());
  }

  /**
   * 获取系统资源信息
   */
  private async getSystemResources(): Promise<{
    cpuAvailable: number;
    memoryAvailable: number;
    networkLatency: number;
    diskSpace: number;
  }> {
    // 模拟系统资源获取
    return {
      cpuAvailable: 100 - Math.random() * 50, // 50-100%
      memoryAvailable: 100 - Math.random() * 40, // 60-100%
      networkLatency: Math.random() * 100, // 0-100ms
      diskSpace: 1000 + Math.random() * 9000 // 1-10GB
    };
  }

  /**
   * 解析时间字符串（HH:MM）为分钟数
   */
  private parseTime(timeStr: string): number {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
  }

  /**
   * 格式化分钟数为时间字符串
   */
  private formatTime(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
  }

  /**
   * 清理历史记录
   */
  clearHistory(): void {
    this.completedTasks.clear();
    this.taskExecutionHistory.clear();
  }
}