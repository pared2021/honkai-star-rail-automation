import PerformanceDataCollector, { 
  ExecutionMetrics, 
  StrategyExecutionSession, 
  RealTimePerformanceData 
} from './PerformanceDataCollector.js';
import DatabaseService from './DatabaseService.js';
import { Strategy, StrategyStep } from '../types/index.js';

/**
 * 智能评估结果
 */
export interface IntelligentEvaluationResult {
  strategyId: string;
  overallScore: number;
  reliability: number;
  efficiency: number;
  stability: number;
  userFriendliness: number;
  resourceConsumption: number;
  
  // 详细分析
  strengths: string[];
  weaknesses: string[];
  bottlenecks: BottleneckAnalysis[];
  optimizationSuggestions: OptimizationSuggestion[];
  
  // 统计数据
  executionStats: ExecutionStatistics;
  performanceMetrics: PerformanceMetrics;
  
  // 预测数据
  predictedSuccessRate: number;
  estimatedDuration: number;
  riskFactors: RiskFactor[];
  
  evaluatedAt: Date;
  dataQuality: number; // 数据质量评分
}

export interface BottleneckAnalysis {
  stepId: string;
  stepDescription: string;
  issueType: 'performance' | 'reliability' | 'timeout' | 'resource';
  severity: 'low' | 'medium' | 'high' | 'critical';
  frequency: number; // 出现频率
  averageDelay: number; // 平均延迟
  description: string;
  suggestedFix: string;
}

export interface OptimizationSuggestion {
  id: string;
  type: 'step_order' | 'timeout_adjustment' | 'retry_logic' | 'resource_optimization' | 'condition_refinement';
  category: 'performance' | 'reliability' | 'efficiency' | 'timing' | 'accuracy';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  expectedImprovement: string;
  implementationComplexity: 'easy' | 'medium' | 'hard';
  estimatedImpact: number; // 预期改进百分比
  impact: 'low' | 'medium' | 'high';
  steps?: string[];
}

export interface ExecutionStatistics {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageDuration: number;
  medianDuration: number;
  minDuration: number;
  maxDuration: number;
  standardDeviation: number;
  successRateByTimeOfDay: { [hour: string]: number };
  successRateByDayOfWeek: { [day: string]: number };
  commonFailureReasons: { [reason: string]: number };
}

export interface PerformanceMetrics {
  averageCpuUsage: number;
  peakCpuUsage: number;
  averageMemoryUsage: number;
  peakMemoryUsage: number;
  averageFps: number;
  minFps: number;
  networkStability: number;
  systemStability: number;
}

export interface RiskFactor {
  type: 'system' | 'network' | 'game' | 'strategy';
  description: string;
  probability: number; // 0-1
  impact: number; // 0-1
  mitigation: string;
}

/**
 * 智能评估器
 * 基于真实执行数据进行深度分析和评估
 */
class IntelligentEvaluator {
  private dataCollector: PerformanceDataCollector;
  private dbService: DatabaseService;
  private evaluationCache: Map<string, IntelligentEvaluationResult> = new Map();
  private cacheExpiry = 5 * 60 * 1000; // 5分钟缓存

  constructor(dataCollector: PerformanceDataCollector, dbService: DatabaseService) {
    this.dataCollector = dataCollector;
    this.dbService = dbService;
  }

