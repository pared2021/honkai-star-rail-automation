// TaskInfoCollector 模块测试
import { TaskInfoCollector } from './TaskInfoCollector.js';
import { TaskType } from '../types';
// Mock dependencies
jest.mock('./ImageRecognition');
jest.mock('../services/DatabaseService');
describe('TaskInfoCollector', () => {
    let taskInfoCollector;
    let mockImageRecognition;
    let mockDatabaseService;
    let mockConfig;
    beforeEach(() => {
        // 创建mock对象
        mockImageRecognition = {
            findImage: jest.fn(),
            recognizeText: jest.fn(),
            updateConfig: jest.fn(),
            getConfig: jest.fn()
        };
        mockDatabaseService = {
            addTaskInfo: jest.fn(),
            getTaskInfos: jest.fn(),
            getTaskInfoById: jest.fn(),
            updateTaskInfo: jest.fn(),
            deleteTaskInfo: jest.fn(),
            searchTaskInfos: jest.fn()
        };
        mockConfig = {
            id: 'test-config',
            name: 'Test Configuration',
            description: 'Test configuration for TaskInfoCollector',
            isEnabled: true,
            scope: {
                taskTypes: [TaskType.MAIN, TaskType.SIDE, TaskType.DAILY],
                categories: ['combat', 'exploration', 'social'],
                difficulty: ['easy', 'medium', 'hard'],
                includeRepeatable: true,
                includeTimeLimited: true,
                includeDeprecated: false
            },
            strategy: {
                method: 'automatic',
                sources: ['game_data', 'community'],
                priority: 'accuracy',
                updateFrequency: 'daily',
                batchSize: 10,
                concurrency: 3
            },
            quality: {
                enableValidation: true,
                minReliability: 0.7,
                minConfidence: 0.7,
                requireVerification: false,
                autoCorrection: true,
                duplicateHandling: 'merge',
                conflictResolution: 'auto'
            },
            storage: {
                enableCaching: true,
                cacheExpiry: 24,
                enableBackup: true,
                backupFrequency: 'daily',
                compressionEnabled: false,
                encryptionEnabled: false
            },
            monitoring: {
                enableMetrics: true,
                enableAlerts: true,
                alertThresholds: {
                    errorRate: 0.1,
                    collectionDelay: 5,
                    dataQualityScore: 0.8
                },
                reportingFrequency: 'daily',
                includePerformanceMetrics: true
            },
            processing: {
                enableFiltering: true,
                filters: [],
                enableTransformation: false,
                transformations: []
            },
            integration: {
                enableApiExport: false,
                apiEndpoints: [],
                enableWebhooks: false,
                webhookUrls: [],
                enableThirdPartySync: false,
                syncTargets: []
            },
            metadata: {
                createdBy: 'test',
                createdAt: new Date(),
                lastModifiedBy: 'test',
                lastModifiedAt: new Date(),
                version: '1.0.0',
                tags: ['test'],
                notes: 'Test configuration'
            }
        };
        taskInfoCollector = new TaskInfoCollector(mockImageRecognition, mockDatabaseService, mockConfig);
    });
    afterEach(() => {
        jest.clearAllMocks();
    });
    describe('collectTaskInfo', () => {
        it('应该成功收集主线任务信息', async () => {
            // 模拟检测到主线任务UI元素
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            // 模拟OCR识别结果
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '击败魔王', confidence: 0.9 })
                .mockResolvedValueOnce({ found: true, text: '前往魔王城堡，击败最终BOSS', confidence: 0.85 })
                .mockResolvedValueOnce({ found: true, text: '经验值+1000\n金币+500', confidence: 0.8 })
                .mockResolvedValueOnce({ found: true, text: '等级达到50级\n完成前置任务', confidence: 0.75 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo).toBeDefined();
            expect(result.taskInfo?.name).toBe('击败魔王');
            expect(result.taskInfo?.type).toBe(TaskType.MAIN);
            expect(result.taskInfo?.description).toBe('前往魔王城堡，击败最终BOSS');
            expect(result.taskInfo?.rewards).toEqual(['经验值+1000', '金币+500']);
            expect(result.taskInfo?.requirements).toEqual(['等级达到50级', '完成前置任务']);
            expect(result.confidence).toBeGreaterThan(0);
            expect(mockDatabaseService.addTaskInfo).toHaveBeenCalledWith(result.taskInfo);
        });
        it('应该成功收集支线任务信息', async () => {
            // 模拟检测到支线任务UI元素
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: false, confidence: 0.3, position: { x: 0, y: 0 }, matchRegion: { x: 0, y: 0, width: 0, height: 0 } }) // 主线任务模板不匹配
                .mockResolvedValueOnce({ found: false, confidence: 0.2, position: { x: 0, y: 0 }, matchRegion: { x: 0, y: 0, width: 0, height: 0 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.88, position: { x: 120, y: 80 }, matchRegion: { x: 120, y: 80, width: 350, height: 50 } }) // 支线任务标题匹配
                .mockResolvedValueOnce({ found: true, confidence: 0.82, position: { x: 120, y: 140 }, matchRegion: { x: 120, y: 140, width: 450, height: 120 } }); // 支线任务描述匹配
            // 模拟OCR识别结果
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '收集草药', confidence: 0.88 })
                .mockResolvedValueOnce({ found: true, text: '在森林中收集10个治疗草药', confidence: 0.82 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo?.name).toBe('收集草药');
            expect(result.taskInfo?.type).toBe(TaskType.SIDE);
            expect(result.taskInfo?.description).toBe('在森林中收集10个治疗草药');
        });
        it('应该成功收集每日任务信息', async () => {
            // 模拟检测到每日任务UI元素
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: false, confidence: 0.3 }) // 主线任务不匹配
                .mockResolvedValueOnce({ found: false, confidence: 0.2 })
                .mockResolvedValueOnce({ found: false, confidence: 0.4 }) // 支线任务不匹配
                .mockResolvedValueOnce({ found: false, confidence: 0.3 })
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 150, y: 100 }, matchRegion: { x: 150, y: 100, width: 300, height: 40 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 150, y: 100 }, matchRegion: { x: 150, y: 100, width: 300, height: 40 } }); // 每日任务名称匹配
            // 模拟OCR识别结果
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '每日签到', confidence: 0.9 })
                .mockResolvedValueOnce({ found: true, text: '完成每日签到获得奖励', confidence: 0.85 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo?.name).toBe('每日签到');
            expect(result.taskInfo?.type).toBe(TaskType.DAILY);
            expect(result.taskInfo?.difficulty).toBe('easy'); // 每日任务难度应该是1
            expect(result.taskInfo?.estimatedTime).toBe(5); // 每日任务基础时间5分钟
        });
        it('当无法检测到任务类型时应该返回失败', async () => {
            // 模拟所有UI元素都不匹配
            mockImageRecognition.findImage.mockResolvedValue({
                found: false,
                confidence: 0.3
            });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(false);
            expect(result.error).toBe('无法检测到任务类型');
            expect(result.confidence).toBe(0);
            expect(mockDatabaseService.addTaskInfo).not.toHaveBeenCalled();
        });
        it('当OCR识别失败时应该使用默认值', async () => {
            // 模拟检测到主线任务UI元素
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            // 模拟OCR识别失败
            mockImageRecognition.recognizeText.mockResolvedValue({
                found: false,
                text: '',
                confidence: 0.2
            });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo?.name).toBe('未知任务');
            expect(result.taskInfo?.description).toBe('');
            expect(result.taskInfo?.rewards).toEqual([]);
            expect(result.taskInfo?.requirements).toEqual([]);
        });
        it('should not save to database when autoSave is false', async () => {
            taskInfoCollector.updateConfig({
                storage: {
                    enableCaching: false,
                    cacheExpiry: 24,
                    enableBackup: false,
                    backupFrequency: 'daily',
                    compressionEnabled: false,
                    encryptionEnabled: false
                }
            });
            // 模拟检测到任务
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '测试任务', confidence: 0.9 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(mockDatabaseService.addTaskInfo).not.toHaveBeenCalled();
        });
        it('当发生异常时应该返回错误信息', async () => {
            // 模拟图像识别抛出异常
            mockImageRecognition.findImage.mockRejectedValue(new Error('图像识别失败'));
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(false);
            expect(result.error).toBe('图像识别失败');
            expect(result.confidence).toBe(0);
        });
    });
    describe('配置管理', () => {
        it('应该能够更新配置', () => {
            const newConfig = {
                quality: {
                    enableValidation: true,
                    minReliability: 0.7,
                    minConfidence: 0.8,
                    requireVerification: false,
                    autoCorrection: true,
                    duplicateHandling: 'merge',
                    conflictResolution: 'auto'
                }
            };
            taskInfoCollector.updateConfig(newConfig);
            const currentConfig = taskInfoCollector.getConfig();
            expect(currentConfig.quality.minConfidence).toBe(0.8);
            expect(currentConfig.storage?.enableCaching).toBe(true);
        });
        it('应该能够获取当前配置', () => {
            const config = taskInfoCollector.getConfig();
            expect(config).toEqual(mockConfig);
            expect(config).not.toBe(mockConfig); // 应该返回副本，不是原对象
        });
    });
    describe('任务难度和时间估算', () => {
        it('应该正确估算主线任务的难度和时间', async () => {
            // 模拟检测到主线任务
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '复杂的主线任务', confidence: 0.9 })
                .mockResolvedValueOnce({ found: true, text: '这是一个非常复杂的主线任务，需要完成多个步骤，包括战斗、解谜和收集等多种玩法元素，预计需要较长时间完成', confidence: 0.85 })
                .mockResolvedValueOnce({ found: true, text: '经验值+5000', confidence: 0.8 })
                .mockResolvedValueOnce({ found: true, text: '要求1\n要求2\n要求3\n要求4', confidence: 0.75 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo?.difficulty).toBe('extreme'); // 主线任务基础难度3 + 要求多1 + 描述长1 = 5
            expect(result.taskInfo?.estimatedTime).toBe(150); // 主线任务基础30分钟 * 难度5 = 150分钟
        });
        it('应该正确估算每日任务的难度和时间', async () => {
            // 模拟检测到每日任务
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: false, confidence: 0.3 })
                .mockResolvedValueOnce({ found: false, confidence: 0.2 })
                .mockResolvedValueOnce({ found: false, confidence: 0.4 })
                .mockResolvedValueOnce({ found: false, confidence: 0.3 })
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 150, y: 100 }, matchRegion: { x: 150, y: 100, width: 300, height: 40 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 150, y: 100 }, matchRegion: { x: 150, y: 100, width: 300, height: 40 } });
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '简单签到', confidence: 0.9 })
                .mockResolvedValueOnce({ found: true, text: '点击签到', confidence: 0.85 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            expect(result.taskInfo?.difficulty).toBe('easy'); // 每日任务难度基础1
            expect(result.taskInfo?.estimatedTime).toBe(5); // 每日任务基础5分钟 * 难度1 = 5分钟
        });
    });
    describe('置信度计算', () => {
        it('应该根据收集到的信息计算正确的置信度', async () => {
            // 模拟收集到完整信息的任务
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: true, text: '完整任务', confidence: 0.9 })
                .mockResolvedValueOnce({ found: true, text: '这是一个有完整描述的任务', confidence: 0.85 })
                .mockResolvedValueOnce({ found: true, text: '奖励信息', confidence: 0.8 });
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            // 基础0.5 + 有名称0.2 + 有描述0.2 + 有奖励0.1 = 1.0
            expect(result.taskInfo?.confidence).toBe(1.0);
        });
        it('应该为信息不完整的任务计算较低的置信度', async () => {
            // 模拟只收集到部分信息的任务
            mockImageRecognition.findImage
                .mockResolvedValueOnce({ found: true, confidence: 0.9, position: { x: 100, y: 50 }, matchRegion: { x: 100, y: 50, width: 400, height: 60 } })
                .mockResolvedValueOnce({ found: true, confidence: 0.85, position: { x: 100, y: 120 }, matchRegion: { x: 100, y: 120, width: 500, height: 150 } });
            mockImageRecognition.recognizeText
                .mockResolvedValueOnce({ found: false, text: '', confidence: 0.3 }) // 名称识别失败
                .mockResolvedValueOnce({ found: true, text: '有描述', confidence: 0.85 })
                .mockResolvedValueOnce({ found: false, text: '', confidence: 0.2 }); // 奖励识别失败
            const result = await taskInfoCollector.collectTaskInfo();
            expect(result.success).toBe(true);
            // 基础0.5 + 有描述0.2 = 0.7
            expect(result.taskInfo?.confidence).toBe(0.7);
        });
    });
});
