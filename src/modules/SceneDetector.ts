import { TemplateManager, TemplateType, GameScene } from './TemplateManager';
import { ImageRecognition } from './ImageRecognition';
import { EventEmitter } from 'events';

/**
 * 场景检测配置
 */
export interface SceneDetectorConfig {
  /** 检测间隔时间(ms) */
  detectionInterval: number;
  /** 场景识别置信度阈值 */
  confidenceThreshold: number;
  /** 连续检测次数确认场景变化 */
  confirmationCount: number;
  /** 是否启用自动检测 */
  autoDetection: boolean;
  /** 检测超时时间(ms) */
  detectionTimeout: number;
}

/**
 * 场景检测结果
 */
export interface SceneDetectionResult {
  /** 检测到的场景 */
  scene: GameScene;
  /** 检测置信度 */
  confidence: number;
  /** 检测时间戳 */
  timestamp: number;
  /** 匹配的模板信息 */
  matchedTemplates: Array<{
    name: string;
    confidence: number;
    position?: { x: number; y: number };
  }>;
  /** 检测耗时(ms) */
  detectionTime: number;
}

/**
 * 场景变化事件
 */
export interface SceneChangeEvent {
  /** 之前的场景 */
  previousScene: GameScene;
  /** 当前场景 */
  currentScene: GameScene;
  /** 检测结果 */
  detectionResult: SceneDetectionResult;
}

/**
 * 场景检测统计信息
 */
export interface SceneDetectionStats {
  /** 总检测次数 */
  totalDetections: number;
  /** 成功检测次数 */
  successfulDetections: number;
  /** 场景变化次数 */
  sceneChanges: number;
  /** 平均检测时间(ms) */
  averageDetectionTime: number;
  /** 各场景检测次数统计 */
  sceneDetectionCounts: Record<GameScene, number>;
  /** 最后检测时间 */
  lastDetectionTime: number;
}

/**
 * 游戏场景检测器
 * 负责识别当前游戏界面所处的场景状态
 */
export class SceneDetector extends EventEmitter {
  private config: SceneDetectorConfig;
  private templateManager: TemplateManager;
  private imageRecognition: ImageRecognition;
  private currentScene: GameScene = GameScene.UNKNOWN;
  private isDetecting: boolean = false;
  private detectionTimer: NodeJS.Timeout | null = null;
  private confirmationBuffer: GameScene[] = [];
  private stats: SceneDetectionStats;
  private logger: {
    info: (msg: string) => void;
    error: (msg: string, error?: unknown) => void;
    debug: (msg: string) => void;
  };

  constructor(
    templateManager: TemplateManager,
    config?: Partial<SceneDetectorConfig>
  ) {
    super();
    
    this.templateManager = templateManager;
    this.imageRecognition = new ImageRecognition();
    
    this.config = {
      detectionInterval: 1000,
      confidenceThreshold: 0.7,
      confirmationCount: 2,
      autoDetection: false,
      detectionTimeout: 5000,
      ...config
    };

    this.stats = {
      totalDetections: 0,
      successfulDetections: 0,
      sceneChanges: 0,
      averageDetectionTime: 0,
      sceneDetectionCounts: {} as Record<GameScene, number>,
      lastDetectionTime: 0
    };

    // 初始化场景计数器
    Object.values(GameScene).forEach(scene => {
      this.stats.sceneDetectionCounts[scene] = 0;
    });

    this.logger = {
      info: (msg: string) => console.log(`[SceneDetector] ${msg}`),
      error: (msg: string, error?: unknown) => console.error(`[SceneDetector] ${msg}`, error),
      debug: (msg: string) => console.debug(`[SceneDetector] ${msg}`)
    };
  }

  /**
   * 启动场景检测
   */
  async startDetection(): Promise<void> {
    if (this.isDetecting) {
      this.logger.debug('场景检测已在运行中');
      return;
    }

    if (!this.templateManager.isReady()) {
      throw new Error('TemplateManager未初始化，无法启动场景检测');
    }

    this.isDetecting = true;
    this.logger.info('启动场景检测');

    if (this.config.autoDetection) {
      this.startAutoDetection();
    }

    // 立即执行一次检测
    await this.detectCurrentScene();
  }