  /**
   * 执行智能评估
   */
  public async evaluateStrategy(strategyId: string): Promise<IntelligentEvaluationResult> {
    // 检查缓存
    const cached = this.evaluationCache.get(strategyId);
    if (cached && Date.now() - cached.evaluatedAt.getTime() < this.cacheExpiry) {
      return cached;
    }

    console.log(`开始智能评估攻略: ${strategyId}`);

    // 收集历史执行数据
    const executionSessions = await this.getExecutionHistory(strategyId);
    const strategies = await this.dbService.getStrategies();
    const strategy = strategies.find(s => s.id === strategyId);
    
    if (!strategy) {
      throw new Error(`未找到攻略: ${strategyId}`);
    }

    // 数据质量检查
    const dataQuality = this.assessDataQuality(executionSessions);
    
    if (dataQuality < 0.3) {
      console.warn(`攻略 ${strategyId} 的数据质量较低: ${dataQuality}`);
    }

    // 执行各项分析
    const executionStats = this.calculateExecutionStatistics(executionSessions);
    const performanceMetrics = this.calculatePerformanceMetrics(executionSessions);
    const bottlenecks = await this.analyzeBottlenecks(strategy, executionSessions);
    const optimizationSuggestions = await this.generateOptimizationSuggestions(strategy, executionStats, bottlenecks);
    const riskFactors = this.assessRiskFactors(executionSessions, performanceMetrics);
    
    // 计算各项评分
    const reliability = this.calculateReliability(executionStats);
    const efficiency = this.calculateEfficiency(executionStats, performanceMetrics);
    const stability = this.calculateStability(executionSessions, performanceMetrics);
    const userFriendliness = this.calculateUserFriendliness(strategy, executionStats);
    const resourceConsumption = this.calculateResourceConsumption(performanceMetrics);
    
    // 计算综合评分
    const overallScore = this.calculateOverallScore({
      reliability,
      efficiency,
      stability,
      userFriendliness,
      resourceConsumption
    });

    // 生成优缺点分析
    const strengths = this.identifyStrengths({
      reliability,
      efficiency,
      stability,
      userFriendliness,
      resourceConsumption
    }, executionStats);
    
    const weaknesses = this.identifyWeaknesses({
      reliability,
      efficiency,
      stability,
      userFriendliness,
      resourceConsumption
    }, bottlenecks);

    // 预测分析
    const predictedSuccessRate = this.predictSuccessRate(executionStats, riskFactors);
    const estimatedDuration = this.estimateDuration(executionStats, performanceMetrics);

    const result: IntelligentEvaluationResult = {
      strategyId,
      overallScore,
      reliability,
      efficiency,
      stability,
      userFriendliness,
      resourceConsumption,
      strengths,
      weaknesses,
      bottlenecks,
      optimizationSuggestions,
      executionStats,
      performanceMetrics,
      predictedSuccessRate,
      estimatedDuration,
      riskFactors,
      evaluatedAt: new Date(),
      dataQuality
    };

    // 缓存结果
    this.evaluationCache.set(strategyId, result);
    
    // 保存评估结果
    await this.saveEvaluationResult(result);

    console.log(`攻略 ${strategyId} 智能评估完成，综合评分: ${overallScore.toFixed(2)}`);
    
    return result;
  }

  /**
   * 评估数据质量
   */
  private assessDataQuality(sessions: StrategyExecutionSession[]): number {
    if (sessions.length === 0) return 0;
    
    let qualityScore = 0;
    let factors = 0;
    
    // 数据量评分
    const dataVolumeScore = Math.min(sessions.length / 10, 1); // 10次执行为满分
    qualityScore += dataVolumeScore * 0.3;
    factors += 0.3;
    
    // 数据完整性评分
    const completeSessionsCount = sessions.filter(s => 
      s.endTime && s.totalDuration && s.metrics.length > 0
    ).length;
    const completenessScore = completeSessionsCount / sessions.length;
    qualityScore += completenessScore * 0.4;
    factors += 0.4;
    
    // 数据新鲜度评分
    const now = Date.now();
    const recentSessions = sessions.filter(s => 
      now - s.startTime.getTime() < 7 * 24 * 60 * 60 * 1000 // 7天内
    ).length;
    const freshnessScore = recentSessions / sessions.length;
    qualityScore += freshnessScore * 0.3;
    factors += 0.3;
    
    return qualityScore / factors;
  }

