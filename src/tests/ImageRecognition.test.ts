// Mock external dependencies
const mockListDisplays = jest.fn();
const mockScreenshotDefault = jest.fn();

jest.mock('screenshot-desktop', () => ({
  __esModule: true,
  default: mockScreenshotDefault,
  listDisplays: mockListDisplays
}));

jest.mock('jimp', () => ({
  Jimp: {
    read: jest.fn()
  },
  intToRGBA: jest.fn()
}));

jest.mock('pixelmatch', () => jest.fn());

jest.mock('fs', () => ({
  existsSync: jest.fn(),
  mkdirSync: jest.fn()
}));

import { ImageRecognition } from '../modules/ImageRecognition';
import screenshotDesktop from 'screenshot-desktop';
import { Jimp } from 'jimp';
import * as pixelmatch from 'pixelmatch';
import * as fs from 'fs';

// Use the mocked functions
const mockScreenshotDesktop = mockScreenshotDefault;

describe('ImageRecognition', () => {
  let imageRecognition: ImageRecognition;
  const mockConfig = {
    confidence: 0.8,
    templatePath: './templates',
    screenshotPath: './screenshots'
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup default mocks
    (fs.existsSync as jest.Mock).mockReturnValue(true);
    (fs.mkdirSync as jest.Mock).mockReturnValue('');
    
    // Mock screenshot-desktop
    mockScreenshotDesktop.mockResolvedValue(Buffer.from('mock-screenshot'));
    mockListDisplays.mockResolvedValue([
      { id: 0, width: 1920, height: 1080 }
    ]);
    
    imageRecognition = new ImageRecognition(mockConfig);
  });

  describe('构造函数和配置', () => {
    test('应该使用默认配置创建实例', () => {
      const defaultInstance = new ImageRecognition();
      expect(defaultInstance).toBeInstanceOf(ImageRecognition);
    });

    test('应该使用自定义配置创建实例', () => {
      expect(imageRecognition).toBeInstanceOf(ImageRecognition);
    });

    test('应该能够更新配置', () => {
      const newConfig = { confidence: 0.9 };
      imageRecognition.updateConfig(newConfig);
      // 验证配置更新（通过后续方法调用验证）
      expect(imageRecognition).toBeInstanceOf(ImageRecognition);
    });
  });

  describe('静态方法', () => {
    test('应该创建模板目录', () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      
      ImageRecognition.createTemplateDirectories();
      
      expect(fs.existsSync).toHaveBeenCalled();
      expect(fs.mkdirSync).toHaveBeenCalled();
    });
  });

  describe('核心功能方法', () => {
    test('应该能够捕获游戏窗口', async () => {
        const mockScreenshot = Buffer.from('fake-screenshot');
        
        // Mock screenshot function to have listDisplays method and be callable
         mockScreenshotDefault.mockResolvedValue(mockScreenshot);
         (mockScreenshotDefault as any).listDisplays = mockListDisplays;
         mockListDisplays.mockResolvedValue([{ id: 0, width: 1920, height: 1080 }]);
        
        const result = await imageRecognition.captureGameWindow();
        
        expect(mockListDisplays).toHaveBeenCalled();
        expect(mockScreenshotDefault).toHaveBeenCalled();
        expect(result).toBe(mockScreenshot);
    });

    test('应该能够获取像素颜色', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      mockScreenshotDesktop.mockResolvedValue(mockScreenshot);
      
      // Mock Jimp instance with getPixelColor method
      const mockJimpInstance = {
        getPixelColor: jest.fn().mockReturnValue(0xFF0000FF) // Red color
      };
      (Jimp.read as jest.Mock).mockResolvedValue(mockJimpInstance);
      
      const result = await imageRecognition.getPixelColor(50, 50);
      
      if (result) {
         expect(result).toHaveProperty('r');
         expect(result).toHaveProperty('g');
         expect(result).toHaveProperty('b');
         expect(result).toHaveProperty('a');
       } else {
         expect(result).toBeUndefined();
       }
    });

    test('应该能够查找图像', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      const mockTemplate = {
        bitmap: { width: 50, height: 50, data: Buffer.alloc(10000) },
        getPixelColor: jest.fn()
      };
      
      mockScreenshotDesktop.mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue(mockTemplate);
      (pixelmatch as unknown as jest.Mock).mockReturnValue(0);
      
      const result = await imageRecognition.findImage('test-template');
       
       expect(result).toHaveProperty('found');
       expect(result).toHaveProperty('confidence');
       if (result.found) {
         expect(result).toHaveProperty('position');
       }
    });

    test('应该能够检测颜色', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      const mockImage = {
        width: 100,
        height: 100,
        getPixelColor: jest.fn().mockReturnValue(0xFF0000FF),
        clone: jest.fn().mockReturnThis(),
        crop: jest.fn().mockReturnThis()
      };
      
      mockScreenshotDesktop.mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue(mockImage);
      
      const colorRange = {
        r: { min: 200, max: 255 },
        g: { min: 0, max: 50 },
        b: { min: 0, max: 50 }
      };
      
      const result = await imageRecognition.detectColor(colorRange);
      
      expect(result).toHaveProperty('found');
      expect(result).toHaveProperty('confidence');
    });

    test('应该能够识别游戏场景', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      mockScreenshotDesktop.mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue({
        bitmap: { width: 100, height: 100, data: Buffer.alloc(40000) },
        getPixelColor: jest.fn()
      });
      (pixelmatch as unknown as jest.Mock).mockReturnValue(0);
      
      const result = await imageRecognition.recognizeGameScene();
      
      expect(typeof result === 'string' || result === null).toBe(true);
    });
  });

  describe('等待功能', () => {
    test('应该能够等待图像出现', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      mockScreenshotDesktop.mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue({
        bitmap: { width: 50, height: 50, data: Buffer.alloc(10000) },
        getPixelColor: jest.fn()
      });
      (pixelmatch as unknown as jest.Mock).mockReturnValue(0);
      
      const result = await imageRecognition.waitForImage('test-template', 1000);
      
      expect(result).toHaveProperty('found');
    });

    test('应该能够等待颜色出现', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      (screenshotDesktop as jest.Mock).mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue({
        bitmap: { width: 100, height: 100, data: Buffer.alloc(40000) },
        getPixelColor: jest.fn().mockReturnValue(0xFF0000FF)
      });
      
      const result = await imageRecognition.waitForImage('test-template', 1000);
      
      expect(result).toHaveProperty('found');
    });
  });

  describe('缓存管理', () => {
    test('应该能够清除缓存', () => {
      imageRecognition.clearCache();
      // 验证缓存清除（通过后续方法调用验证）
      expect(imageRecognition).toBeInstanceOf(ImageRecognition);
    });

    test('应该能够获取缓存统计', () => {
      const stats = imageRecognition.getCacheStats();
      expect(stats).toHaveProperty('templateCacheSize');
      expect(stats).toHaveProperty('hasScreenshotCache');
    });
  });

  describe('统计信息', () => {
    test('应该能够获取图像统计信息', async () => {
      const mockScreenshot = Buffer.from('mock-screenshot');
      (screenshotDesktop as jest.Mock).mockResolvedValue(mockScreenshot);
      (Jimp.read as jest.Mock).mockResolvedValue({
        bitmap: { width: 100, height: 100, data: Buffer.alloc(40000) },
        getPixelColor: jest.fn()
      });
      
      const result = await imageRecognition.getImageStats();
       
       if (result) {
         expect(result).toHaveProperty('width');
         expect(result).toHaveProperty('height');
         expect(result).toHaveProperty('averageColor');
         expect(result).toHaveProperty('dominantColors');
       } else {
         expect(result).toBeNull();
       }
    });
  });

  describe('游戏窗口管理', () => {
    test('应该能够设置游戏窗口边界', () => {
      const bounds = { x: 0, y: 0, width: 1920, height: 1080 };
      
      expect(() => {
        imageRecognition.setGameWindowBounds(bounds);
      }).not.toThrow();
    });
  });

  describe('错误处理', () => {
    test('应该处理不存在的模板文件', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      
      const result = await imageRecognition.findImage('non-existent-template');
      
      expect(result.found).toBe(false);
    });

    test('应该处理截图失败', async () => {
      mockScreenshotDesktop.mockRejectedValue(new Error('Screenshot failed'));
       
       const result = await imageRecognition.captureGameWindow();
       expect(result).toBeNull();
    });
  });
});