  /**
   * 停止场景检测
   */
  stopDetection(): void {
    if (!this.isDetecting) {
      return;
    }

    this.isDetecting = false;
    this.stopAutoDetection();
    this.confirmationBuffer = [];
    this.logger.info('停止场景检测');
  }

  /**
   * 启动自动检测
   */
  private startAutoDetection(): void {
    if (this.detectionTimer) {
      clearInterval(this.detectionTimer);
    }

    this.detectionTimer = setInterval(async () => {
      try {
        await this.detectCurrentScene();
      } catch (error) {
        this.logger.error('自动场景检测失败:', error);
      }
    }, this.config.detectionInterval);

    this.logger.debug(`启动自动检测，间隔: ${this.config.detectionInterval}ms`);
  }

  /**
   * 停止自动检测
   */
  private stopAutoDetection(): void {
    if (this.detectionTimer) {
      clearInterval(this.detectionTimer);
      this.detectionTimer = null;
      this.logger.debug('停止自动检测');
    }
  }

  /**
   * 检测当前场景
   */
  async detectCurrentScene(): Promise<SceneDetectionResult> {
    const startTime = Date.now();
    this.stats.totalDetections++;

    try {
      this.logger.debug('开始场景检测...');

      // 获取当前截图
      const screenshot = await this.imageRecognition.captureGameWindow();
      if (!screenshot) {
        throw new Error('无法获取游戏窗口截图');
      }

      // 检测各个场景
      const sceneResults = await this.detectAllScenes(screenshot);
      
      // 选择最佳匹配场景
      const bestMatch = this.selectBestScene(sceneResults);
      
      const detectionTime = Date.now() - startTime;
      const result: SceneDetectionResult = {
        scene: bestMatch.scene,
        confidence: bestMatch.confidence,
        timestamp: Date.now(),
        matchedTemplates: bestMatch.matchedTemplates,
        detectionTime
      };

      // 更新统计信息
      this.updateStats(result);

      // 处理场景变化
      await this.handleSceneChange(result);

      this.logger.debug(`场景检测完成: ${result.scene} (置信度: ${result.confidence.toFixed(3)}, 耗时: ${detectionTime}ms)`);
      
      return result;

    } catch (error) {
      this.logger.error('场景检测失败:', error);
      
      const detectionTime = Date.now() - startTime;
      return {
        scene: GameScene.UNKNOWN,
        confidence: 0,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime
      };
    }
  }

  /**
   * 检测所有可能的场景
   */
  private async detectAllScenes(screenshot: Buffer): Promise<Array<{
    scene: GameScene;
    confidence: number;
    matchedTemplates: Array<{
      name: string;
      confidence: number;
      position?: { x: number; y: number };
    }>;
  }>> {
    const results: Array<{
      scene: GameScene;
      confidence: number;
      matchedTemplates: Array<{
        name: string;
        confidence: number;
        position?: { x: number; y: number };
      }>;
    }> = [];

    // 获取场景模板
    const sceneTemplates = this.templateManager.getTemplatesByType(TemplateType.SCENE);
    
    for (const template of sceneTemplates) {
      if (template.scene && template.scene !== GameScene.UNKNOWN) {
        try {
          const matchResult = await this.imageRecognition.findImage(template.path, screenshot);
          
          if (matchResult.found && matchResult.confidence >= this.config.confidenceThreshold) {
            // 查找该场景的其他相关模板
            const relatedTemplates = await this.findRelatedTemplates(template.scene!, screenshot);
            
            results.push({
              scene: template.scene!,
              confidence: matchResult.confidence,
              matchedTemplates: [
                {
                  name: template.name,
                  confidence: matchResult.confidence,
                  position: matchResult.position
                },
                ...relatedTemplates
              ]
            });
          }
        } catch (error) {
          this.logger.error(`检测场景模板 ${template.name} 失败:`, error);
        }
      }
    }

    return results;
  }