  /**
   * 计算执行统计数据
   */
  private calculateExecutionStatistics(sessions: StrategyExecutionSession[]): ExecutionStatistics {
    const totalExecutions = sessions.length;
    const successfulExecutions = sessions.filter(s => s.status === 'completed').length;
    const failedExecutions = sessions.filter(s => s.status === 'failed').length;
    
    const durations = sessions
      .filter(s => s.totalDuration)
      .map(s => s.totalDuration!);
    
    const averageDuration = durations.length > 0 ? 
      durations.reduce((sum, d) => sum + d, 0) / durations.length : 0;
    
    const sortedDurations = durations.sort((a, b) => a - b);
    const medianDuration = sortedDurations.length > 0 ? 
      sortedDurations[Math.floor(sortedDurations.length / 2)] : 0;
    
    const minDuration = durations.length > 0 ? Math.min(...durations) : 0;
    const maxDuration = durations.length > 0 ? Math.max(...durations) : 0;
    
    // 计算标准差
    const variance = durations.length > 0 ? 
      durations.reduce((sum, d) => sum + Math.pow(d - averageDuration, 2), 0) / durations.length : 0;
    const standardDeviation = Math.sqrt(variance);
    
    // 按时间段分析成功率
    const successRateByTimeOfDay: { [hour: string]: number } = {};
    const successRateByDayOfWeek: { [day: string]: number } = {};
    
    for (let hour = 0; hour < 24; hour++) {
      const hourSessions = sessions.filter(s => s.startTime.getHours() === hour);
      const hourSuccessful = hourSessions.filter(s => s.status === 'completed').length;
      successRateByTimeOfDay[hour.toString()] = hourSessions.length > 0 ? 
        hourSuccessful / hourSessions.length : 0;
    }
    
    for (let day = 0; day < 7; day++) {
      const daySessions = sessions.filter(s => s.startTime.getDay() === day);
      const daySuccessful = daySessions.filter(s => s.status === 'completed').length;
      successRateByDayOfWeek[day.toString()] = daySessions.length > 0 ? 
        daySuccessful / daySessions.length : 0;
    }
    
    // 统计常见失败原因
    const commonFailureReasons: { [reason: string]: number } = {};
    sessions.forEach(session => {
      session.metrics.forEach(metric => {
        if (!metric.success && metric.errorMessage) {
          commonFailureReasons[metric.errorMessage] = 
            (commonFailureReasons[metric.errorMessage] || 0) + 1;
        }
      });
    });
    
    return {
      totalExecutions,
      successfulExecutions,
      failedExecutions,
      averageDuration,
      medianDuration,
      minDuration,
      maxDuration,
      standardDeviation,
      successRateByTimeOfDay,
      successRateByDayOfWeek,
      commonFailureReasons
    };
  }

  /**
   * 计算性能指标
   */
  private calculatePerformanceMetrics(sessions: StrategyExecutionSession[]): PerformanceMetrics {
    const allMetrics = sessions.flatMap(s => s.metrics);
    
    const cpuUsages = allMetrics.filter(m => m.cpuUsage).map(m => m.cpuUsage!);
    const memoryUsages = allMetrics.filter(m => m.memoryUsage).map(m => m.memoryUsage!);
    
    // 从性能历史数据获取FPS信息
    const performanceHistory = this.dataCollector.getPerformanceHistory(60); // 最近1小时
    const fpsData = performanceHistory.map(p => p.fps);
    
    return {
      averageCpuUsage: cpuUsages.length > 0 ? 
        cpuUsages.reduce((sum, cpu) => sum + cpu, 0) / cpuUsages.length : 0,
      peakCpuUsage: cpuUsages.length > 0 ? Math.max(...cpuUsages) : 0,
      averageMemoryUsage: memoryUsages.length > 0 ? 
        memoryUsages.reduce((sum, mem) => sum + mem, 0) / memoryUsages.length : 0,
      peakMemoryUsage: memoryUsages.length > 0 ? Math.max(...memoryUsages) : 0,
      averageFps: fpsData.length > 0 ? 
        fpsData.reduce((sum, fps) => sum + fps, 0) / fpsData.length : 0,
      minFps: fpsData.length > 0 ? Math.min(...fpsData) : 0,
      networkStability: this.calculateNetworkStability(performanceHistory),
      systemStability: this.calculateSystemStability(performanceHistory)
    };
  }

