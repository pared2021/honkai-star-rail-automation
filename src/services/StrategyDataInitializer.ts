import { DatabaseService } from './DatabaseService.js';
import { TaskInfo, TaskType } from '../types/index.js';
import fs from 'fs';
import path from 'path';

// 步骤数据接口
interface StepData {
  description: string;
  action?: Record<string, unknown>;
  timeout?: number;
  retryCount?: number;
  isOptional?: boolean;
}

export interface PresetStrategyData {
  taskId: string;
  taskName: string;
  taskType: 'main' | 'side' | 'daily';
  strategies: {
    id: string;
    name: string;
    description: string;
    steps: string[];
    successRate: number;
    averageTime: number;
    difficulty: 'easy' | 'medium' | 'hard';
    requirements: string[];
    tips: string[];
    resources: {
      energy?: number;
      materials?: string[];
      characters?: string[];
    };
  }[];
}

export class StrategyDataInitializer {
  private db: DatabaseService;
  private dataPath: string;

  constructor(db: DatabaseService) {
    this.db = db;
    this.dataPath = path.join(process.cwd(), 'data', 'preset-strategies.json');
  }

  /**
   * 检查是否需要初始化预置攻略数据
   */
  async needsInitialization(): Promise<boolean> {
    try {
      // 检查数据库中是否已有预置攻略数据
      const existingStrategies = await this.db.getStrategies();
      const presetStrategies = existingStrategies.filter(s => s.author === 'preset');
      
      // 如果没有预置攻略或数量少于预期，则需要初始化
      return presetStrategies.length === 0;
    } catch (error) {
      console.error('检查初始化状态失败:', error);
      return true;
    }
  }

  /**
   * 加载预置攻略数据文件
   */
  private async loadPresetData(): Promise<PresetStrategyData[]> {
    try {
      if (!fs.existsSync(this.dataPath)) {
        console.warn(`预置攻略数据文件不存在: ${this.dataPath}`);
        return [];
      }

      const fileContent = fs.readFileSync(this.dataPath, 'utf-8');
      const data = JSON.parse(fileContent) as PresetStrategyData[];
      
      console.log(`成功加载 ${data.length} 个预置任务的攻略数据`);
      return data;
    } catch (error) {
      console.error('加载预置攻略数据失败:', error);
      return [];
    }
  }

  /**
   * 初始化预置攻略数据
   */
  async initializePresetData(): Promise<void> {
    try {
      console.log('开始初始化预置攻略数据...');
      
      const presetData = await this.loadPresetData();
      if (presetData.length === 0) {
        console.log('没有找到预置攻略数据，跳过初始化');
        return;
      }

      let importedCount = 0;
      let errorCount = 0;

      for (const taskData of presetData) {
        try {
          // 检查任务是否已存在
          const allTaskInfos = await this.db.getTaskInfos();
          let taskInfo = allTaskInfos.find(t => t.id === taskData.taskId);
          let taskInfoId = taskData.taskId;
          
          // 如果任务不存在，创建任务信息
          if (!taskInfo) {
            const newTaskInfo: TaskInfo = {
                id: taskData.taskId,
                taskName: taskData.taskName,
                taskType: taskData.taskType as TaskType,
                name: taskData.taskName, // 别名映射
                type: taskData.taskType as TaskType, // 别名映射
                description: `预置任务: ${taskData.taskName}`,
                prerequisites: [],
                rewards: [],
                difficulty: 'medium',
                estimatedTime: 30,
                location: '',
                npcName: '',
                chapter: '',
                questLine: '',
                isRepeatable: false,
                collectTime: new Date(),
                lastUpdated: new Date()
              };
            
            const createdTaskInfo = await this.db.createTaskInfo(newTaskInfo);
            taskInfo = createdTaskInfo;
            taskInfoId = createdTaskInfo.id;
            console.log(`创建预置任务信息: ${taskData.taskName}`);
          }

          if (taskData.strategies && taskData.strategies.length > 0) {
            // 准备攻略数据
            const strategiesToCreate = taskData.strategies.map((strategyData) => ({
              taskInfoId: taskInfoId,
            strategyName: strategyData.name,
            description: strategyData.description,
            steps: strategyData.steps.map((step: string | StepData, index: number) => ({
              id: `${strategyData.name}-step-${index + 1}`,
              strategyId: '', // 将在创建后设置
              stepOrder: index + 1,
              stepType: 'custom' as const,
              description: typeof step === 'string' ? step : step.description,
              action: {
                type: 'custom' as const,
                parameters: typeof step === 'string' ? {} : (step.action || {})
              },
              timeout: typeof step === 'string' ? 30 : (step.timeout || 30),
              retryCount: typeof step === 'string' ? 3 : (step.retryCount || 3),
              isOptional: typeof step === 'string' ? false : (step.isOptional || false)
            })),
            estimatedTime: strategyData.averageTime,
            successRate: strategyData.successRate,
            difficulty: strategyData.difficulty,
            requirements: strategyData.requirements,
            tips: strategyData.tips,
            author: 'preset',
            version: '1.0.0',
            isVerified: true
          }));

          // 批量创建攻略
             const createdStrategies = await this.db.batchCreateStrategies(strategiesToCreate);
             importedCount += createdStrategies.length;

             console.log(`导入任务 ${taskData.taskName} 的 ${taskData.strategies.length} 个攻略`);
           }
        } catch (error) {
          console.error(`导入任务 ${taskData.taskName} 的攻略失败:`, error);
          errorCount++;
        }
      }

      console.log(`预置攻略数据初始化完成: 成功导入 ${importedCount} 个攻略，失败 ${errorCount} 个`);
    } catch (error) {
      console.error('初始化预置攻略数据失败:', error);
      throw error;
    }
  }

