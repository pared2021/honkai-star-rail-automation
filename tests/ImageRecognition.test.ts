// 测试文件，允许使用any类型进行mock
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { ImageRecognition } from '../src/modules/ImageRecognition';
import * as fs from 'fs';

// Mock函数必须在jest.mock之前定义
const mockJimpRead = jest.fn() as jest.MockedFunction<any>;
const mockJimpIntToRGBA = jest.fn() as jest.MockedFunction<any>;
const mockJimpRgbaToInt = jest.fn() as jest.MockedFunction<any>;

// Mock screenshot-desktop
jest.mock('screenshot-desktop', () => {
  const mockFn = jest.fn();
  mockFn.listDisplays = jest.fn();
  return mockFn;
});
jest.mock('fs', () => ({
  existsSync: jest.fn(),
  mkdirSync: jest.fn(),
  readdirSync: jest.fn(),
  readFileSync: jest.fn(),
  statSync: jest.fn().mockReturnValue({ mtime: new Date() })
}));

// Mock jimp模块
jest.mock('jimp', () => ({
  Jimp: {
    read: jest.fn(),
    MIME_PNG: 'image/png'
  },
  intToRGBA: jest.fn(),
  rgbaToInt: jest.fn()
}));

describe('ImageRecognition', () => {
  let imageRecognition: ImageRecognition;
  let mockConfig: any;

  beforeEach(() => {
    mockConfig = {
      confidence: 0.8,
      timeout: 5000,
      templateCacheSize: 10,
      screenshotInterval: 100
    };
    
    // Reset all mocks
    jest.clearAllMocks();
    
    // 设置mock函数的实现
    const { Jimp } = require('jimp');
    const { intToRGBA, rgbaToInt } = require('jimp');
    const mockScreenshotModule = require('screenshot-desktop');
    const mockFs = require('fs');
    
    Jimp.read.mockImplementation(mockJimpRead);
    intToRGBA.mockImplementation(mockJimpIntToRGBA);
    rgbaToInt.mockImplementation(mockJimpRgbaToInt);
    
    // 设置fs mock的默认实现
    mockFs.existsSync.mockReturnValue(true);
    mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
    mockFs.statSync.mockReturnValue({ mtime: new Date() });
    
    // 设置screenshot-desktop mock
    mockScreenshotModule.mockResolvedValue(Buffer.from('mock-screenshot'));
    mockScreenshotModule.listDisplays.mockResolvedValue([{ id: 0, name: 'Display 1', width: 1920, height: 1080 }]);
    
    imageRecognition = new ImageRecognition(mockConfig);
  });

  afterEach(() => {
    imageRecognition.clearCache();
    jest.restoreAllMocks();
  });

  describe('构造函数', () => {
    it('应该正确初始化配置', () => {
      expect(imageRecognition).toBeDefined();
      expect(imageRecognition.getCacheStats().templateCacheSize).toBe(0);
    });

    it('应该使用默认配置', () => {
      const defaultImageRecognition = new ImageRecognition();
      expect(defaultImageRecognition).toBeDefined();
    });
  });

  describe('captureGameWindow', () => {
    it('应该成功截取游戏窗口', async () => {
      const mockScreenshot = jest.fn().mockResolvedValue(Buffer.from('mock-screenshot')) as jest.MockedFunction<any>;
      jest.doMock('screenshot-desktop', () => ({ default: mockScreenshot }));
      
      const result = await imageRecognition.captureGameWindow();
      expect(result).toBeDefined();
    });

    it('应该处理截图失败的情况', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockClear();
      mockScreenshotModule.mockRejectedValue(new Error('截图失败'));
      
      const result = await imageRecognition.captureGameWindow();
      expect(result).toBeNull();
    });

    it('应该使用缓存机制', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockClear();
      mockScreenshotModule.mockResolvedValue(Buffer.from('cached-screenshot'));
      
      // 第一次调用
      const result1 = await imageRecognition.captureGameWindow();
      expect(result1).not.toBeNull();
      
      // 第二次调用（应该使用缓存）
      const result2 = await imageRecognition.captureGameWindow();
      expect(result2).not.toBeNull();
      
      // 由于缓存间隔，screenshot应该只被调用一次
      expect(mockScreenshotModule).toHaveBeenCalledTimes(1);
    });
  });

  describe('findImage', () => {
    beforeEach(() => {
      // Mock fs.existsSync
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      
      // Mock Jimp.read
      const mockJimp = {
        bitmap: { width: 100, height: 100 },
        getPixelColor: () => mockJimpRgbaToInt(255, 0, 0, 255),
        crop: () => mockJimp
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
    });

    it('应该找到匹配的图像', async () => {
      const templatePath = 'test-template.png';
      
      // Mock captureGameWindow
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const result = await imageRecognition.findImage(templatePath);
      
      expect(result).toBeDefined();
      expect(typeof result.found).toBe('boolean');
      expect(typeof result.confidence).toBe('number');
    });

    it('应该处理模板文件不存在的情况', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      
      const result = await imageRecognition.findImage('non-existent.png');
      
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });

    it('应该处理截图失败的情况', async () => {
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(null);
      
      const result = await imageRecognition.findImage('test-template.png');
      
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });
  });

  describe('detectColor', () => {
    it('应该检测指定颜色范围', async () => {
      const colorRange = {
        r: { min: 200, max: 255 },
        g: { min: 0, max: 50 },
        b: { min: 0, max: 50 }
      };
      
      // Mock captureGameWindow
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      // Mock Jimp
      const mockJimp = {
        getWidth: () => 10,
        getHeight: () => 10,
        getPixelColor: () => mockJimpRgbaToInt(255, 0, 0, 255), // 红色像素
        crop: function() { return this; }
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
        mockJimpIntToRGBA.mockReturnValue({ r: 255, g: 0, b: 0, a: 255 });
      
      const result = await imageRecognition.detectColor(colorRange);
      
      expect(result).toBeDefined();
      expect(typeof result.found).toBe('boolean');
      expect(typeof result.confidence).toBe('number');
    });

    it('应该支持区域检测', async () => {
      const colorRange = {
        r: { min: 0, max: 255 },
        g: { min: 0, max: 255 },
        b: { min: 0, max: 255 }
      };
      
      const region = { x: 10, y: 10, width: 50, height: 50 };
      
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const mockJimp = {
        width: 50,
        height: 50,
        getPixelColor: () => mockJimpRgbaToInt(100, 100, 100, 255),
        clone: function() { return this; },
        crop: function() { return this; }
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      mockJimpIntToRGBA.mockReturnValue({ r: 100, g: 100, b: 100, a: 255 });
      
      const result = await imageRecognition.detectColor(colorRange, region);
      
      expect(result.position).toBeDefined();
      expect(result.position?.x).toBe(35); // region.x + region.width / 2
      expect(result.position?.y).toBe(35); // region.y + region.height / 2
    });
  });

  describe('recognizeGameScene', () => {
    it('应该识别已知游戏场景', async () => {
      // Mock模板文件存在
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      
      // Mock findImage返回高置信度结果
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 100 }
      });
      
      const result = await imageRecognition.recognizeGameScene();
      
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
    });

    it('应该处理未识别到场景的情况', async () => {
      // Mock模板文件不存在
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      
      const result = await imageRecognition.recognizeGameScene();
      
      expect(result).toBeNull();
    });

    it('应该处理低置信度的情况', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      
      // Mock findImage返回低置信度结果
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        confidence: 0.3
      });
      
      const result = await imageRecognition.recognizeGameScene();
      
      expect(result).toBeNull();
    });
  });

  describe('waitForImage', () => {
    it('应该在图像出现时立即返回', async () => {
      const templatePath = 'test-template.png';
      
      // Mock findImage立即返回成功结果
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: true,
        confidence: 0.9,
        position: { x: 100, y: 100 }
      });
      
      const startTime = Date.now();
      const result = await imageRecognition.waitForImage(templatePath, 5000, 100);
      const elapsed = Date.now() - startTime;
      
      expect(result.found).toBe(true);
      expect(elapsed).toBeLessThan(1000); // 应该很快返回
    });

    it('应该在超时后返回失败结果', async () => {
      const templatePath = 'test-template.png';
      
      // Mock findImage始终返回失败结果
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        confidence: 0.1
      });
      
      const startTime = Date.now();
      const result = await imageRecognition.waitForImage(templatePath, 1000, 100);
      const elapsed = Date.now() - startTime;
      
      expect(result.found).toBe(false);
      expect(elapsed).toBeGreaterThanOrEqual(1000); // 应该等待超时时间
    });
  });

  describe('getPixelColor', () => {
    it('应该返回指定坐标的像素颜色', async () => {
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const mockJimp = {
        width: 100,
        height: 100,
        getPixelColor: () => mockJimpRgbaToInt(255, 128, 64, 255)
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
        mockJimpIntToRGBA.mockReturnValue({ r: 255, g: 128, b: 64, a: 255 });
      
      const color = await imageRecognition.getPixelColor(50, 50);
      
      expect(color).toBeDefined();
      expect(color?.r).toBe(255);
      expect(color?.g).toBe(128);
      expect(color?.b).toBe(64);
      expect(color?.a).toBe(255);
    });

    it('应该处理坐标超出范围的情况', async () => {
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const mockJimp = {
        width: 100,
        height: 100,
        getPixelColor: () => mockJimpRgbaToInt(0, 0, 0, 255)
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      
      const color = await imageRecognition.getPixelColor(150, 150); // 超出范围
      
      expect(color).toBeNull();
    });
  });

  describe('缓存管理', () => {
    it('应该正确管理模板缓存', () => {
      const stats = imageRecognition.getCacheStats();
      expect(stats.templateCacheSize).toBe(0);
      expect(stats.hasScreenshotCache).toBe(false);
    });

    it('应该清理缓存', () => {
      imageRecognition.clearCache();
      const stats = imageRecognition.getCacheStats();
      expect(stats.templateCacheSize).toBe(0);
      expect(stats.hasScreenshotCache).toBe(false);
    });

    it('应该设置游戏窗口边界', () => {
      const bounds = { x: 100, y: 100, width: 800, height: 600 };
      imageRecognition.setGameWindowBounds(bounds);
      // 这里只是测试方法不会抛出错误
      expect(true).toBe(true);
    });
  });

  describe('配置更新', () => {
    it('应该更新配置', () => {
      const newConfig = {
        confidence: 0.9,
        timeout: 8000
      };
      
      imageRecognition.updateConfig(newConfig);
      // 这里只是测试方法不会抛出错误
      expect(true).toBe(true);
    });
  });

  describe('OCR文字识别', () => {
    it('应该识别文字区域', async () => {
      const result = await imageRecognition.recognizeText();
      expect(result).toHaveProperty('found');
      expect(result).toHaveProperty('confidence');
      expect(result).toHaveProperty('text');
    });

    it('应该支持区域文字识别', async () => {
      const region = { x: 10, y: 10, width: 100, height: 50 };
      const result = await imageRecognition.recognizeText(region);
      expect(result).toHaveProperty('found');
      expect(result).toHaveProperty('confidence');
    });

    it('应该处理OCR识别失败', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockRejectedValueOnce(new Error('截图失败'));
      
      const result = await imageRecognition.recognizeText();
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });
  });

  describe('模板缓存高级功能', () => {
    it('应该正确生成缓存键', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
      
      // 测试缓存键生成逻辑
      const result = await imageRecognition.findImage('test-template.png');
      expect(result).toHaveProperty('found');
    });

    it('应该在缓存满时清理旧缓存', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
      
      // 创建一个小缓存配置来测试缓存清理
      const smallCacheConfig = { ...mockConfig, templateCacheSize: 2 };
      const smallCacheRecognition = new ImageRecognition(smallCacheConfig);
      
      // 加载多个模板触发缓存清理
      await smallCacheRecognition.findImage('template1.png');
      await smallCacheRecognition.findImage('template2.png');
      await smallCacheRecognition.findImage('template3.png');
      
      const stats = smallCacheRecognition.getCacheStats();
      expect(stats.templateCacheSize).toBeLessThanOrEqual(2);
    });
  });

  describe('颜色检测高级功能', () => {
    it('应该正确计算匹配像素数量', async () => {
      const colorRange = {
        r: { min: 200, max: 255 },
        g: { min: 0, max: 50 },
        b: { min: 0, max: 50 }
      };
      
      const result = await imageRecognition.detectColor(colorRange);
      expect(result).toHaveProperty('found');
      expect(result).toHaveProperty('confidence');
      expect(typeof result.confidence).toBe('number');
    });

    it('应该处理颜色检测错误', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockRejectedValueOnce(new Error('截图失败'));
      
      const colorRange = {
        r: { min: 0, max: 255 },
        g: { min: 0, max: 255 },
        b: { min: 0, max: 255 }
      };
      
      const result = await imageRecognition.detectColor(colorRange);
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });
  });

  describe('场景识别高级功能', () => {
    it('应该处理模板文件不存在的场景', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(false);
      
      const result = await imageRecognition.recognizeGameScene();
      expect(result).toBeNull();
    });

    it('应该处理场景识别错误', async () => {
      // Mock findImage 方法抛出错误
      jest.spyOn(imageRecognition, 'findImage').mockRejectedValue(new Error('图像识别失败'));
      
      const result = await imageRecognition.recognizeGameScene();
      expect(result).toBeNull();
    });
  });

  describe('等待图像高级功能', () => {
    it('应该处理等待过程中的错误', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      
      // 模拟间歇性错误
      let callCount = 0;
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          throw new Error('临时错误');
        }
        return Promise.resolve(Buffer.from('mock-screenshot'));
      });
      
      const result = await imageRecognition.waitForImage('test.png', 2000, 100);
      expect(result).toHaveProperty('found');
    });
  });

  describe('工具方法', () => {
    it('应该正确检查模板文件存在性', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(false);
      
      const result = await imageRecognition.findImage('nonexistent.png');
      expect(result.found).toBe(false);
    });

    it('应该获取缓存统计信息', () => {
      const stats = imageRecognition.getCacheStats();
      expect(stats).toHaveProperty('templateCacheSize');
      expect(stats).toHaveProperty('hasScreenshotCache');
      expect(typeof stats.templateCacheSize).toBe('number');
      expect(typeof stats.hasScreenshotCache).toBe('boolean');
    });
  });

  describe('边界条件测试', () => {
    it('应该处理空截图缓冲区', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockResolvedValueOnce(null);
      
      const result = await imageRecognition.findImage('test.png');
      expect(result.found).toBe(false);
    });

    it('应该处理游戏窗口边界裁剪', async () => {
      // 设置游戏窗口边界
      imageRecognition.setGameWindowBounds({ x: 100, y: 100, width: 800, height: 600 });
      
      // Mock Jimp.read 和相关方法
      const mockCroppedImage = {
        getBuffer: jest.fn().mockResolvedValue(Buffer.from('cropped-screenshot'))
      };
      const mockFullImage = {
        clone: jest.fn().mockReturnValue({
          crop: jest.fn().mockReturnValue(mockCroppedImage)
        })
      };
      mockJimpRead.mockResolvedValueOnce(mockFullImage as any);
      
      const result = await imageRecognition.captureGameWindow();
      expect(result).not.toBeNull();
      expect(mockFullImage.clone).toHaveBeenCalled();
    });

    it('应该处理显示器列表为空的情况', async () => {
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.listDisplays.mockResolvedValueOnce([]);
      
      const result = await imageRecognition.captureGameWindow();
      expect(result).toBeNull();
    });

    it('应该处理模板加载失败', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockJimpRead.mockRejectedValueOnce(new Error('图像加载失败'));
      
      const result = await imageRecognition.findImage('invalid-template.png');
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });

    it('应该处理截图图像加载失败', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
      
      // 第一次调用成功（模板），第二次调用失败（截图）
      mockJimpRead
        .mockResolvedValueOnce({ bitmap: { width: 100, height: 100 } } as any)
        .mockRejectedValueOnce(new Error('截图加载失败'));
      
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const result = await imageRecognition.findImage('test.png');
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });
  });

  describe('高级功能测试', () => {
    it('应该处理颜色检测的基本功能', async () => {
      // Mock captureGameWindow 方法
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      // Mock Jimp 实例
      const mockJimp = {
        width: 2,
        height: 2,
        getPixelColor: jest.fn().mockReturnValue(mockJimpRgbaToInt(255, 0, 0, 255)),
        clone: function() { return this; },
        crop: function() { return this; }
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      mockJimpIntToRGBA.mockReturnValue({ r: 255, g: 0, b: 0, a: 255 });
      
      const colorRange = {
        r: { min: 200, max: 255 },
        g: { min: 0, max: 50 },
        b: { min: 0, max: 50 }
      };
      
      const result = await imageRecognition.detectColor(colorRange);
      // 验证方法能正常执行并返回结果
      expect(result).toHaveProperty('found');
      expect(result).toHaveProperty('confidence');
      expect(typeof result.confidence).toBe('number');
    });

    it('应该处理延时等待', async () => {
      // Mock findImage 方法，前几次返回未找到，最后一次返回找到
      let callCount = 0;
      jest.spyOn(imageRecognition, 'findImage').mockImplementation(async () => {
        callCount++;
        if (callCount < 4) {
          return { found: false, confidence: 0 };
        }
        return { found: true, confidence: 0.9 };
      });
      
      const start = Date.now();
      await imageRecognition.waitForImage('test.png', 1000, 50);
      const elapsed = Date.now() - start;
      expect(elapsed).toBeGreaterThanOrEqual(150); // 至少等待了一些时间
    });

    it('应该处理模板缓存键生成', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockFs.statSync.mockReturnValue({ mtime: new Date() });
      mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
      
      const mockJimp = {
        width: 100,
        height: 100,
        getPixelColor: jest.fn().mockReturnValue(mockJimpRgbaToInt(255, 255, 255, 255)),
        bitmap: { width: 100, height: 100 }
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      // 多次查找同一模板，应该使用缓存
      await imageRecognition.findImage('cached-template.png');
      await imageRecognition.findImage('cached-template.png');
      
      // 验证缓存统计
      const stats = imageRecognition.getCacheStats();
      expect(stats.templateCacheSize).toBeGreaterThan(0);
    });

    it('应该处理模板缓存清理', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(true);
      mockFs.statSync.mockReturnValue({ mtime: new Date() });
      mockFs.readFileSync.mockReturnValue(Buffer.from('mock-template'));
      
      const mockJimp = {
        width: 100,
        height: 100,
        getPixelColor: jest.fn().mockReturnValue(mockJimpRgbaToInt(255, 255, 255, 255)),
        bitmap: { width: 100, height: 100 }
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      
      // 创建小缓存配置
      const smallConfig = { ...mockConfig, templateCacheSize: 1 };
      const smallCacheRecognition = new ImageRecognition(smallConfig);
      
      jest.spyOn(smallCacheRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      // 加载两个不同模板，触发缓存清理
      await smallCacheRecognition.findImage('template1.png');
      await smallCacheRecognition.findImage('template2.png');
      
      const stats = smallCacheRecognition.getCacheStats();
      expect(stats.templateCacheSize).toBeLessThanOrEqual(1);
    });

    it('应该处理像素颜色获取', async () => {
      const mockJimp = {
        width: 100,
        height: 100,
        getPixelColor: jest.fn().mockReturnValue(mockJimpRgbaToInt(128, 64, 32, 255))
      };
      mockJimpRead.mockResolvedValue(mockJimp as any);
      mockJimpIntToRGBA.mockReturnValue({ r: 128, g: 64, b: 32, a: 255 });
      
      // 确保captureGameWindow返回有效的Buffer
      const mockScreenshotModule = require('screenshot-desktop');
      mockScreenshotModule.mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const color = await imageRecognition.getPixelColor(10, 20);
      expect(color).toEqual({ r: 128, g: 64, b: 32, a: 255 });
    });

    it('应该处理配置更新', () => {
      const newConfig = {
        confidence: 0.9,
        timeout: 10000,
        templateCacheSize: 20,
        screenshotInterval: 200
      };
      
      imageRecognition.updateConfig(newConfig);
      
      // 验证配置已更新（通过行为验证）
      expect(imageRecognition).toBeDefined();
    });
  });

  describe('静态方法', () => {
    it('应该创建模板目录', () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(false);
      
      ImageRecognition.createTemplateDirectories();
      
      expect(mockFs.mkdirSync).toHaveBeenCalled();
    });

    it('应该处理模板文件不存在的情况', async () => {
      const mockFs = require('fs');
      mockFs.existsSync.mockReturnValue(false);
      
      jest.spyOn(imageRecognition, 'captureGameWindow').mockResolvedValue(Buffer.from('mock-screenshot'));
      
      const result = await imageRecognition.findImage('nonexistent.png');
      expect(result.found).toBe(false);
      expect(result.confidence).toBe(0);
    });
  });
});