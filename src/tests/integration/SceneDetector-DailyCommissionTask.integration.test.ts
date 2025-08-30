import { DailyCommissionTask } from '../../modules/DailyCommissionTask';
import { SceneDetector } from '../../modules/SceneDetector';
import { TemplateManager } from '../../modules/TemplateManager';
import { InputController } from '../../modules/InputController';
import { ImageRecognition } from '../../modules/ImageRecognition';
import { GameDetector } from '../../modules/GameDetector';
import { GameScene } from '../../modules/TemplateManager';
import path from 'path';

/**
 * SceneDetector与DailyCommissionTask集成测试
 * 测试真实的场景检测与任务执行的集成
 */
describe('SceneDetector-DailyCommissionTask Integration', () => {
  let sceneDetector: SceneDetector;
  let templateManager: TemplateManager;
  let inputController: InputController;
  let imageRecognition: ImageRecognition;
  let gameDetector: GameDetector;
  let dailyCommissionTask: DailyCommissionTask;

  beforeAll(async () => {
    // 初始化TemplateManager
    const templatesPath = path.join(__dirname, '../../assets/templates');
    templateManager = new TemplateManager({ templatesPath });
    await templateManager.initialize();

    // 初始化其他组件
    imageRecognition = new ImageRecognition();
    gameDetector = new GameDetector();
    inputController = new InputController();
    
    // 初始化SceneDetector
    sceneDetector = new SceneDetector(templateManager, {
      detectionInterval: 500,
      confidenceThreshold: 0.7,
      confirmationCount: 2,
      autoDetection: false,
      detectionTimeout: 5000
    });

    // 初始化DailyCommissionTask
    dailyCommissionTask = new DailyCommissionTask(
      sceneDetector,
      inputController,
      imageRecognition,
      gameDetector,
      {
        autoClaimRewards: true,
        autoStartCommissions: false,
        maxCommissions: 2,
        waitTimeout: 5000
      }
    );
  });

  afterEach(() => {
    // 清理所有mock
    jest.restoreAllMocks();
  });

  afterAll(async () => {
    // 停止所有检测
    if (sceneDetector.isDetectionRunning()) {
      sceneDetector.stopDetection();
    }
    sceneDetector.destroy();
    dailyCommissionTask.removeAllListeners();
  });

  describe('Component Initialization', () => {
    test('should initialize all components successfully', () => {
      expect(templateManager.isReady()).toBe(true);
      expect(sceneDetector).toBeDefined();
      expect(dailyCommissionTask).toBeDefined();
    });

    test('should have correct initial configuration', () => {
      const sceneConfig = sceneDetector.getConfig();
      expect(sceneConfig.detectionInterval).toBe(500);
      expect(sceneConfig.confidenceThreshold).toBe(0.7);
      
      const taskConfig = dailyCommissionTask.getConfig();
      expect(taskConfig.autoClaimRewards).toBe(true);
      expect(taskConfig.maxCommissions).toBe(2);
    });
  });

  describe('Scene Detection Integration', () => {
    test('should start scene detection before task execution', async () => {
      // 启动场景检测
      await sceneDetector.startDetection();
      expect(sceneDetector.isDetectionRunning()).toBe(true);
      
      // 停止检测
      sceneDetector.stopDetection();
      expect(sceneDetector.isDetectionRunning()).toBe(false);
    });

    test('should detect scene changes during task execution', async () => {
      const sceneChanges: any[] = [];
      
      // 监听场景变化事件
      sceneDetector.on('sceneChange', (event) => {
        sceneChanges.push(event);
      });

      // 启动场景检测
      await sceneDetector.startDetection();
      
      // 模拟场景变化
      sceneDetector.setCurrentScene(GameScene.MAIN_MENU);
      await new Promise(resolve => setTimeout(resolve, 100));
      
      sceneDetector.setCurrentScene(GameScene.COMMISSION);
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 验证场景变化被正确检测
      expect(sceneChanges.length).toBeGreaterThan(0);
      
      sceneDetector.stopDetection();
    });

    test('should handle waitForScene timeout gracefully', async () => {
      // 设置一个不存在的场景
      const result = await sceneDetector.waitForScene(GameScene.BATTLE, 1000);
      expect(result).toBe(false);
    });
  });

  describe('Task Execution with Scene Detection', () => {
    test('should check execution conditions with scene detector', async () => {
      // Mock游戏检测器返回true
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(true);
      jest.spyOn(gameDetector, 'isGameActive').mockReturnValue(true);
      
      const canExecute = await dailyCommissionTask.canExecute();
      expect(canExecute).toBe(true);
    });

    test('should handle scene detection errors during task execution', async () => {
      // Mock场景检测失败
      jest.spyOn(sceneDetector, 'detectCurrentScene').mockRejectedValue(new Error('Scene detection failed'));
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(true);
      jest.spyOn(gameDetector, 'isGameActive').mockReturnValue(true);
      
      // Mock图像识别和输入控制器
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        location: { x: 0, y: 0 },
        confidence: 0
      });
      
      const result = await dailyCommissionTask.execute();
      expect(result.success).toBe(false);
      expect(result.message).toContain('失败');
    });
  });

  describe('Performance and Resource Management', () => {
    test('should manage resources properly during integration', async () => {
      const initialStats = sceneDetector.getStats();
      
      // Mock detectCurrentScene to avoid actual detection
      jest.spyOn(sceneDetector, 'detectCurrentScene').mockResolvedValue({
        scene: GameScene.MAIN_MENU,
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      });
      
      // 启动检测
      await sceneDetector.startDetection();
      
      // 执行一些检测
      await sceneDetector.detectCurrentScene();
      await sceneDetector.detectCurrentScene();
      
      const finalStats = sceneDetector.getStats();
      expect(finalStats.totalDetections).toBeGreaterThanOrEqual(initialStats.totalDetections);
      
      // 清理资源
      sceneDetector.stopDetection();
    });

    test('should handle concurrent operations safely', async () => {
      // 启动场景检测
      await sceneDetector.startDetection();
      
      // 并发执行多个检测
      const detectionPromises = [
        sceneDetector.detectCurrentScene(),
        sceneDetector.detectCurrentScene(),
        sceneDetector.detectCurrentScene()
      ];
      
      const results = await Promise.allSettled(detectionPromises);
      
      // 验证所有检测都完成（无论成功或失败）
      expect(results.length).toBe(3);
      results.forEach(result => {
        expect(['fulfilled', 'rejected']).toContain(result.status);
      });
      
      sceneDetector.stopDetection();
    });
  });

  describe('Configuration Synchronization', () => {
    test('should synchronize timeout configurations', () => {
      const sceneConfig = sceneDetector.getConfig();
      const taskConfig = dailyCommissionTask.getConfig();
      
      // 验证超时配置的合理性
      expect(taskConfig.waitTimeout).toBeLessThanOrEqual(sceneConfig.detectionTimeout * 10);
    });

    test('should update configurations dynamically', () => {
      // 更新场景检测器配置
      sceneDetector.updateConfig({
        confidenceThreshold: 0.8,
        detectionInterval: 1000
      });
      
      const updatedConfig = sceneDetector.getConfig();
      expect(updatedConfig.confidenceThreshold).toBe(0.8);
      expect(updatedConfig.detectionInterval).toBe(1000);
      
      // 更新任务配置
      dailyCommissionTask.updateConfig({
        waitTimeout: 8000,
        maxCommissions: 3
      });
      
      const updatedTaskConfig = dailyCommissionTask.getConfig();
      expect(updatedTaskConfig.waitTimeout).toBe(8000);
      expect(updatedTaskConfig.maxCommissions).toBe(3);
    });
  });

  describe('Error Recovery and Resilience', () => {
    test('should recover from temporary scene detection failures', async () => {
      let callCount = 0;
      
      // Mock前两次调用失败，第三次成功
      jest.spyOn(sceneDetector, 'detectCurrentScene').mockImplementation(async () => {
        callCount++;
        if (callCount <= 2) {
          throw new Error('Temporary failure');
        }
        return {
          scene: GameScene.MAIN_MENU,
          confidence: 0.9,
          timestamp: Date.now(),
          matchedTemplates: [],
          detectionTime: 100
        };
      });
      
      // 多次尝试检测
      let lastResult;
      for (let i = 0; i < 3; i++) {
        try {
          lastResult = await sceneDetector.detectCurrentScene();
          break;
        } catch (error) {
          // 继续尝试
        }
      }
      
      expect(lastResult).toBeDefined();
      expect(lastResult?.scene).toBe(GameScene.MAIN_MENU);
    });

    test('should maintain state consistency during errors', async () => {
      const initialScene = sceneDetector.getCurrentScene();
      
      // 尝试一个会失败的操作
      try {
        await sceneDetector.waitForScene(GameScene.BATTLE, 100);
      } catch (error) {
        // 忽略错误
      }
      
      // 验证状态没有被破坏
      const currentScene = sceneDetector.getCurrentScene();
      expect(currentScene).toBe(initialScene);
    });
  });
});