  /**
   * 更新预置攻略数据
   */
  async updatePresetData(): Promise<void> {
    try {
      console.log('开始更新预置攻略数据...');
      
      // 删除现有的预置攻略
      await this.db.deleteStrategiesBySource('preset');
      
      // 重新导入
      await this.initializePresetData();
      
      console.log('预置攻略数据更新完成');
    } catch (error) {
      console.error('更新预置攻略数据失败:', error);
      throw error;
    }
  }

  /**
   * 获取预置攻略统计信息
   */
  async getPresetDataStats(): Promise<{
    totalTasks: number;
    totalStrategies: number;
    taskTypes: Record<string, number>;
    difficultyDistribution: Record<string, number>;
  }> {
    try {
      const strategies = await this.db.getStrategies();
      const presetStrategies = strategies.filter(s => s.author === 'preset');
      const taskIds = new Set(presetStrategies.map(s => s.taskInfoId));
      const taskTypes: Record<string, number> = {};
      const difficultyDistribution: Record<string, number> = {};

      // 统计任务类型
      for (const taskId of taskIds) {
        const allTaskInfos = await this.db.getTaskInfos();
         const taskInfo = allTaskInfos.find(t => t.id === taskId);
         if (taskInfo) {
           taskTypes[taskInfo.taskType] = (taskTypes[taskInfo.taskType] || 0) + 1;
        }
      }

      // 统计难度分布
      for (const strategy of presetStrategies) {
        difficultyDistribution[strategy.difficulty] = 
          (difficultyDistribution[strategy.difficulty] || 0) + 1;
      }

      return {
        totalTasks: taskIds.size,
        totalStrategies: presetStrategies.length,
        taskTypes,
        difficultyDistribution
      };
    } catch (error) {
      console.error('获取预置攻略统计信息失败:', error);
      return {
        totalTasks: 0,
        totalStrategies: 0,
        taskTypes: {},
        difficultyDistribution: {}
      };
    }
  }

  /**
   * 验证预置攻略数据的完整性
   */
  async validatePresetData(): Promise<{
    isValid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      const presetData = await this.loadPresetData();
      
      if (presetData.length === 0) {
        warnings.push('没有找到预置攻略数据文件');
        return { isValid: true, errors, warnings };
      }

      for (const taskData of presetData) {
        // 验证任务数据
        if (!taskData.taskId || !taskData.taskName) {
          errors.push(`任务缺少必要字段: ${JSON.stringify(taskData)}`);
          continue;
        }

        if (!['main', 'side', 'daily'].includes(taskData.taskType)) {
          errors.push(`任务 ${taskData.taskName} 的类型无效: ${taskData.taskType}`);
        }

        // 验证攻略数据
        for (const strategy of taskData.strategies) {
          if (!strategy.id || !strategy.name || !strategy.steps || strategy.steps.length === 0) {
            errors.push(`任务 ${taskData.taskName} 的攻略缺少必要字段: ${strategy.name}`);
          }

          if (strategy.successRate < 0 || strategy.successRate > 1) {
            warnings.push(`任务 ${taskData.taskName} 的攻略 ${strategy.name} 成功率超出范围: ${strategy.successRate}`);
          }

          if (strategy.averageTime <= 0) {
            warnings.push(`任务 ${taskData.taskName} 的攻略 ${strategy.name} 平均时间无效: ${strategy.averageTime}`);
          }
        }
      }

      return {
        isValid: errors.length === 0,
        errors,
        warnings
      };
    } catch (error) {
      errors.push(`验证预置攻略数据时发生错误: ${error}`);
      return { isValid: false, errors, warnings };
    }
  }
}