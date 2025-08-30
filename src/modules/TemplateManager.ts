import * as path from 'path';
import * as fs from 'fs';
import { ImageRecognition } from './ImageRecognition';

/**
 * 模板类型枚举
 */
export enum TemplateType {
  SCENE = 'scenes',
  BUTTON = 'buttons', 
  ICON = 'icons',
  UI = 'ui',
  DAILY = 'daily'
}

/**
 * 游戏场景枚举
 */
export enum GameScene {
  MAIN_MENU = 'main_menu',
  BATTLE = 'battle',
  DIALOG = 'dialog',
  COMMISSION = 'commission',
  LOADING = 'loading',
  UNKNOWN = 'unknown'
}

/**
 * UI元素定义
 */
export interface UIElement {
  name: string;
  templatePath: string;
  position?: { x: number; y: number };
  size?: { width: number; height: number };
  confidence: number;
  threshold?: number;
}

/**
 * 模板信息
 */
export interface TemplateInfo {
  name: string;
  path: string;
  type: TemplateType;
  scene?: GameScene;
  description?: string;
  threshold?: number;
  lastModified: number;
}

/**
 * 场景检测结果
 */
export interface SceneDetectionResult {
  scene: GameScene;
  confidence: number;
  elements: UIElement[];
  timestamp: number;
}

/**
 * 模板匹配结果
 */
export interface TemplateMatchResult {
  found: boolean;
  confidence: number;
  position?: { x: number; y: number };
  templateName: string;
}

/**
 * 模板管理器配置
 */
export interface TemplateManagerConfig {
  templatesPath: string;
  cacheEnabled: boolean;
  defaultThreshold: number;
  maxCacheSize: number;
}

/**
 * 模板管理器类
 * 负责加载、缓存和管理游戏界面模板
 */
export class TemplateManager {
  private config: TemplateManagerConfig;
  private templateCache: Map<string, TemplateInfo> = new Map();
  private imageRecognition: ImageRecognition;
  private isInitialized: boolean = false;

  constructor(config?: Partial<TemplateManagerConfig>) {
    this.config = {
      templatesPath: path.join(process.cwd(), 'templates'),
      cacheEnabled: true,
      defaultThreshold: 0.8,
      maxCacheSize: 100,
      ...config
    };
    
    this.imageRecognition = new ImageRecognition();
  }

  /**
   * 初始化模板管理器
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      await this.loadAllTemplates();
      this.isInitialized = true;
      console.log(`TemplateManager initialized with ${this.templateCache.size} templates`);
    } catch (error) {
      console.error('Failed to initialize TemplateManager:', error);
      throw error;
    }
  }

  /**
   * 加载所有模板文件
   */
  private async loadAllTemplates(): Promise<void> {
    const templateTypes = Object.values(TemplateType);
    
    for (const type of templateTypes) {
      const typePath = path.join(this.config.templatesPath, type);
      
      if (fs.existsSync(typePath)) {
        await this.loadTemplatesFromDirectory(typePath, type);
      }
    }
  }

