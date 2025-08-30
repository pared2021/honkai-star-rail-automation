import { ImageRecognition } from '../modules/ImageRecognition';
import { jest } from '@jest/globals';
import * as fs from 'fs';
import * as path from 'path';

// Mock dependencies
jest.mock('robotjs');
jest.mock('fs');
jest.mock('path');

describe('ImageRecognition', () => {
  let imageRecognition: ImageRecognition;
  const mockConfig = {
    confidence: 0.8,
    timeout: 5000,
    retryCount: 3,
    templateCacheSize: 50,
    screenshotInterval: 100
  };

  beforeEach(() => {
    jest.clearAllMocks();
    imageRecognition = new ImageRecognition(mockConfig);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('构造函数和配置', () => {
    test('应该正确初始化配置', () => {
      expect(imageRecognition.getConfig()).toEqual(mockConfig);
    });

    test('应该能够更新配置', () => {
      const newConfig = {
        ...mockConfig,
        similarity: 0.9,
        timeout: 10000
      };
      
      imageRecognition.updateConfig(newConfig);
      expect(imageRecognition.getConfig()).toEqual(newConfig);
    });

    test('应该创建模板目录', () => {
      const mkdirSyncSpy = jest.spyOn(fs, 'mkdirSync').mockImplementation();
      const existsSyncSpy = jest.spyOn(fs, 'existsSync').mockReturnValue(false);
      
      ImageRecognition.createTemplateDirectories('./test-templates');
      
      expect(existsSyncSpy).toHaveBeenCalled();
      expect(mkdirSyncSpy).toHaveBeenCalled();
    });
  });

  describe('游戏窗口截图', () => {
    test('应该能够截取游戏窗口', async () => {
      const mockScreenshot = Buffer.from('mock-image-data');

      // Mock screenshot-desktop
      const screenshot = require('screenshot-desktop');
      screenshot.listDisplays = jest.fn().mockResolvedValue([{
        id: 0,
        width: 1920,
        height: 1080
      }]);
      screenshot.mockResolvedValue = jest.fn().mockResolvedValue(mockScreenshot);
      
      // Mock the default export function
      const mockScreenshotFn = jest.fn().mockResolvedValue(mockScreenshot);
      jest.doMock('screenshot-desktop', () => {
        const fn = mockScreenshotFn;
        fn.listDisplays = screenshot.listDisplays;
        return fn;
      });

      const result = await imageRecognition.captureGameWindow();
      
      expect(result).toBe(mockScreenshot);
    });

    test('应该能够截取指定区域', async () => {
      const mockScreenshot = Buffer.from('mock-image-data');
      const mockCroppedBuffer = Buffer.from('mock-cropped-data');
      
      // Mock captureGameWindow
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(mockScreenshot);
      
      // Mock Jimp
      const mockJimp = {
        clone: jest.fn().mockReturnThis(),
        crop: jest.fn().mockReturnThis(),
        getBuffer: jest.fn().mockResolvedValue(mockCroppedBuffer)
      };
      const { Jimp } = require('jimp');
      Jimp.read = jest.fn().mockResolvedValue(mockJimp);

      const region = { x: 100, y: 100, width: 500, height: 300 };
      const result = await imageRecognition.captureRegion(region);
      
      expect(mockJimp.crop).toHaveBeenCalledWith({
        x: region.x,
        y: region.y,
        w: region.width,
        h: region.height
      });
      expect(result).toBe(mockCroppedBuffer);
    });
  });

  describe('模板匹配', () => {
    test('应该能够加载模板图像', async () => {
      const mockTemplate = {
        width: 100,
        height: 50,
        bitmap: { data: Buffer.from('mock-template-data') }
      };

      jest.spyOn(fs, 'existsSync').mockReturnValue(true);
      const { Jimp } = require('jimp');
      Jimp.read = jest.fn().mockResolvedValue(mockTemplate);

      // 通过findImage间接测试loadTemplate
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      jest.spyOn(imageRecognition as any, 'performTemplateMatch').mockReturnValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 100 },
        region: { x: 100, y: 100, width: 100, height: 50 }
      });

      const result = await imageRecognition.findImage('test-template.png');
      
      expect(result.found).toBe(true);
    });

    test('应该能够在截图中查找模板', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      const mockTemplate = {
        width: 100,
        height: 50,
        bitmap: { data: Buffer.from('mock-template') }
      };

      // Mock methods
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(mockScreenshot);
      jest.spyOn(fs, 'existsSync').mockReturnValue(true);
      
      const { Jimp } = require('jimp');
      Jimp.read = jest.fn()
        .mockResolvedValueOnce(mockScreenshot) // for screenshot
        .mockResolvedValueOnce(mockTemplate); // for template
      
      jest.spyOn(imageRecognition as any, 'performTemplateMatch').mockReturnValue({
        confidence: 0.95,
        position: { x: 500, y: 300 },
        region: { x: 500, y: 300, width: 100, height: 50 }
      });

      const result = await imageRecognition.findImage('test-template.png');
      
      expect(result.found).toBe(true);
      expect(result.position).toEqual({ x: 500, y: 300 });
      expect(result.confidence).toBe(0.95);
    });

    test('应该在找不到模板时返回正确结果', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      const mockTemplate = {
        width: 100,
        height: 50,
        bitmap: { data: Buffer.from('mock-template') }
      };

      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(mockScreenshot);
      jest.spyOn(fs, 'existsSync').mockReturnValue(true);
      
      const { Jimp } = require('jimp');
      Jimp.read = jest.fn()
        .mockResolvedValueOnce(mockScreenshot)
        .mockResolvedValueOnce(mockTemplate);
      
      jest.spyOn(imageRecognition as any, 'performTemplateMatch').mockReturnValue({
        confidence: 0.3,
        position: { x: 0, y: 0 },
        region: { x: 0, y: 0, width: 100, height: 50 }
      });

      const result = await imageRecognition.findImage('non-existent-template.png');
      
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0.3);
    });
  });

  describe('颜色检测', () => {
    test('应该能够检测指定位置的像素颜色', async () => {
      const mockScreenshot = {
        width: 1920,
        height: 1080,
        image: Buffer.from('mock-screenshot'),
        colorAt: jest.fn().mockReturnValue(0xFF0000) // 红色
      };

      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(mockScreenshot);

      const color = await imageRecognition.getPixelColor(100, 200);
      
      expect(mockScreenshot.colorAt).toHaveBeenCalledWith(100, 200);
      expect(color).toBe(0xFF0000);
    });

    test('应该能够检测颜色范围', async () => {
      const mockScreenshot = {
        width: 100,
        height: 100,
        image: Buffer.from('mock-screenshot'),
        colorAt: jest.fn((x, y) => {
          // 模拟部分像素匹配目标颜色
          if (x < 50 && y < 50) return 0xFF0000; // 红色
          return 0x00FF00; // 绿色
        })
      };

      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(mockScreenshot);

      const colorRange = {
        r: { min: 250, max: 255 },
        g: { min: 0, max: 10 },
        b: { min: 0, max: 10 }
      };

      const region = { x: 0, y: 0, width: 100, height: 100 };
      const result = await imageRecognition.detectColor(colorRange, region);
      
      expect(result.found).toBe(true);
      expect(result.matchingPixels).toBeGreaterThan(0);
      expect(result.totalPixels).toBe(10000); // 100x100
    });
  });

  describe('场景识别', () => {
    test('应该能够识别游戏场景', async () => {
      const mockTemplates = {
        'main-menu': { found: false, confidence: 0.2 },
        'battle': { found: true, confidence: 0.9 },
        'inventory': { found: false, confidence: 0.1 }
      };

      jest.spyOn(imageRecognition, 'findImage').mockImplementation((templateName) => {
        const sceneName = templateName.replace('.png', '');
        return Promise.resolve({
          found: mockTemplates[sceneName]?.found || false,
          location: mockTemplates[sceneName]?.found ? { x: 100, y: 100 } : null,
          confidence: mockTemplates[sceneName]?.confidence || 0
        });
      });

      const result = await imageRecognition.recognizeGameScene();
      
      expect(result.scene).toBe('battle');
      expect(result.confidence).toBe(0.9);
    });
  });

  describe('等待功能', () => {
    test('应该能够等待图像出现', async () => {
      let callCount = 0;
      jest.spyOn(imageRecognition, 'findImage').mockImplementation(() => {
        callCount++;
        if (callCount >= 3) {
          return Promise.resolve({
            found: true,
            location: { x: 100, y: 100 },
            confidence: 0.9
          });
        }
        return Promise.resolve({
          found: false,
          location: null,
          confidence: 0.1
        });
      });

      const result = await imageRecognition.waitForImage('target.png', 1000);
      
      expect(result.found).toBe(true);
      expect(callCount).toBeGreaterThanOrEqual(3);
    });

    test('应该在超时后返回失败结果', async () => {
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        location: null,
        confidence: 0.1
      });

      const result = await imageRecognition.waitForImage('non-existent.png', 500);
      
      expect(result.found).toBe(false);
    });
  });

  describe('缓存管理', () => {
    test('应该能够清除缓存', () => {
      // 添加一些缓存数据
      imageRecognition['templateCache'].set('test', { width: 100, height: 100, image: Buffer.alloc(0) });
      imageRecognition['screenshotCache'].set('test', { width: 100, height: 100, image: Buffer.alloc(0), colorAt: jest.fn() });
      
      imageRecognition.clearCache();
      
      expect(imageRecognition['templateCache'].size).toBe(0);
      expect(imageRecognition['screenshotCache'].size).toBe(0);
    });

    test('应该能够获取缓存统计', () => {
      // 添加一些缓存数据
      imageRecognition['templateCache'].set('test1', { width: 100, height: 100, image: Buffer.alloc(0) });
      imageRecognition['templateCache'].set('test2', { width: 100, height: 100, image: Buffer.alloc(0) });
      
      const stats = imageRecognition.getCacheStats();
      
      expect(stats.templateCacheSize).toBe(2);
      expect(stats.screenshotCacheSize).toBe(0);
    });
  });

  describe('统计信息', () => {
    test('应该能够获取图像识别统计', () => {
      const stats = imageRecognition.getImageStats();
      
      expect(stats).toHaveProperty('totalRecognitions');
      expect(stats).toHaveProperty('successfulRecognitions');
      expect(stats).toHaveProperty('averageConfidence');
      expect(stats).toHaveProperty('averageProcessingTime');
      expect(stats).toHaveProperty('cacheHitRate');
    });
  });

  describe('游戏窗口边界', () => {
    test('应该能够设置游戏窗口边界', () => {
      const newBounds = {
        x: 100,
        y: 100,
        width: 1280,
        height: 720
      };
      
      imageRecognition.setGameWindowBounds(newBounds);
      
      const config = imageRecognition.getConfig();
      expect(config.gameWindow).toEqual(newBounds);
    });
  });

  describe('错误处理', () => {
    test('应该处理截图失败', async () => {
      const robotjs = require('robotjs');
      robotjs.screen = {
        capture: jest.fn().mockImplementation(() => {
          throw new Error('Screenshot failed');
        })
      };

      await expect(imageRecognition.captureGameWindow()).rejects.toThrow('Screenshot failed');
    });

    test('应该处理模板加载失败', async () => {
      jest.spyOn(fs, 'existsSync').mockReturnValue(false);
      
      await expect(imageRecognition.loadTemplate('non-existent.png')).rejects.toThrow();
    });
  });
});