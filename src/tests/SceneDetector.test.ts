import { SceneDetector, SceneDetectorConfig, SceneDetectionResult, SceneChangeEvent } from '../modules/SceneDetector';
import { TemplateManager, GameScene, TemplateType } from '../modules/TemplateManager';
import { ImageRecognition } from '../modules/ImageRecognition';
import { EventEmitter } from 'events';

// Mock dependencies
jest.mock('../modules/TemplateManager');
jest.mock('../modules/ImageRecognition');
jest.mock('pixelmatch', () => {
  return jest.fn(() => 0);
});

const MockedTemplateManager = TemplateManager as jest.MockedClass<typeof TemplateManager>;
const MockedImageRecognition = ImageRecognition as jest.MockedClass<typeof ImageRecognition>;

describe('SceneDetector', () => {
  let sceneDetector: SceneDetector;
  let mockTemplateManager: jest.Mocked<TemplateManager>;
  let mockImageRecognition: jest.Mocked<ImageRecognition>;
  let mockConfig: Partial<SceneDetectorConfig>;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Create mock template manager
    mockTemplateManager = {
      isReady: jest.fn().mockReturnValue(true),
      getTemplatesByType: jest.fn(),
      getTemplatesByScene: jest.fn(),
      initialize: jest.fn(),
      getTemplate: jest.fn(),
      hasTemplate: jest.fn(),
      findTemplate: jest.fn(),
      getStats: jest.fn(),
      clearCache: jest.fn(),
      updateConfig: jest.fn(),
      getConfig: jest.fn()
    } as any;

    // Create mock image recognition
    mockImageRecognition = {
      captureGameWindow: jest.fn(),
      findImage: jest.fn(),
      loadTemplate: jest.fn(),
      performTemplateMatch: jest.fn(),
      calculateSimilarity: jest.fn(),
      recognizeText: jest.fn()
    } as any;

    // Mock constructors
    MockedTemplateManager.mockImplementation(() => mockTemplateManager);
    MockedImageRecognition.mockImplementation(() => mockImageRecognition);

    mockConfig = {
      detectionInterval: 500,
      confidenceThreshold: 0.8,
      confirmationCount: 2,
      autoDetection: false,
      detectionTimeout: 3000
    };

    sceneDetector = new SceneDetector(mockTemplateManager, mockConfig);
  });

  afterEach(() => {
    sceneDetector.destroy();
  });

  describe('Constructor', () => {
    it('should initialize with default config when no config provided', () => {
      const detector = new SceneDetector(mockTemplateManager);
      const config = detector.getConfig();
      
      expect(config.detectionInterval).toBe(1000);
      expect(config.confidenceThreshold).toBe(0.7);
      expect(config.confirmationCount).toBe(2);
      expect(config.autoDetection).toBe(false);
      expect(config.detectionTimeout).toBe(5000);
      
      detector.destroy();
    });

    it('should merge provided config with defaults', () => {
      const config = sceneDetector.getConfig();
      
      expect(config.detectionInterval).toBe(500);
      expect(config.confidenceThreshold).toBe(0.8);
      expect(config.confirmationCount).toBe(2);
      expect(config.autoDetection).toBe(false);
      expect(config.detectionTimeout).toBe(3000);
    });

    it('should initialize stats correctly', () => {
      const stats = sceneDetector.getStats();
      
      expect(stats.totalDetections).toBe(0);
      expect(stats.successfulDetections).toBe(0);
      expect(stats.sceneChanges).toBe(0);
      expect(stats.averageDetectionTime).toBe(0);
      expect(stats.lastDetectionTime).toBe(0);
      expect(Object.keys(stats.sceneDetectionCounts)).toContain(GameScene.MAIN_MENU);
    });
  });

  describe('Detection Lifecycle', () => {
    it('should start detection successfully', async () => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      await sceneDetector.startDetection();
      
      expect(sceneDetector.isDetectionRunning()).toBe(true);
      expect(mockTemplateManager.isReady).toHaveBeenCalled();
    });

    it('should throw error when starting detection with unready template manager', async () => {
      mockTemplateManager.isReady.mockReturnValue(false);
      
      await expect(sceneDetector.startDetection()).rejects.toThrow('TemplateManager未初始化，无法启动场景检测');
    });

    it('should not start detection if already running', async () => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      await sceneDetector.startDetection();
      const firstCall = mockTemplateManager.isReady.mock.calls.length;
      
      await sceneDetector.startDetection();
      
      expect(mockTemplateManager.isReady.mock.calls.length).toBe(firstCall);
    });

    it('should stop detection successfully', async () => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      await sceneDetector.startDetection();
      sceneDetector.stopDetection();
      
      expect(sceneDetector.isDetectionRunning()).toBe(false);
    });
  });

  describe('Scene Detection', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
    });

    it('should detect scene successfully', async () => {
      const mockTemplate = {
        name: 'main_menu_template',
        path: '/path/to/template.png',
        type: TemplateType.SCENE,
        scene: GameScene.MAIN_MENU,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([]);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 200 }
      });
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.MAIN_MENU);
      expect(result.confidence).toBe(0.9);
      expect(result.matchedTemplates).toHaveLength(1);
      expect(result.matchedTemplates[0].name).toBe('main_menu_template');
    });

    it('should return UNKNOWN scene when no templates match', async () => {
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.UNKNOWN);
      expect(result.confidence).toBe(0);
      expect(result.matchedTemplates).toHaveLength(0);
    });

    it('should handle detection errors gracefully', async () => {
      mockImageRecognition.captureGameWindow.mockRejectedValue(new Error('Screenshot failed'));
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.UNKNOWN);
      expect(result.confidence).toBe(0);
    });

    it('should filter templates by confidence threshold', async () => {
      const mockTemplate = {
        name: 'low_confidence_template',
        path: '/path/to/template.png',
        type: TemplateType.SCENE,
        scene: GameScene.MAIN_MENU,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        confidence: 0.5, // Below threshold of 0.8
        position: { x: 100, y: 200 }
      });
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.UNKNOWN);
    });
  });

  describe('Scene Change Detection', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
    });

    it('should emit scene change event after confirmation', async () => {
      const mockTemplate = {
        name: 'battle_template',
        path: '/path/to/template.png',
        type: TemplateType.SCENE,
        scene: GameScene.BATTLE,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([]);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 200 }
      });

      const sceneChangePromise = new Promise<SceneChangeEvent>((resolve) => {
        sceneDetector.once('sceneChange', resolve);
      });

      // Detect same scene twice to trigger confirmation
      await sceneDetector.detectCurrentScene();
      await sceneDetector.detectCurrentScene();

      const changeEvent = await sceneChangePromise;
      
      expect(changeEvent.previousScene).toBe(GameScene.UNKNOWN);
      expect(changeEvent.currentScene).toBe(GameScene.BATTLE);
    });

    it('should not emit scene change without sufficient confirmation', async () => {
      const mockTemplate = {
        name: 'battle_template',
        path: '/path/to/template.png',
        type: TemplateType.SCENE,
        scene: GameScene.BATTLE,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([]);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 200 }
      });

      let sceneChangeEmitted = false;
      sceneDetector.once('sceneChange', () => {
        sceneChangeEmitted = true;
      });

      // Only one detection, should not trigger scene change
      await sceneDetector.detectCurrentScene();
      
      // Wait a bit to ensure no event is emitted
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(sceneChangeEmitted).toBe(false);
      expect(sceneDetector.getCurrentScene()).toBe(GameScene.UNKNOWN);
    });
  });

  describe('Auto Detection', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
    });

    it('should start auto detection when enabled', async () => {
      const autoDetectionConfig = { ...mockConfig, autoDetection: true };
      const autoDetector = new SceneDetector(mockTemplateManager, autoDetectionConfig);
      
      await autoDetector.startDetection();
      
      // Wait for auto detection interval
      await new Promise(resolve => setTimeout(resolve, 600));
      
      // Should have called captureGameWindow multiple times
      expect(mockImageRecognition.captureGameWindow.mock.calls.length).toBeGreaterThan(1);
      
      autoDetector.destroy();
    });

    it('should stop auto detection when disabled', async () => {
      const autoDetectionConfig = { ...mockConfig, autoDetection: true };
      const autoDetector = new SceneDetector(mockTemplateManager, autoDetectionConfig);
      
      await autoDetector.startDetection();
      autoDetector.stopDetection();
      
      const callCountAfterStop = mockImageRecognition.captureGameWindow.mock.calls.length;
      
      // Wait for what would be another detection interval
      await new Promise(resolve => setTimeout(resolve, 600));
      
      // Should not have made additional calls
      expect(mockImageRecognition.captureGameWindow.mock.calls.length).toBe(callCountAfterStop);
      
      autoDetector.destroy();
    });
  });

  describe('Statistics', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
    });

    it('should update statistics after detection', async () => {
      const mockTemplate = {
        name: 'main_menu_template',
        path: '/path/to/template.png',
        type: TemplateType.SCENE,
        scene: GameScene.MAIN_MENU,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([]);
      
      // Add a small delay to ensure detectionTime > 0
      mockImageRecognition.findImage.mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 1));
        return {
          found: true,
          confidence: 0.9,
          position: { x: 100, y: 200 }
        };
      });
      
      await sceneDetector.detectCurrentScene();
      
      const stats = sceneDetector.getStats();
      
      expect(stats.totalDetections).toBe(1);
      expect(stats.successfulDetections).toBe(1);
      expect(stats.sceneDetectionCounts[GameScene.MAIN_MENU]).toBe(1);
      expect(stats.averageDetectionTime).toBeGreaterThan(0);
      expect(stats.lastDetectionTime).toBeGreaterThan(0);
    });

    it('should reset statistics correctly', async () => {
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      await sceneDetector.detectCurrentScene();
      sceneDetector.resetStats();
      
      const stats = sceneDetector.getStats();
      
      expect(stats.totalDetections).toBe(0);
      expect(stats.successfulDetections).toBe(0);
      expect(stats.sceneChanges).toBe(0);
      expect(stats.averageDetectionTime).toBe(0);
      expect(stats.lastDetectionTime).toBe(0);
    });
  });

  describe('Configuration Management', () => {
    it('should update configuration correctly', () => {
      const newConfig = {
        detectionInterval: 2000,
        confidenceThreshold: 0.9
      };
      
      sceneDetector.updateConfig(newConfig);
      
      const config = sceneDetector.getConfig();
      expect(config.detectionInterval).toBe(2000);
      expect(config.confidenceThreshold).toBe(0.9);
      expect(config.confirmationCount).toBe(2); // Should keep original value
    });

    it('should restart auto detection when auto detection setting changes', async () => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      mockTemplateManager.getTemplatesByType.mockReturnValue([]);
      
      await sceneDetector.startDetection();
      
      // Enable auto detection
      sceneDetector.updateConfig({ autoDetection: true });
      
      // Wait for auto detection to trigger
      await new Promise(resolve => setTimeout(resolve, 600));
      
      expect(mockImageRecognition.captureGameWindow.mock.calls.length).toBeGreaterThan(1);
    });
  });

  describe('Manual Scene Setting', () => {
    it('should set current scene manually', () => {
      const sceneChangePromise = new Promise<SceneChangeEvent>((resolve) => {
        sceneDetector.once('sceneChange', resolve);
      });
      
      sceneDetector.setCurrentScene(GameScene.BATTLE);
      
      expect(sceneDetector.getCurrentScene()).toBe(GameScene.BATTLE);
      
      return sceneChangePromise.then(changeEvent => {
        expect(changeEvent.previousScene).toBe(GameScene.UNKNOWN);
        expect(changeEvent.currentScene).toBe(GameScene.BATTLE);
        expect(changeEvent.detectionResult.confidence).toBe(1.0);
      });
    });

    it('should not emit event when setting same scene', () => {
      let sceneChangeEmitted = false;
      sceneDetector.once('sceneChange', () => {
        sceneChangeEmitted = true;
      });
      
      sceneDetector.setCurrentScene(GameScene.UNKNOWN); // Same as initial
      
      expect(sceneChangeEmitted).toBe(false);
    });
  });

  describe('Scene Waiting', () => {
    it('should resolve immediately if already in target scene', async () => {
      sceneDetector.setCurrentScene(GameScene.BATTLE);
      
      const result = await sceneDetector.waitForScene(GameScene.BATTLE, 1000);
      
      expect(result).toBe(true);
    });

    it('should wait for scene change and resolve when target scene is reached', async () => {
      const waitPromise = sceneDetector.waitForScene(GameScene.BATTLE, 5000);
      
      // Simulate scene change after a delay
      setTimeout(() => {
        sceneDetector.setCurrentScene(GameScene.BATTLE);
      }, 100);
      
      const result = await waitPromise;
      
      expect(result).toBe(true);
    });

    it('should timeout and return false if target scene is not reached', async () => {
      const result = await sceneDetector.waitForScene(GameScene.BATTLE, 100);
      
      expect(result).toBe(false);
    });
  });

  describe('Related Templates Detection', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
    });

    it('should find related templates to improve detection accuracy', async () => {
      const sceneTemplate = {
        name: 'battle_scene',
        path: '/path/to/scene.png',
        type: TemplateType.SCENE,
        scene: GameScene.BATTLE,
        lastModified: Date.now()
      };
      
      const relatedTemplate = {
        name: 'battle_button',
        path: '/path/to/button.png',
        type: TemplateType.BUTTON,
        scene: GameScene.BATTLE,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([sceneTemplate]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([sceneTemplate, relatedTemplate]);
      
      // Mock scene template match
      mockImageRecognition.findImage
        .mockResolvedValueOnce({
          found: true,
          confidence: 0.9,
          position: { x: 100, y: 200 }
        })
        // Mock related template match
        .mockResolvedValueOnce({
          found: true,
          confidence: 0.85,
          position: { x: 150, y: 250 }
        });
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.BATTLE);
      expect(result.matchedTemplates).toHaveLength(2);
      expect(result.matchedTemplates[0].name).toBe('battle_scene');
      expect(result.matchedTemplates[1].name).toBe('battle_button');
    });
  });

  describe('Best Scene Selection', () => {
    beforeEach(() => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
    });

    it('should select scene with highest confidence when multiple scenes detected', async () => {
      const template1 = {
        name: 'scene1',
        path: '/path/to/scene1.png',
        type: TemplateType.SCENE,
        scene: GameScene.MAIN_MENU,
        lastModified: Date.now()
      };
      
      const template2 = {
        name: 'scene2',
        path: '/path/to/scene2.png',
        type: TemplateType.SCENE,
        scene: GameScene.BATTLE,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([template1, template2]);
      mockTemplateManager.getTemplatesByScene.mockReturnValue([]);
      
      // Mock different confidence levels
      mockImageRecognition.findImage
        .mockResolvedValueOnce({
          found: true,
          confidence: 0.85,
          position: { x: 100, y: 200 }
        })
        .mockResolvedValueOnce({
          found: true,
          confidence: 0.95, // Higher confidence
          position: { x: 150, y: 250 }
        });
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.BATTLE);
      expect(result.confidence).toBe(0.95);
    });
  });

  describe('Error Handling', () => {
    it('should handle template loading errors gracefully', async () => {
      mockTemplateManager.isReady.mockReturnValue(true);
      mockImageRecognition.captureGameWindow.mockResolvedValue(Buffer.from('screenshot'));
      
      const mockTemplate = {
        name: 'error_template',
        path: '/invalid/path.png',
        type: TemplateType.SCENE,
        scene: GameScene.MAIN_MENU,
        lastModified: Date.now()
      };
      
      mockTemplateManager.getTemplatesByType.mockReturnValue([mockTemplate]);
      mockImageRecognition.findImage.mockRejectedValue(new Error('Template not found'));
      
      const result = await sceneDetector.detectCurrentScene();
      
      expect(result.scene).toBe(GameScene.UNKNOWN);
      expect(result.confidence).toBe(0);
    });
  });

  describe('Cleanup', () => {
    it('should clean up resources when destroyed', () => {
      const detector = new SceneDetector(mockTemplateManager, { autoDetection: true });
      
      detector.destroy();
      
      expect(detector.isDetectionRunning()).toBe(false);
      expect(detector.listenerCount('sceneChange')).toBe(0);
    });
  });
})