  /**
   * 从指定目录加载模板
   */
  private async loadTemplatesFromDirectory(dirPath: string, type: TemplateType): Promise<void> {
    try {
      const files = fs.readdirSync(dirPath);
      
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isFile() && this.isImageFile(file)) {
          const templateInfo: TemplateInfo = {
            name: path.parse(file).name,
            path: filePath,
            type,
            lastModified: stat.mtime.getTime(),
            threshold: this.config.defaultThreshold
          };
          
          // 根据文件名推断场景
          templateInfo.scene = this.inferSceneFromFileName(file);
          
          const cacheKey = this.generateCacheKey(type, templateInfo.name);
          this.templateCache.set(cacheKey, templateInfo);
        }
      }
    } catch (error) {
      console.error(`Failed to load templates from ${dirPath}:`, error);
    }
  }

  /**
   * 检查是否为图像文件
   */
  private isImageFile(filename: string): boolean {
    const imageExtensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif'];
    const ext = path.extname(filename).toLowerCase();
    return imageExtensions.includes(ext);
  }

  /**
   * 从文件名推断游戏场景
   */
  private inferSceneFromFileName(filename: string): GameScene {
    const name = filename.toLowerCase();
    
    if (name.includes('main') || name.includes('menu')) {
      return GameScene.MAIN_MENU;
    }
    if (name.includes('battle') || name.includes('combat')) {
      return GameScene.BATTLE;
    }
    if (name.includes('dialog') || name.includes('conversation')) {
      return GameScene.DIALOG;
    }
    if (name.includes('commission') || name.includes('daily')) {
      return GameScene.COMMISSION;
    }
    if (name.includes('loading')) {
      return GameScene.LOADING;
    }
    
    return GameScene.UNKNOWN;
  }

  /**
   * 生成缓存键
   */
  private generateCacheKey(type: TemplateType, name: string): string {
    return `${type}:${name}`;
  }

  /**
   * 获取指定类型的所有模板
   */
  getTemplatesByType(type: TemplateType): TemplateInfo[] {
    const templates: TemplateInfo[] = [];
    
    for (const [key, template] of this.templateCache) {
      if (template.type === type) {
        templates.push(template);
      }
    }
    
    return templates;
  }

  /**
   * 获取指定场景的所有模板
   */
  getTemplatesByScene(scene: GameScene): TemplateInfo[] {
    const templates: TemplateInfo[] = [];
    
    for (const [key, template] of this.templateCache) {
      if (template.scene === scene) {
        templates.push(template);
      }
    }
    
    return templates;
  }

  /**
   * 根据名称获取模板
   */
  getTemplate(type: TemplateType, name: string): TemplateInfo | undefined {
    const cacheKey = this.generateCacheKey(type, name);
    return this.templateCache.get(cacheKey);
  }

  /**
   * 在屏幕截图中查找模板
   */
  async findTemplate(
    screenshotPath: string, 
    templateName: string, 
    type: TemplateType,
    threshold?: number
  ): Promise<TemplateMatchResult> {
    const template = this.getTemplate(type, templateName);
    
    if (!template) {
      return {
        found: false,
        confidence: 0,
        templateName
      };
    }

    try {
      // 读取截图文件
      const screenshotBuffer = await fs.promises.readFile(screenshotPath);
      const result = await this.imageRecognition.findImage(
        template.path,
        screenshotBuffer
      );

      return {
        found: result.found,
        confidence: result.confidence,
        position: result.found ? result.position : undefined,
        templateName
      };
    } catch (error) {
      console.error(`Failed to find template ${templateName}:`, error);
      return {
        found: false,
        confidence: 0,
        templateName
      };
    }
  }

  /**
   * 在屏幕截图中查找多个模板
   */
  async findMultipleTemplates(
    screenshotPath: string,
    templates: Array<{ name: string; type: TemplateType; threshold?: number }>
  ): Promise<TemplateMatchResult[]> {
    const results: TemplateMatchResult[] = [];
    
    for (const templateConfig of templates) {
      const result = await this.findTemplate(
        screenshotPath,
        templateConfig.name,
        templateConfig.type,
        templateConfig.threshold
      );
      results.push(result);
    }
    
    return results;
  }

  /**
   * 获取每日委托相关的所有模板
   */
  getDailyCommissionTemplates(): TemplateInfo[] {
    return this.getTemplatesByType(TemplateType.DAILY);
  }

  /**
   * 检查模板是否存在
   */
  hasTemplate(type: TemplateType, name: string): boolean {
    const cacheKey = this.generateCacheKey(type, name);
    return this.templateCache.has(cacheKey);
  }

  /**
   * 获取模板统计信息
   */
  getStats(): {
    totalTemplates: number;
    templatesByType: Record<TemplateType, number>;
    templatesByScene: Record<GameScene, number>;
  } {
    const stats = {
      totalTemplates: this.templateCache.size,
      templatesByType: {} as Record<TemplateType, number>,
      templatesByScene: {} as Record<GameScene, number>
    };

    // 初始化计数器
    Object.values(TemplateType).forEach(type => {
      stats.templatesByType[type] = 0;
    });
    Object.values(GameScene).forEach(scene => {
      stats.templatesByScene[scene] = 0;
    });

    // 统计模板数量
    for (const template of this.templateCache.values()) {
      stats.templatesByType[template.type]++;
      if (template.scene) {
        stats.templatesByScene[template.scene]++;
      }
    }

    return stats;
  }

  /**
   * 重新加载模板
   */
  async reload(): Promise<void> {
    this.templateCache.clear();
    this.isInitialized = false;
    await this.initialize();
  }

  /**
   * 清理缓存
   */
  clearCache(): void {
    this.templateCache.clear();
  }

  /**
   * 获取模板路径
   */
  getTemplatesPath(): string {
    return this.config.templatesPath;
  }

  /**
   * 检查初始化状态
   */
  isReady(): boolean {
    return this.isInitialized;
  }
}