  /**
   * 查找相关模板以提高检测准确性
   */
  private async findRelatedTemplates(
    scene: GameScene, 
    screenshot: Buffer
  ): Promise<Array<{
    name: string;
    confidence: number;
    position?: { x: number; y: number };
  }>> {
    const relatedTemplates: Array<{
      name: string;
      confidence: number;
      position?: { x: number; y: number };
    }> = [];

    // 获取该场景的相关模板
    const sceneTemplates = this.templateManager.getTemplatesByScene(scene);
    
    for (const template of sceneTemplates) {
      if (template.type !== TemplateType.SCENE) {
        try {
          const matchResult = await this.imageRecognition.findImage(template.path, screenshot);
          
          if (matchResult.found && matchResult.confidence >= this.config.confidenceThreshold * 0.8) {
            relatedTemplates.push({
              name: template.name,
              confidence: matchResult.confidence,
              position: matchResult.position
            });
          }
        } catch (error) {
          this.logger.debug(`检测相关模板 ${template.name} 失败: ${error}`);
        }
      }
    }

    return relatedTemplates;
  }

  /**
   * 选择最佳匹配场景
   */
  private selectBestScene(sceneResults: Array<{
    scene: GameScene;
    confidence: number;
    matchedTemplates: Array<{
      name: string;
      confidence: number;
      position?: { x: number; y: number };
    }>;
  }>): {
    scene: GameScene;
    confidence: number;
    matchedTemplates: Array<{
      name: string;
      confidence: number;
      position?: { x: number; y: number };
    }>;
  } {
    if (sceneResults.length === 0) {
      return {
        scene: GameScene.UNKNOWN,
        confidence: 0,
        matchedTemplates: []
      };
    }

    // 计算综合得分（主模板置信度 + 相关模板数量加权）
    const scoredResults = sceneResults.map(result => {
      const baseScore = result.confidence;
      const relatedBonus = result.matchedTemplates.length > 1 ? 
        (result.matchedTemplates.length - 1) * 0.1 : 0;
      const avgRelatedConfidence = result.matchedTemplates.length > 1 ?
        result.matchedTemplates.slice(1).reduce((sum, t) => sum + t.confidence, 0) / (result.matchedTemplates.length - 1) : 0;
      
      return {
        ...result,
        score: baseScore + relatedBonus + avgRelatedConfidence * 0.2
      };
    });

    // 选择得分最高的场景
    const bestResult = scoredResults.reduce((best, current) => 
      current.score > best.score ? current : best
    );

    return {
      scene: bestResult.scene,
      confidence: bestResult.confidence,
      matchedTemplates: bestResult.matchedTemplates
    };
  }

  /**
   * 处理场景变化
   */
  private async handleSceneChange(result: SceneDetectionResult): Promise<void> {
    // 添加到确认缓冲区
    this.confirmationBuffer.push(result.scene);
    
    // 保持缓冲区大小
    if (this.confirmationBuffer.length > this.config.confirmationCount) {
      this.confirmationBuffer.shift();
    }

    // 检查是否需要确认场景变化
    if (this.confirmationBuffer.length === this.config.confirmationCount) {
      const confirmedScene = this.getConfirmedScene();
      
      if (confirmedScene && confirmedScene !== this.currentScene) {
        const previousScene = this.currentScene;
        this.currentScene = confirmedScene;
        this.stats.sceneChanges++;

        const changeEvent: SceneChangeEvent = {
          previousScene,
          currentScene: confirmedScene,
          detectionResult: result
        };

        this.logger.info(`场景变化: ${previousScene} -> ${confirmedScene}`);
        this.emit('sceneChange', changeEvent);
      }
    }
  }