  /**
   * 分析瓶颈
   */
  private async analyzeBottlenecks(
    strategy: Strategy, 
    sessions: StrategyExecutionSession[]
  ): Promise<BottleneckAnalysis[]> {
    const bottlenecks: BottleneckAnalysis[] = [];
    
    // 分析每个步骤的性能
    for (const step of strategy.steps) {
      const stepMetrics = sessions.flatMap(s => 
        s.metrics.filter(m => m.stepId === step.id)
      );
      
      if (stepMetrics.length === 0) continue;
      
      // 分析超时问题
      const timeouts = stepMetrics.filter(m => 
        m.duration && m.duration > (step.timeout || 30000)
      );
      
      if (timeouts.length > stepMetrics.length * 0.2) { // 超过20%超时
        bottlenecks.push({
          stepId: step.id,
          stepDescription: step.description,
          issueType: 'timeout',
          severity: timeouts.length > stepMetrics.length * 0.5 ? 'critical' : 'high',
          frequency: timeouts.length / stepMetrics.length,
          averageDelay: timeouts.reduce((sum, t) => sum + (t.duration! - (step.timeout || 30000)), 0) / timeouts.length,
          description: `步骤经常超时，${(timeouts.length / stepMetrics.length * 100).toFixed(1)}% 的执行超过预期时间`,
          suggestedFix: `建议增加超时时间到 ${Math.ceil((step.timeout || 30000) * 1.5 / 1000)} 秒，或优化步骤逻辑`
        });
      }
      
      // 分析失败率
      const failures = stepMetrics.filter(m => !m.success);
      if (failures.length > stepMetrics.length * 0.15) { // 超过15%失败
        bottlenecks.push({
          stepId: step.id,
          stepDescription: step.description,
          issueType: 'reliability',
          severity: failures.length > stepMetrics.length * 0.3 ? 'critical' : 'medium',
          frequency: failures.length / stepMetrics.length,
          averageDelay: 0,
          description: `步骤失败率较高，${(failures.length / stepMetrics.length * 100).toFixed(1)}% 的执行失败`,
          suggestedFix: '建议检查步骤条件设置，增加重试次数或改进识别逻辑'
        });
      }
    }
    
    return bottlenecks.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }

