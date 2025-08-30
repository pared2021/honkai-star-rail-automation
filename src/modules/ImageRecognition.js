// 图像识别模块
// import { GameStatus } from '../types';
import { isBrowser } from '../utils/browserCompat.js';
import screenshot from 'screenshot-desktop';
import { Jimp, intToRGBA } from 'jimp';
import { createHash } from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as pixelmatch from 'pixelmatch';
export class ImageRecognition {
    constructor(config = {}) {
        Object.defineProperty(this, "config", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "templateCache", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "lastScreenshot", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "lastScreenshotTime", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 0
        });
        Object.defineProperty(this, "gameWindowBounds", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "logger", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.config = {
            confidence: 0.8,
            timeout: 5000,
            retryCount: 3,
            templateCacheSize: 50,
            screenshotInterval: 100,
            ...config
        };
        this.logger = {
            info: (msg) => console.log(`[ImageRecognition] ${msg}`),
            error: (msg, error) => console.error(`[ImageRecognition] ${msg}`, error),
            debug: (msg) => console.debug(`[ImageRecognition] ${msg}`)
        };
    }
    /**
     * 截取游戏窗口截图
     */
    async captureGameWindow() {
        try {
            const now = Date.now();
            // 检查是否需要重新截图（基于间隔时间）
            if (this.lastScreenshot &&
                now - this.lastScreenshotTime < this.config.screenshotInterval) {
                this.logger.debug('使用缓存的截图');
                return this.lastScreenshot;
            }
            // 浏览器环境中无法截图
            if (isBrowser || !screenshot) {
                this.logger.debug('浏览器环境中无法执行屏幕截图');
                return null;
            }
            this.logger.debug('开始截取屏幕...');
            // 获取所有显示器的截图
            const displays = await screenshot.listDisplays();
            if (displays.length === 0) {
                throw new Error('未找到可用的显示器');
            }
            // 截取主显示器
            const mainDisplay = displays[0];
            const screenshotBuffer = await screenshot({
                screen: mainDisplay.id,
                format: 'png'
            });
            // 如果设置了游戏窗口边界，裁剪截图
            if (this.gameWindowBounds) {
                const fullImage = await Jimp.read(screenshotBuffer);
                const croppedImage = fullImage.clone().crop({
                    x: this.gameWindowBounds.x,
                    y: this.gameWindowBounds.y,
                    w: this.gameWindowBounds.width,
                    h: this.gameWindowBounds.height
                });
                const croppedBuffer = await croppedImage.getBuffer('image/png');
                this.lastScreenshot = croppedBuffer;
                this.lastScreenshotTime = now;
                this.logger.debug(`截图完成，裁剪区域: ${this.gameWindowBounds.width}x${this.gameWindowBounds.height}`);
                return croppedBuffer;
            }
            this.lastScreenshot = screenshotBuffer;
            this.lastScreenshotTime = now;
            this.logger.debug(`截图完成，尺寸: ${mainDisplay.width}x${mainDisplay.height}`);
            return screenshotBuffer;
        }
        catch (error) {
            this.logger.error('截图失败:', error);
            return null;
        }
    }
    /**
     * 在截图中查找指定图像
     */
    async findImage(templatePath, screenshot) {
        try {
            this.logger.debug(`开始查找图像: ${templatePath}`);
            // 获取截图
            const screenshotBuffer = screenshot || await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            // 加载模板图像
            const template = await this.loadTemplate(templatePath);
            if (!template) {
                throw new Error(`无法加载模板图像: ${templatePath}`);
            }
            // 加载截图
            const screenshotImage = await Jimp.read(screenshotBuffer);
            // 执行模板匹配
            const matchResult = await this.performTemplateMatch(screenshotImage, template);
            if (matchResult.confidence >= this.config.confidence) {
                this.logger.debug(`图像匹配成功: ${templatePath}, 置信度: ${matchResult.confidence.toFixed(3)}`);
                return {
                    found: true,
                    confidence: matchResult.confidence,
                    position: matchResult.position,
                    matchRegion: matchResult.region
                };
            }
            else {
                this.logger.debug(`图像匹配失败: ${templatePath}, 置信度: ${matchResult.confidence.toFixed(3)} < ${this.config.confidence}`);
                return {
                    found: false,
                    confidence: matchResult.confidence
                };
            }
        }
        catch (error) {
            this.logger.error('图像识别失败:', error);
            return {
                found: false,
                confidence: 0
            };
        }
    }
    /**
     * 加载模板图像
     */
    async loadTemplate(templatePath) {
        try {
            // 检查缓存
            const cacheKey = this.getTemplateCacheKey(templatePath);
            if (this.templateCache.has(cacheKey)) {
                return this.templateCache.get(cacheKey);
            }
            // 检查文件是否存在
            if (!fs.existsSync(templatePath)) {
                this.logger.error(`模板文件不存在: ${templatePath}`);
                return null;
            }
            // 加载图像
            const template = await Jimp.read(templatePath);
            // 添加到缓存
            this.addToTemplateCache(cacheKey, template);
            return template;
        }
        catch (error) {
            this.logger.error(`加载模板失败: ${templatePath}`, error);
            return null;
        }
    }
    /**
     * 执行模板匹配
     */
    async performTemplateMatch(screenshot, template) {
        const screenshotWidth = screenshot.width;
        const screenshotHeight = screenshot.height;
        const templateWidth = template.width;
        const templateHeight = template.height;
        let bestMatch = {
            confidence: 0,
            position: { x: 0, y: 0 },
            region: { x: 0, y: 0, width: templateWidth, height: templateHeight }
        };
        // 滑动窗口匹配
        for (let y = 0; y <= screenshotHeight - templateHeight; y += 2) {
            for (let x = 0; x <= screenshotWidth - templateWidth; x += 2) {
                const confidence = this.calculateSimilarity(screenshot, template, x, y, templateWidth, templateHeight);
                if (confidence > bestMatch.confidence) {
                    bestMatch = {
                        confidence,
                        position: { x: x + templateWidth / 2, y: y + templateHeight / 2 },
                        region: { x, y, width: templateWidth, height: templateHeight }
                    };
                }
            }
        }
        return bestMatch;
    }
    /**
     * 计算图像相似度
     */
    calculateSimilarity(screenshot, template, startX, startY, width, height) {
        let totalDiff = 0;
        let pixelCount = 0;
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const screenshotColorInt = screenshot.getPixelColor(startX + x, startY + y);
                const templateColorInt = template.getPixelColor(x, y);
                const screenshotColor = intToRGBA(screenshotColorInt);
                const templateColor = intToRGBA(templateColorInt);
                const rDiff = Math.abs(screenshotColor.r - templateColor.r);
                const gDiff = Math.abs(screenshotColor.g - templateColor.g);
                const bDiff = Math.abs(screenshotColor.b - templateColor.b);
                totalDiff += (rDiff + gDiff + bDiff) / 3;
                pixelCount++;
            }
        }
        const avgDiff = totalDiff / pixelCount;
        return Math.max(0, 1 - (avgDiff / 255));
    }
    /**
     * OCR文字识别（简化版本）
     */
    async recognizeText(region) {
        try {
            this.logger.debug('开始OCR文字识别...');
            // 获取截图
            const screenshotBuffer = await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            let image = await Jimp.read(screenshotBuffer);
            // 如果指定了区域，裁剪图像
            if (region) {
                image = image.clone().crop({ x: region.x, y: region.y, w: region.width, h: region.height });
            }
            // 简单的文字检测（基于颜色和形状）
            const textRegions = this.detectTextRegions(image);
            return {
                found: textRegions.length > 0,
                confidence: textRegions.length > 0 ? 0.8 : 0,
                text: textRegions.length > 0 ? '检测到文字区域' : ''
            };
        }
        catch (error) {
            this.logger.error('OCR识别失败:', error);
            return {
                found: false,
                confidence: 0,
                text: ''
            };
        }
    }
    /**
     * 模板缓存管理
     */
    getTemplateCacheKey(templatePath) {
        const stats = fs.statSync(templatePath);
        return createHash('md5').update(templatePath + stats.mtime.getTime()).digest('hex');
    }
    addToTemplateCache(key, template) {
        if (this.templateCache.size >= this.config.templateCacheSize) {
            const firstKey = this.templateCache.keys().next().value;
            this.templateCache.delete(firstKey);
        }
        this.templateCache.set(key, template);
    }
    /**
     * 检测文字区域（简化版本）
     */
    detectTextRegions(image) {
        const regions = [];
        const width = image.width;
        const height = image.height;
        // 简单的边缘检测来寻找文字区域
        for (let y = 0; y < height - 10; y += 5) {
            for (let x = 0; x < width - 10; x += 5) {
                if (this.isTextLikeRegion(image, x, y, 10, 10)) {
                    regions.push({ x, y, width: 10, height: 10 });
                }
            }
        }
        return regions;
    }
    /**
     * 判断是否为文字区域
     */
    isTextLikeRegion(image, x, y, width, height) {
        let edgeCount = 0;
        let totalPixels = 0;
        for (let dy = 0; dy < height - 1; dy++) {
            for (let dx = 0; dx < width - 1; dx++) {
                const currentColorInt = image.getPixelColor(x + dx, y + dy);
                const rightColorInt = image.getPixelColor(x + dx + 1, y + dy);
                const bottomColorInt = image.getPixelColor(x + dx, y + dy + 1);
                const currentColor = intToRGBA(currentColorInt);
                const rightColor = intToRGBA(rightColorInt);
                const bottomColor = intToRGBA(bottomColorInt);
                const rightDiff = Math.abs(currentColor.r - rightColor.r) +
                    Math.abs(currentColor.g - rightColor.g) +
                    Math.abs(currentColor.b - rightColor.b);
                const bottomDiff = Math.abs(currentColor.r - bottomColor.r) +
                    Math.abs(currentColor.g - bottomColor.g) +
                    Math.abs(currentColor.b - bottomColor.b);
                if (rightDiff > 50 || bottomDiff > 50) {
                    edgeCount++;
                }
                totalPixels++;
            }
        }
        return (edgeCount / totalPixels) > 0.3;
    }
    /**
     * 颜色检测
     */
    async detectColor(colorRange, region) {
        try {
            const screenshotBuffer = await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            let image = await Jimp.read(screenshotBuffer);
            if (region) {
                image = image.clone().crop({ x: region.x, y: region.y, w: region.width, h: region.height });
            }
            const matchingPixels = this.countMatchingPixels(image, colorRange);
            const totalPixels = image.width * image.height;
            const confidence = matchingPixels / totalPixels;
            return {
                found: confidence >= this.config.confidence,
                confidence,
                position: region ? { x: region.x + region.width / 2, y: region.y + region.height / 2 } : undefined
            };
        }
        catch (error) {
            this.logger.error('颜色检测失败:', error);
            return {
                found: false,
                confidence: 0
            };
        }
    }
    /**
     * 计算匹配颜色的像素数量
     */
    countMatchingPixels(image, colorRange) {
        let count = 0;
        const width = image.width;
        const height = image.height;
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const colorInt = image.getPixelColor(x, y);
                const color = intToRGBA(colorInt);
                if (color.r >= colorRange.r.min && color.r <= colorRange.r.max &&
                    color.g >= colorRange.g.min && color.g <= colorRange.g.max &&
                    color.b >= colorRange.b.min && color.b <= colorRange.b.max) {
                    count++;
                }
            }
        }
        return count;
    }
    /**
     * 识别当前游戏场景
     */
    async recognizeGameScene() {
        try {
            this.logger.debug('开始识别游戏场景...');
            const sceneTemplates = {
                'main_menu': 'templates/scenes/main_menu.png',
                'world_map': 'templates/scenes/world_map.png',
                'battle': 'templates/scenes/battle.png',
                'inventory': 'templates/scenes/inventory.png',
                'character': 'templates/scenes/character.png',
                'mission': 'templates/scenes/mission.png',
                'shop': 'templates/scenes/shop.png'
            };
            let bestMatch = { scene: null, confidence: 0 };
            for (const [sceneName, templatePath] of Object.entries(sceneTemplates)) {
                const fullTemplatePath = path.join(process.cwd(), templatePath);
                if (fs.existsSync(fullTemplatePath)) {
                    const result = await this.findImage(fullTemplatePath);
                    if (result.confidence > bestMatch.confidence) {
                        bestMatch = { scene: sceneName, confidence: result.confidence };
                    }
                }
            }
            if (bestMatch.confidence >= this.config.confidence) {
                this.logger.debug(`识别到场景: ${bestMatch.scene}, 置信度: ${bestMatch.confidence.toFixed(3)}`);
                return bestMatch.scene;
            }
            this.logger.debug('未识别到已知场景');
            return null;
        }
        catch (error) {
            this.logger.error('场景识别失败:', error);
            return null;
        }
    }
    /**
     * 等待指定图像出现
     */
    async waitForImage(templatePath, timeout = 10000, interval = 500) {
        const startTime = Date.now();
        this.logger.debug(`开始等待图像: ${templatePath}, 超时时间: ${timeout}ms`);
        while (Date.now() - startTime < timeout) {
            try {
                const result = await this.findImage(templatePath);
                if (result.found) {
                    const elapsed = Date.now() - startTime;
                    this.logger.debug(`图像找到: ${templatePath}, 耗时: ${elapsed}ms, 置信度: ${result.confidence.toFixed(3)}`);
                    return result;
                }
                // 等待指定间隔后重试
                await new Promise(resolve => setTimeout(resolve, interval));
            }
            catch (error) {
                this.logger.error('等待图像时出错:', error);
                await new Promise(resolve => setTimeout(resolve, interval));
            }
        }
        const elapsed = Date.now() - startTime;
        this.logger.debug(`等待超时: ${templatePath}, 总耗时: ${elapsed}ms`);
        return {
            found: false,
            confidence: 0
        };
    }
    /**
     * 获取像素颜色
     */
    async getPixelColor(x, y) {
        try {
            const screenshotBuffer = await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            const image = await Jimp.read(screenshotBuffer);
            if (x < 0 || x >= image.width || y < 0 || y >= image.height) {
                this.logger.error(`坐标超出范围: (${x}, ${y})`);
                return null;
            }
            const colorInt = image.getPixelColor(x, y);
            const color = intToRGBA(colorInt);
            return color;
        }
        catch (error) {
            this.logger.error('获取像素颜色失败:', error);
            return null;
        }
    }
    /**
     * 清理缓存
     */
    clearCache() {
        this.templateCache.clear();
        this.lastScreenshot = null;
        this.lastScreenshotTime = 0;
        this.logger.debug('缓存已清理');
    }
    /**
     * 设置游戏窗口边界
     */
    setGameWindowBounds(bounds) {
        this.gameWindowBounds = bounds;
        this.logger.debug(`设置游戏窗口边界: ${JSON.stringify(bounds)}`);
    }
    /**
     * 获取缓存统计信息
     */
    getCacheStats() {
        return {
            templateCacheSize: this.templateCache.size,
            hasScreenshotCache: this.lastScreenshot !== null
        };
    }
    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    /**
     * 检查模板文件是否存在
     */
    checkTemplateExists(templatePath) {
        if (!fs.existsSync(templatePath)) {
            this.logger.error(`模板文件不存在: ${templatePath}`);
            return false;
        }
        return true;
    }
    /**
     * 创建模板目录
     */
    static createTemplateDirectories() {
        const templateDirs = [
            'templates/scenes',
            'templates/ui',
            'templates/buttons',
            'templates/icons'
        ];
        templateDirs.forEach(dir => {
            const fullPath = path.join(process.cwd(), dir);
            if (!fs.existsSync(fullPath)) {
                fs.mkdirSync(fullPath, { recursive: true });
                console.log(`创建模板目录: ${fullPath}`);
            }
        });
    }
    /**
     * 更新配置
     */
    updateConfig(config) {
        this.config = { ...this.config, ...config };
    }
    /**
     * 获取当前配置
     */
    getConfig() {
        return { ...this.config };
    }
    /**
     * 多模板匹配 - 在一张截图中查找多个模板
     */
    async findMultipleImages(templatePaths, screenshot) {
        const results = new Map();
        try {
            // 获取截图（只截取一次）
            const screenshotBuffer = screenshot || await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            // 并行处理所有模板
            const promises = templatePaths.map(async (templatePath) => {
                const result = await this.findImage(templatePath, screenshotBuffer);
                return { templatePath, result };
            });
            const allResults = await Promise.all(promises);
            allResults.forEach(({ templatePath, result }) => {
                results.set(templatePath, result);
            });
        }
        catch (error) {
            this.logger.error('多模板匹配失败:', error);
        }
        return results;
    }
    /**
     * 保存截图到文件
     */
    async saveScreenshot(filename) {
        try {
            const screenshotBuffer = await this.captureGameWindow();
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const defaultFilename = `screenshot_${timestamp}.png`;
            const filepath = path.join(process.cwd(), 'screenshots', filename || defaultFilename);
            // 确保目录存在
            const dir = path.dirname(filepath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(filepath, screenshotBuffer);
            this.logger.info(`截图已保存: ${filepath}`);
            return filepath;
        }
        catch (error) {
            this.logger.error('保存截图失败:', error);
            return null;
        }
    }
    /**
     * 区域截图
     */
    async captureRegion(region) {
        try {
            const fullScreenshot = await this.captureGameWindow();
            if (!fullScreenshot) {
                throw new Error('无法获取截图');
            }
            const image = await Jimp.read(fullScreenshot);
            const croppedImage = image.clone().crop({
                x: region.x,
                y: region.y,
                w: region.width,
                h: region.height
            });
            return await croppedImage.getBuffer('image/png');
        }
        catch (error) {
            this.logger.error('区域截图失败:', error);
            return null;
        }
    }
    /**
     * 图像差异检测
     */
    async detectImageDifference(templatePath, threshold = 0.1) {
        try {
            const currentScreenshot = await this.captureGameWindow();
            if (!currentScreenshot) {
                throw new Error('无法获取当前截图');
            }
            const template = await this.loadTemplate(templatePath);
            if (!template) {
                throw new Error(`无法加载模板: ${templatePath}`);
            }
            const currentImage = await Jimp.read(currentScreenshot);
            // 确保尺寸匹配
            if (currentImage.width !== template.width || currentImage.height !== template.height) {
                // 调整模板大小以匹配当前图像
                template.resize({ w: currentImage.width, h: currentImage.height });
            }
            // 计算像素差异
            const diff = new Uint8ClampedArray(currentImage.width * currentImage.height * 4);
            const diffPixels = pixelmatch.default(new Uint8ClampedArray(currentImage.bitmap.data), new Uint8ClampedArray(template.bitmap.data), diff, currentImage.width, currentImage.height, { threshold: threshold * 255 });
            const totalPixels = currentImage.width * currentImage.height;
            const differenceRatio = diffPixels / totalPixels;
            return {
                found: differenceRatio > threshold,
                confidence: differenceRatio,
                text: `差异像素: ${diffPixels}/${totalPixels} (${(differenceRatio * 100).toFixed(2)}%)`
            };
        }
        catch (error) {
            this.logger.error('图像差异检测失败:', error);
            return {
                found: false,
                confidence: 0
            };
        }
    }
    /**
     * 获取图像统计信息
     */
    async getImageStats(region) {
        try {
            let screenshotBuffer;
            if (region) {
                screenshotBuffer = await this.captureRegion(region);
            }
            else {
                screenshotBuffer = await this.captureGameWindow();
            }
            if (!screenshotBuffer) {
                throw new Error('无法获取截图');
            }
            const image = await Jimp.read(screenshotBuffer);
            const width = image.width;
            const height = image.height;
            // 计算平均颜色
            let totalR = 0, totalG = 0, totalB = 0;
            const colorMap = new Map();
            for (let y = 0; y < height; y++) {
                for (let x = 0; x < width; x++) {
                    const colorInt = image.getPixelColor(x, y);
                    const color = intToRGBA(colorInt);
                    totalR += color.r;
                    totalG += color.g;
                    totalB += color.b;
                    // 统计颜色分布（简化为16色）
                    const simplifiedColor = {
                        r: Math.floor(color.r / 16) * 16,
                        g: Math.floor(color.g / 16) * 16,
                        b: Math.floor(color.b / 16) * 16
                    };
                    const colorKey = `${simplifiedColor.r},${simplifiedColor.g},${simplifiedColor.b}`;
                    colorMap.set(colorKey, (colorMap.get(colorKey) || 0) + 1);
                }
            }
            const totalPixels = width * height;
            const averageColor = {
                r: Math.round(totalR / totalPixels),
                g: Math.round(totalG / totalPixels),
                b: Math.round(totalB / totalPixels)
            };
            // 获取主要颜色（前5个）
            const dominantColors = Array.from(colorMap.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([colorKey, count]) => {
                const [r, g, b] = colorKey.split(',').map(Number);
                return {
                    color: { r, g, b },
                    percentage: (count / totalPixels) * 100
                };
            });
            return {
                width,
                height,
                averageColor,
                dominantColors
            };
        }
        catch (error) {
            this.logger.error('获取图像统计信息失败:', error);
            return null;
        }
    }
}
export default ImageRecognition;
