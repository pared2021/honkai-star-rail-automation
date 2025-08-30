import { TemplateManager, TemplateType, GameScene } from '../modules/TemplateManager';
import path from 'path';
import fs from 'fs';

// Mock fs module
jest.mock('fs', () => ({
  existsSync: jest.fn(),
  readdirSync: jest.fn(),
  statSync: jest.fn(),
  promises: {
    readFile: jest.fn()
  }
}));

const mockFs = require('fs');

// Mock ImageRecognition
jest.mock('../modules/ImageRecognition', () => {
  return {
    ImageRecognition: jest.fn().mockImplementation(() => ({
      findImage: jest.fn().mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 200 }
      })
    }))
  };
});

describe('TemplateManager', () => {
  let templateManager: TemplateManager;
  const mockTemplatesPath = '/mock/templates';

  beforeEach(() => {
    jest.clearAllMocks();
    
    templateManager = new TemplateManager({
      templatesPath: mockTemplatesPath,
      cacheEnabled: true,
      defaultThreshold: 0.8,
      maxCacheSize: 100
    });

    // Mock file system structure
    mockFs.existsSync.mockImplementation((path: any) => {
      const pathStr = path.toString();
      return pathStr.includes('daily') || pathStr.includes('buttons') || pathStr.includes('scenes');
    });

    mockFs.readdirSync.mockImplementation((path: any) => {
      const pathStr = path.toString();
      if (pathStr.includes('daily')) {
        return ['commission_button.png', 'accept_button.png', 'claim_reward_button.png'] as any;
      }
      if (pathStr.includes('buttons')) {
        return ['confirm_button.png', 'cancel_button.png'] as any;
      }
      if (pathStr.includes('scenes')) {
        return ['main_menu.png', 'battle_ui.png'] as any;
      }
      return [] as any;
    });

    mockFs.statSync.mockReturnValue({
      isFile: () => true,
      mtime: new Date('2025-01-20T10:00:00Z')
    } as any);
  });

  describe('initialization', () => {
    it('should initialize successfully', async () => {
      await templateManager.initialize();
      expect(templateManager.isReady()).toBe(true);
    });

    it('should load templates from all directories', async () => {
      await templateManager.initialize();
      
      const dailyTemplates = templateManager.getTemplatesByType(TemplateType.DAILY);
      const buttonTemplates = templateManager.getTemplatesByType(TemplateType.BUTTON);
      const sceneTemplates = templateManager.getTemplatesByType(TemplateType.SCENE);
      
      expect(dailyTemplates.length).toBe(3);
      expect(buttonTemplates.length).toBe(2);
      expect(sceneTemplates.length).toBe(2);
    });

    it('should handle initialization errors gracefully', async () => {
      mockFs.existsSync.mockReturnValue(false);
      
      // 应该成功初始化，即使没有模板目录
      await expect(templateManager.initialize()).resolves.not.toThrow();
      expect(templateManager.isReady()).toBe(true);
    });

    it('should handle file system errors during template loading', async () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readdirSync.mockImplementation(() => {
        throw new Error('Permission denied');
      });

      // 应该成功初始化，但没有加载任何模板
       await templateManager.initialize();
       expect(templateManager.isReady()).toBe(true);
       expect(templateManager.getStats().totalTemplates).toBe(0);
     });
  });

  describe('template management', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should get template by type and name', () => {
      const template = templateManager.getTemplate(TemplateType.DAILY, 'commission_button');
      
      expect(template).toBeDefined();
      expect(template?.name).toBe('commission_button');
      expect(template?.type).toBe(TemplateType.DAILY);
    });

    it('should return undefined for non-existent template', () => {
      const template = templateManager.getTemplate(TemplateType.DAILY, 'non_existent');
      expect(template).toBeUndefined();
    });

    it('should check if template exists', () => {
      expect(templateManager.hasTemplate(TemplateType.DAILY, 'commission_button')).toBe(true);
      expect(templateManager.hasTemplate(TemplateType.DAILY, 'non_existent')).toBe(false);
    });

    it('should get templates by type', () => {
      const dailyTemplates = templateManager.getTemplatesByType(TemplateType.DAILY);
      expect(dailyTemplates.length).toBe(3);
      expect(dailyTemplates.every(t => t.type === TemplateType.DAILY)).toBe(true);
    });

    it('should get templates by scene', () => {
      const commissionTemplates = templateManager.getTemplatesByScene(GameScene.COMMISSION);
      expect(commissionTemplates.length).toBeGreaterThan(0);
    });
  });

  describe('scene inference', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should infer commission scene from daily templates', () => {
      const template = templateManager.getTemplate(TemplateType.DAILY, 'commission_button');
      expect(template?.scene).toBe(GameScene.COMMISSION);
    });

    it('should infer main menu scene from filename', () => {
      const template = templateManager.getTemplate(TemplateType.SCENE, 'main_menu');
      expect(template?.scene).toBe(GameScene.MAIN_MENU);
    });

    it('should infer battle scene from filename', () => {
      const template = templateManager.getTemplate(TemplateType.SCENE, 'battle_ui');
      expect(template?.scene).toBe(GameScene.BATTLE);
    });
  });

  describe('template matching', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should find template in screenshot', async () => {
      const result = await templateManager.findTemplate(
        '/mock/screenshot.png',
        'commission_button',
        TemplateType.DAILY
      );

      expect(result.found).toBe(true);
      expect(result.confidence).toBe(0.9);
      expect(result.position).toEqual({ x: 100, y: 200 });
      expect(result.templateName).toBe('commission_button');
    });

    it('should handle non-existent template', async () => {
      const result = await templateManager.findTemplate(
        '/mock/screenshot.png',
        'non_existent',
        TemplateType.DAILY
      );

      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
      expect(result.templateName).toBe('non_existent');
    });

    it('should find multiple templates', async () => {
      const templates = [
        { name: 'commission_button', type: TemplateType.DAILY },
        { name: 'accept_button', type: TemplateType.DAILY }
      ];

      const results = await templateManager.findMultipleTemplates(
        '/mock/screenshot.png',
        templates
      );

      expect(results).toHaveLength(2);
      expect(results[0].found).toBe(true);
      expect(results[1].found).toBe(true);
    });
  });

  describe('daily commission templates', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should get all daily commission templates', () => {
      const dailyTemplates = templateManager.getDailyCommissionTemplates();
      expect(dailyTemplates.length).toBe(3);
      expect(dailyTemplates.every(t => t.type === TemplateType.DAILY)).toBe(true);
    });
  });

  describe('statistics', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should provide template statistics', () => {
      const stats = templateManager.getStats();
      
      expect(stats.totalTemplates).toBe(7); // 3 daily + 2 buttons + 2 scenes
      expect(stats.templatesByType[TemplateType.DAILY]).toBe(3);
      expect(stats.templatesByType[TemplateType.BUTTON]).toBe(2);
      expect(stats.templatesByType[TemplateType.SCENE]).toBe(2);
    });
  });

  describe('cache management', () => {
    beforeEach(async () => {
      await templateManager.initialize();
    });

    it('should clear cache', () => {
      templateManager.clearCache();
      const stats = templateManager.getStats();
      expect(stats.totalTemplates).toBe(0);
    });

    it('should reload templates', async () => {
      const initialStats = templateManager.getStats();
      expect(initialStats.totalTemplates).toBeGreaterThan(0);
      
      await templateManager.reload();
      
      const reloadedStats = templateManager.getStats();
      expect(reloadedStats.totalTemplates).toBe(initialStats.totalTemplates);
      expect(templateManager.isReady()).toBe(true);
    });
  });

  describe('configuration', () => {
    it('should use default configuration', () => {
      const defaultManager = new TemplateManager();
      expect(defaultManager.getTemplatesPath()).toContain('templates');
    });

    it('should use custom configuration', () => {
      const customPath = '/custom/templates';
      const customManager = new TemplateManager({ templatesPath: customPath });
      expect(customManager.getTemplatesPath()).toBe(customPath);
    });
  });

  describe('file type validation', () => {
    beforeEach(() => {
      mockFs.readdirSync.mockReturnValue([
        'valid_image.png',
        'another_image.jpg',
        'not_image.txt',
        'readme.md',
        'config.json'
      ] as any);
    });

    it('should only load image files', async () => {
      await templateManager.initialize();
      
      const dailyTemplates = templateManager.getTemplatesByType(TemplateType.DAILY);
      expect(dailyTemplates.length).toBe(2); // Only .png and .jpg files
      
      const templateNames = dailyTemplates.map(t => t.name);
      expect(templateNames).toContain('valid_image');
      expect(templateNames).toContain('another_image');
      expect(templateNames).not.toContain('not_image');
      expect(templateNames).not.toContain('readme');
    });
  });
});