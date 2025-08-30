import { TaskExecutor, TaskResult } from './TaskExecutor';
import { SceneDetector } from './SceneDetector';
import { InputController } from './InputController';
import { ImageRecognition } from './ImageRecognition';
import { GameDetector } from './GameDetector';
import { GameScene } from './TemplateManager';
import { TaskConditionManager, TaskCondition, ConditionType } from './TaskConditionManager';

/**
 * 每日委托任务配置
 */
export interface DailyCommissionConfig {
  autoClaimRewards: boolean;
  autoStartCommissions: boolean;
  maxCommissions: number;
  waitTimeout: number;
}

/**
 * 每日委托任务执行器
 * 负责自动完成每日委托相关任务
 */
export class DailyCommissionTask extends TaskExecutor {
  private sceneDetector: SceneDetector;
  private inputController: InputController;
  private imageRecognition: ImageRecognition;
  private gameDetector: GameDetector;
  private taskConfig: DailyCommissionConfig;

  constructor(
    sceneDetector: SceneDetector,
    inputController: InputController,
    imageRecognition: ImageRecognition,
    gameDetector: GameDetector,
    config: Partial<DailyCommissionConfig> = {},
    conditionManager?: TaskConditionManager
  ) {
    // 定义每日委托任务的执行条件
    const taskConditions: TaskCondition[] = [
      {
        type: ConditionType.GAME_STATE,
        gameRunning: true,
        description: '游戏必须正在运行'
      },
      {
        type: ConditionType.TIME,
        allowedHours: [6, 7, 8, 9, 10, 11, 18, 19, 20, 21, 22, 23], // 早上6-11点，晚上6-11点
        description: '只在适合游戏的时间段执行'
      },
      {
        type: ConditionType.RESOURCE,
        minCpuAvailable: 30,
        maxNetworkLatency: 200,
        description: '系统资源充足'
      }
    ];

    super('DailyCommission', {
      maxRetries: 2,
      retryDelay: 2000,
      timeout: 120000, // 2分钟超时
      enableLogging: true,
      conditions: taskConditions
    }, conditionManager);

    this.sceneDetector = sceneDetector;
    this.inputController = inputController;
    this.imageRecognition = imageRecognition;
    this.gameDetector = gameDetector;
    
    this.taskConfig = {
      autoClaimRewards: true,
      autoStartCommissions: false,
      maxCommissions: 4,
      waitTimeout: 10000,
      ...config
    };
  }

  /**
   * 获取预估执行时间（毫秒）
   */
  getEstimatedTime(): number {
    return 60000; // 预估1分钟
  }

  /**
   * 检查任务是否可以执行
   */
  async canExecute(): Promise<boolean> {
    try {
      // 检查游戏是否运行
      const gameRunning = await this.gameDetector.isGameRunning();
      if (!gameRunning) {
        this.logError('游戏未运行');
        return false;
      }

      // 检查游戏窗口是否激活
      const windowActive = this.gameDetector.isGameActive();
      if (!windowActive) {
        this.logError('游戏窗口未激活');
        return false;
      }

      // Scene detector is always ready in current implementation

      return true;
    } catch (error) {
      this.logError('检查执行条件失败', error);
      return false;
    }
  }