  /**
   * 获取确认的场景
   */
  private getConfirmedScene(): GameScene | null {
    if (this.confirmationBuffer.length < this.config.confirmationCount) {
      return null;
    }

    // 检查缓冲区中是否有足够的一致性
    const sceneCount = new Map<GameScene, number>();
    
    for (const scene of this.confirmationBuffer) {
      sceneCount.set(scene, (sceneCount.get(scene) || 0) + 1);
    }

    // 找到出现次数最多的场景
    let maxCount = 0;
    let confirmedScene: GameScene | null = null;
    
    for (const [scene, count] of sceneCount) {
      if (count > maxCount) {
        maxCount = count;
        confirmedScene = scene;
      }
    }

    // 需要至少一半以上的确认
    const requiredCount = Math.ceil(this.config.confirmationCount / 2);
    return maxCount >= requiredCount ? confirmedScene : null;
  }

  /**
   * 更新统计信息
   */
  private updateStats(result: SceneDetectionResult): void {
    if (result.scene !== GameScene.UNKNOWN) {
      this.stats.successfulDetections++;
    }

    this.stats.sceneDetectionCounts[result.scene]++;
    this.stats.lastDetectionTime = result.timestamp;
    
    // 更新平均检测时间
    const totalTime = this.stats.averageDetectionTime * (this.stats.totalDetections - 1) + result.detectionTime;
    this.stats.averageDetectionTime = totalTime / this.stats.totalDetections;
  }

  /**
   * 获取当前场景
   */
  getCurrentScene(): GameScene {
    return this.currentScene;
  }

  /**
   * 获取检测状态
   */
  isDetectionRunning(): boolean {
    return this.isDetecting;
  }

  /**
   * 获取统计信息
   */
  getStats(): SceneDetectionStats {
    return { ...this.stats };
  }

  /**
   * 重置统计信息
   */
  resetStats(): void {
    this.stats = {
      totalDetections: 0,
      successfulDetections: 0,
      sceneChanges: 0,
      averageDetectionTime: 0,
      sceneDetectionCounts: {} as Record<GameScene, number>,
      lastDetectionTime: 0
    };

    Object.values(GameScene).forEach(scene => {
      this.stats.sceneDetectionCounts[scene] = 0;
    });
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<SceneDetectorConfig>): void {
    const oldAutoDetection = this.config.autoDetection;
    
    this.config = {
      ...this.config,
      ...newConfig
    };

    // 如果自动检测设置发生变化，重新启动
    if (this.isDetecting && oldAutoDetection !== this.config.autoDetection) {
      if (this.config.autoDetection) {
        this.startAutoDetection();
      } else {
        this.stopAutoDetection();
      }
    }

    this.logger.info('场景检测器配置已更新');
  }

  /**
   * 获取配置
   */
  getConfig(): SceneDetectorConfig {
    return { ...this.config };
  }

  /**
   * 手动设置当前场景（用于测试或特殊情况）
   */
  setCurrentScene(scene: GameScene): void {
    const previousScene = this.currentScene;
    this.currentScene = scene;
    
    if (previousScene !== scene) {
      this.stats.sceneChanges++;
      this.logger.info(`手动设置场景: ${previousScene} -> ${scene}`);
      
      const changeEvent: SceneChangeEvent = {
        previousScene,
        currentScene: scene,
        detectionResult: {
          scene,
          confidence: 1.0,
          timestamp: Date.now(),
          matchedTemplates: [],
          detectionTime: 0
        }
      };
      
      this.emit('sceneChange', changeEvent);
    }
  }

  /**
   * 等待特定场景出现
   */
  async waitForScene(targetScene: GameScene, timeout: number = 30000): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.currentScene === targetScene) {
        resolve(true);
        return;
      }

      const timeoutId = setTimeout(() => {
        this.removeListener('sceneChange', sceneChangeHandler);
        resolve(false);
      }, timeout);

      const sceneChangeHandler = (event: SceneChangeEvent) => {
        if (event.currentScene === targetScene) {
          clearTimeout(timeoutId);
          this.removeListener('sceneChange', sceneChangeHandler);
          resolve(true);
        }
      };

      this.on('sceneChange', sceneChangeHandler);
    });
  }

  /**
   * 销毁检测器
   */
  destroy(): void {
    this.stopDetection();
    this.removeAllListeners();
    this.logger.info('场景检测器已销毁');
  }
}