  /**
   * 生成优化建议
   */
  private async generateOptimizationSuggestions(
    strategy: Strategy,
    stats: ExecutionStatistics,
    bottlenecks: BottleneckAnalysis[]
  ): Promise<OptimizationSuggestion[]> {
    const suggestions: OptimizationSuggestion[] = [];
    
    // 基于瓶颈生成建议
    bottlenecks.forEach((bottleneck, index) => {
      if (bottleneck.issueType === 'timeout') {
        suggestions.push({
          id: `timeout_${index}_${Date.now()}`,
          type: 'timeout_adjustment',
          category: 'performance',
          priority: bottleneck.severity === 'critical' ? 'high' : 'medium',
          title: '超时设置优化',
          description: `调整步骤 "${bottleneck.stepDescription}" 的超时设置`,
          expectedImprovement: `预计可减少 ${(bottleneck.frequency * 100).toFixed(1)}% 的超时失败`,
          implementationComplexity: 'easy',
          estimatedImpact: bottleneck.frequency * 100,
          impact: bottleneck.frequency > 0.3 ? 'high' : bottleneck.frequency > 0.1 ? 'medium' : 'low',
          steps: [
            '分析当前超时设置',
            '根据历史数据调整超时时间',
            '测试新的超时配置',
            '监控改进效果'
          ]
        });
      }
      
      if (bottleneck.issueType === 'reliability') {
        suggestions.push({
          id: `retry_${index}_${Date.now()}`,
          type: 'retry_logic',
          category: 'reliability',
          priority: 'high',
          title: '重试逻辑优化',
          description: `优化步骤 "${bottleneck.stepDescription}" 的重试逻辑`,
          expectedImprovement: `预计可提高 ${(bottleneck.frequency * 50).toFixed(1)}% 的成功率`,
          implementationComplexity: 'medium',
          estimatedImpact: bottleneck.frequency * 50,
          impact: bottleneck.frequency > 0.3 ? 'high' : bottleneck.frequency > 0.1 ? 'medium' : 'low',
          steps: [
            '分析失败原因',
            '设计智能重试策略',
            '实现指数退避算法',
            '添加失败恢复机制'
          ]
        });
      }
    });
    
    // 基于统计数据生成建议
    if (stats.standardDeviation > stats.averageDuration * 0.3) {
      suggestions.push({
        id: `step_order_${Date.now()}`,
        type: 'step_order',
        category: 'efficiency',
        priority: 'medium',
        title: '步骤顺序优化',
        description: '执行时间波动较大，建议优化步骤顺序和条件判断',
        expectedImprovement: '预计可减少20-30%的执行时间波动',
        implementationComplexity: 'hard',
        estimatedImpact: 25,
        impact: 'medium',
        steps: [
          '分析执行时间波动原因',
          '重新排序关键步骤',
          '优化条件判断逻辑',
          '测试新的执行顺序'
        ]
      });
    }
    
    return suggestions.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  // 评分计算方法
  private calculateReliability(stats: ExecutionStatistics): number {
    if (stats.totalExecutions === 0) return 0;
    return (stats.successfulExecutions / stats.totalExecutions) * 100;
  }

  private calculateEfficiency(stats: ExecutionStatistics, performance: PerformanceMetrics): number {
    // 基于执行时间稳定性和资源使用效率
    const timeStability = stats.averageDuration > 0 ? 
      Math.max(0, 100 - (stats.standardDeviation / stats.averageDuration * 100)) : 0;
    const resourceEfficiency = Math.max(0, 100 - performance.averageCpuUsage - performance.averageMemoryUsage / 10);
    return (timeStability + resourceEfficiency) / 2;
  }

  private calculateStability(sessions: StrategyExecutionSession[], performance: PerformanceMetrics): number {
    // 基于系统稳定性和FPS稳定性
    const systemStability = performance.systemStability * 100;
    const fpsStability = performance.averageFps > 30 ? 
      Math.min(100, (performance.minFps / performance.averageFps) * 100) : 50;
    return (systemStability + fpsStability) / 2;
  }

  private calculateUserFriendliness(strategy: Strategy, stats: ExecutionStatistics): number {
    // 基于步骤复杂度和执行时间
    const complexityScore = Math.max(0, 100 - strategy.steps.length * 2); // 步骤越多越复杂
    const durationScore = stats.averageDuration > 0 ? 
      Math.max(0, 100 - stats.averageDuration / 60000 * 10) : 100; // 时间越长越不友好
    return (complexityScore + durationScore) / 2;
  }

  private calculateResourceConsumption(performance: PerformanceMetrics): number {
    // 资源消耗越低评分越高
    const cpuScore = Math.max(0, 100 - performance.averageCpuUsage * 2);
    const memoryScore = Math.max(0, 100 - performance.averageMemoryUsage / 10);
    return (cpuScore + memoryScore) / 2;
  }

  private calculateOverallScore(scores: {
    reliability: number;
    efficiency: number;
    stability: number;
    userFriendliness: number;
    resourceConsumption: number;
  }): number {
    // 加权平均
    const weights = {
      reliability: 0.3,
      efficiency: 0.25,
      stability: 0.2,
      userFriendliness: 0.15,
      resourceConsumption: 0.1
    };
    
    return Object.entries(scores).reduce((total, [key, score]) => {
      return total + score * weights[key as keyof typeof weights];
    }, 0);
  }

  // 辅助方法
  private calculateNetworkStability(history: RealTimePerformanceData[]): number {
    if (history.length === 0) return 1;
    const latencies = history.map(h => h.networkLatency);
    const avgLatency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length;
    const maxLatency = Math.max(...latencies);
    return Math.max(0, 1 - (maxLatency - avgLatency) / avgLatency);
  }

  private calculateSystemStability(history: RealTimePerformanceData[]): number {
    if (history.length === 0) return 1;
    // 基于FPS和CPU使用率的稳定性
    const fpsVariance = this.calculateVariance(history.map(h => h.fps));
    const cpuVariance = this.calculateVariance(history.map(h => h.cpuUsage));
    return Math.max(0, 1 - (fpsVariance + cpuVariance) / 2000);
  }

  private calculateVariance(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    return values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  }

  private identifyStrengths(scores: any, stats: ExecutionStatistics): string[] {
    const strengths: string[] = [];
    
    if (scores.reliability > 85) {
      strengths.push(`可靠性优秀，成功率达到 ${scores.reliability.toFixed(1)}%`);
    }
    
    if (scores.efficiency > 80) {
      strengths.push('执行效率高，时间稳定性好');
    }
    
    if (scores.stability > 80) {
      strengths.push('系统稳定性好，运行流畅');
    }
    
    if (stats.standardDeviation < stats.averageDuration * 0.1) {
      strengths.push('执行时间非常稳定');
    }
    
    return strengths;
  }

  private identifyWeaknesses(scores: any, bottlenecks: BottleneckAnalysis[]): string[] {
    const weaknesses: string[] = [];
    
    if (scores.reliability < 70) {
      weaknesses.push(`可靠性需要改进，成功率仅为 ${scores.reliability.toFixed(1)}%`);
    }
    
    if (scores.efficiency < 60) {
      weaknesses.push('执行效率偏低，存在性能瓶颈');
    }
    
    if (bottlenecks.filter(b => b.severity === 'critical').length > 0) {
      weaknesses.push('存在严重的性能瓶颈需要立即解决');
    }
    
    if (scores.resourceConsumption < 50) {
      weaknesses.push('资源消耗较高，需要优化');
    }
    
    return weaknesses;
  }

  private predictSuccessRate(stats: ExecutionStatistics, risks: RiskFactor[]): number {
    let baseSuccessRate = stats.totalExecutions > 0 ? 
      stats.successfulExecutions / stats.totalExecutions : 0.5;
    
    // 根据风险因子调整预测
    const riskImpact = risks.reduce((total, risk) => 
      total + risk.probability * risk.impact, 0
    );
    
    return Math.max(0, Math.min(1, baseSuccessRate - riskImpact)) * 100;
  }

  private estimateDuration(stats: ExecutionStatistics, performance: PerformanceMetrics): number {
    if (stats.totalExecutions === 0) return 0;
    
    // 基于历史数据和当前系统性能调整
    let baseDuration = stats.averageDuration;
    
    // 如果系统性能较差，增加预估时间
    if (performance.averageCpuUsage > 80) {
      baseDuration *= 1.2;
    }
    
    if (performance.averageFps < 30) {
      baseDuration *= 1.1;
    }
    
    return baseDuration;
  }

  private assessRiskFactors(
    sessions: StrategyExecutionSession[], 
    performance: PerformanceMetrics
  ): RiskFactor[] {
    const risks: RiskFactor[] = [];
    
    // 系统性能风险
    if (performance.averageCpuUsage > 80) {
      risks.push({
        type: 'system',
        description: 'CPU使用率过高可能影响执行稳定性',
        probability: 0.7,
        impact: 0.3,
        mitigation: '关闭不必要的后台程序，降低系统负载'
      });
    }
    
    // 网络稳定性风险
    if (performance.networkStability < 0.8) {
      risks.push({
        type: 'network',
        description: '网络不稳定可能导致连接超时',
        probability: 0.5,
        impact: 0.4,
        mitigation: '检查网络连接，考虑使用有线网络'
      });
    }
    
    // 游戏版本风险
    const recentFailures = sessions.filter(s => 
      s.status === 'failed' && 
      Date.now() - s.startTime.getTime() < 24 * 60 * 60 * 1000
    ).length;
    
    if (recentFailures > sessions.length * 0.3) {
      risks.push({
        type: 'game',
        description: '最近失败率较高，可能游戏版本更新导致',
        probability: 0.6,
        impact: 0.5,
        mitigation: '检查游戏版本，更新攻略适配'
      });
    }
    
    return risks;
  }

  // 数据库操作
  private async getExecutionHistory(strategyId: string): Promise<StrategyExecutionSession[]> {
    // TODO: 从数据库获取执行历史
    return [];
  }

  private async saveEvaluationResult(result: IntelligentEvaluationResult): Promise<void> {
    // TODO: 保存评估结果到数据库
    console.log('保存智能评估结果:', result.strategyId);
  }

  /**
   * 清除缓存
   */
  public clearCache(): void {
    this.evaluationCache.clear();
  }

  /**
   * 获取评估历史
   */
  public async getEvaluationHistory(strategyId: string): Promise<IntelligentEvaluationResult[]> {
    // TODO: 从数据库获取评估历史
    return [];
  }
}

export default IntelligentEvaluator;