  /**
   * 执行每日委托任务
   */
  protected async executeTask(): Promise<TaskResult> {
    const startTime = Date.now();
    const steps: string[] = [];
    const errors: string[] = [];

    try {
      this.log('开始执行每日委托任务');

      // 步骤1: 导航到主界面
      steps.push('导航到主界面');
      await this.navigateToMainMenu();
      this.log('已导航到主界面');

      // 步骤2: 打开委托界面
      steps.push('打开委托界面');
      await this.openCommissionPanel();
      this.log('已打开委托界面');

      // 步骤3: 领取奖励
      if (this.taskConfig.autoClaimRewards) {
        steps.push('领取委托奖励');
        const claimResult = await this.claimCommissionRewards();
        if (claimResult.claimed > 0) {
          this.log(`成功领取 ${claimResult.claimed} 个委托奖励`);
        }
      }

      // 步骤4: 开始新委托（可选）
      if (this.taskConfig.autoStartCommissions) {
        steps.push('开始新委托');
        const startResult = await this.startNewCommissions();
        if (startResult.started > 0) {
          this.log(`成功开始 ${startResult.started} 个新委托`);
        }
      }

      // 步骤5: 返回主界面
      steps.push('返回主界面');
      await this.returnToMainMenu();
      this.log('已返回主界面');

      const executionTime = Date.now() - startTime;
      return {
        success: true,
        message: '每日委托任务执行完成',
        executionTime,
        data: {
          steps,
          config: this.taskConfig
        }
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      errors.push(errorMessage);
      this.logError('每日委托任务执行失败', error);

      return {
        success: false,
        message: `每日委托任务执行失败: ${errorMessage}`,
        executionTime: Date.now() - startTime,
        errors,
        data: {
          steps,
          failedAt: steps[steps.length - 1]
        }
      };
    }
  }

  /**
   * 导航到主界面
   */
  private async navigateToMainMenu(): Promise<void> {
    const currentScene = await this.sceneDetector.detectCurrentScene();
    
    if (currentScene.scene === GameScene.MAIN_MENU) {
      this.logDebug('已在主界面');
      return;
    }

    // 尝试按ESC键返回主界面
    await this.inputController.pressKey('Escape');
    await this.delayMs(1000);

    // 等待场景切换到主界面
    const success = await this.sceneDetector.waitForScene(GameScene.MAIN_MENU, this.taskConfig.waitTimeout);
    if (!success) {
      throw new Error('无法导航到主界面');
    }
  }

  /**
   * 打开委托界面
   */
  private async openCommissionPanel(): Promise<void> {
    // 查找委托按钮
    const commissionButton = await this.imageRecognition.findImage('commission_button');
    if (!commissionButton.found) {
      throw new Error('未找到委托按钮');
    }

    // 点击委托按钮
    await this.inputController.click(commissionButton.location.x, commissionButton.location.y);
    await this.delayMs(2000);

    // 等待委托界面加载
    const success = await this.sceneDetector.waitForScene(GameScene.COMMISSION, this.taskConfig.waitTimeout);
    if (!success) {
      throw new Error('委托界面加载失败');
    }
  }

  /**
   * 领取委托奖励
   */
  private async claimCommissionRewards(): Promise<{ claimed: number }> {
    let claimed = 0;
    const maxAttempts = this.taskConfig.maxCommissions;

    for (let i = 0; i < maxAttempts; i++) {
      // 查找可领取的奖励按钮
      const claimButton = await this.imageRecognition.findImage('claim_reward_button');
      if (!claimButton.found) {
        this.logDebug('未找到可领取的奖励');
        break;
      }

      // 点击领取按钮
      await this.inputController.click(claimButton.location.x, claimButton.location.y);
      await this.delayMs(1000);

      // 检查是否有确认对话框
      const confirmButton = await this.imageRecognition.findImage('confirm_button');
      if (confirmButton.found) {
        await this.inputController.click(confirmButton.location.x, confirmButton.location.y);
        await this.delayMs(1000);
      }

      claimed++;
      this.logDebug(`已领取第 ${claimed} 个奖励`);

      // 等待界面更新
      await this.delayMs(1000);
    }

    return { claimed };
  }

  /**
   * 开始新委托
   */
  private async startNewCommissions(): Promise<{ started: number }> {
    let started = 0;
    const maxAttempts = this.taskConfig.maxCommissions;

    for (let i = 0; i < maxAttempts; i++) {
      // 查找可开始的委托
      const startButton = await this.imageRecognition.findImage('start_commission_button');
      if (!startButton.found) {
        this.logDebug('未找到可开始的委托');
        break;
      }

      // 点击开始按钮
      await this.inputController.click(startButton.location.x, startButton.location.y);
      await this.delayMs(1000);

      // 检查是否有确认对话框
      const confirmButton = await this.imageRecognition.findImage('confirm_button');
      if (confirmButton.found) {
        await this.inputController.click(confirmButton.location.x, confirmButton.location.y);
        await this.delayMs(1000);
      }

      started++;
      this.logDebug(`已开始第 ${started} 个委托`);

      // 等待界面更新
      await this.delayMs(1000);
    }

    return { started };
  }

  /**
   * 返回主界面
   */
  private async returnToMainMenu(): Promise<void> {
    // 查找返回按钮
    const backButton = await this.imageRecognition.findImage('back_button');
    if (backButton.found) {
      await this.inputController.click(backButton.location.x, backButton.location.y);
    } else {
      // 如果没有找到返回按钮，尝试按ESC键
      await this.inputController.pressKey('Escape');
    }

    await this.delayMs(1000);

    // 等待返回主界面
    const success = await this.sceneDetector.waitForScene(GameScene.MAIN_MENU, this.taskConfig.waitTimeout);
    if (!success) {
      throw new Error('无法返回主界面');
    }
  }

  /**
   * 延迟函数
   */
  private async delayMs(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 更新任务配置
   */
  updateConfig(config: Partial<DailyCommissionConfig>): void {
    this.taskConfig = { ...this.taskConfig, ...config };
    this.log('任务配置已更新');
  }

  /**
   * 获取任务配置
   */
  getConfig(): DailyCommissionConfig {
    return { ...this.taskConfig };
  }
}