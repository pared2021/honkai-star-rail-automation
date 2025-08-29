// API类型定义
import { Request } from 'express';
import { DatabaseService } from '../../src/services/DatabaseService.js';

// 扩展的Request接口
export interface ExtendedRequest extends Request {
  dbService: DatabaseService;
  user?: {
    id: string;
    username: string;
    email: string;
  };
  automationManager?: any;
  strategyAnalyzer?: any;
}

// 自动启动设置接口
export interface AutoLaunchSettings {
  enabled: boolean;
  gamePath: string;
  autoLaunch: boolean;
  launchDelay: number;
  enableMonitoring: boolean;
  startMonitoring: boolean;
  monitoringInterval: number;
  monitoringDelay: number;
  enableFilterDetection: boolean;
  filterDetectionInterval: number;
  detectInjection: boolean;
  detectDriverFilters: boolean;
  terminateOnExit: boolean;
  retryAttempts: number;
  retryDelay: number;
}

// 任务相关类型
export enum TaskType {
  DAILY = 'daily',
  MAIN = 'main',
  SIDE = 'side',
  CUSTOM = 'custom',
  EVENT = 'event',
  WEEKLY = 'weekly'
}

// 任务奖励类型
export interface TaskReward {
  type: 'exp' | 'credits' | 'materials' | 'items' | 'stellar_jade';
  name: string;
  amount: number;
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
}

// 攻略步骤类型
export interface StrategyStep {
  id: string;
  strategyId: string;
  stepOrder: number;
  stepType: 'navigation' | 'interaction' | 'battle' | 'dialog' | 'wait' | 'custom';
  description: string;
  action: StrategyAction;
  expectedResult?: string;
  timeout: number;
  retryCount: number;
  isOptional: boolean;
  conditions?: StrategyCondition[];
}

// 攻略动作类型
export interface StrategyAction {
  type: 'click' | 'key_press' | 'move' | 'wait' | 'image_recognition' | 'text_recognition';
  target?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    imagePath?: string;
    text?: string;
    key?: string;
  };
  parameters?: Record<string, any>;
}

// 攻略条件类型
export interface StrategyCondition {
  type: 'image_exists' | 'text_exists' | 'window_title' | 'time_range' | 'custom';
  value: string;
  operator: 'equals' | 'contains' | 'not_equals' | 'greater_than' | 'less_than';
}

export interface Task {
  id: string;
  name: string;
  description: string;
  type: TaskType;
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: number;
  rewards: TaskReward[];
  requirements: string[];
  location?: string;
  isAvailable: boolean;
  isCompleted: boolean;
  completionCount: number;
  lastCompletedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
  steps?: StrategyStep[]; // 任务步骤
}

export interface StartTaskRequest {
  accountId: string;
  taskType: string;
  config?: any;
}

export interface TaskControlRequest {
  taskId: string;
  action: 'pause' | 'resume' | 'stop';
}

export interface TaskInfo {
  taskId: string;
  status: string;
  progress: number;
  timestamp: string;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  steps: any[];
  config: any;
}

export interface AutomationConfig {
  id: number;
  accountId: string;
  level: 'low' | 'medium' | 'high';
  taskType: TaskType | 'all' | 'event';
  autoCollectInfo: boolean;
  autoAnalyzeStrategy: boolean;
  autoSelectBestStrategy: boolean;
  autoExecuteTasks: boolean;
  minSuccessRate: number;
  maxRetryCount: number;
  intervalMinutes: number;
  enableSmartScheduling: boolean;
  prioritySettings: {
    main: number;
    side: number;
    daily: number;
    event: number;
  };
  resourceManagement: {
    maxConcurrentTasks: number;
    energyThreshold: number;
    autoRestoreEnergy: boolean;
  };
  taskPriority: {
    daily: 'low' | 'medium' | 'high';
    main: 'low' | 'medium' | 'high';
    side: 'low' | 'medium' | 'high';
    event: 'low' | 'medium' | 'high';
  };
  enableErrorRecovery: boolean;
  pauseOnError: boolean;
  notificationSettings: {
    onTaskComplete: boolean;
    onError: boolean;
    onOptimalStrategyFound: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
}

// 评估系统相关类型
export interface ExecutionData {
  id: string;
  strategyId: string;
  accountId: string;
  startTime: Date;
  endTime?: Date;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  totalSteps: number;
  completedSteps: number;
  currentStep?: number;
  stepData: ExecutionStepData[];
  performanceMetrics: PerformanceMetrics;
  errors: ExecutionError[];
  result?: {
    success: boolean;
    rewards?: any[];
    finalState?: any;
  };
  createdAt: Date;
  updatedAt: Date;
}

export interface ExecutionStepData {
  stepId: string;
  stepOrder: number;
  stepType: string;
  description: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  performanceData: StepPerformanceData;
  errors: ExecutionError[];
  retryCount: number;
  screenshots?: string[];
  logs: string[];
}

export interface StepPerformanceData {
  executionTime: number;
  memoryUsage: number;
  cpuUsage: number;
  accuracy: number;
  confidence: number;
  responseTime: number;
  resourceConsumption: {
    energy?: number;
    credits?: number;
    materials?: any[];
  };
}

export interface ExecutionError {
  id: string;
  type: 'timeout' | 'recognition_failed' | 'action_failed' | 'unexpected_state' | 'system_error';
  message: string;
  stepId?: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: any;
  stackTrace?: string;
  screenshot?: string;
}

export interface PerformanceMetrics {
  totalExecutionTime: number;
  averageStepTime: number;
  successRate: number;
  errorRate: number;
  retryRate: number;
  resourceEfficiency: number;
  memoryPeakUsage: number;
  cpuAverageUsage: number;
  throughput: number;
  reliability: number;
}

export interface IntelligentEvaluation {
  id: string;
  strategyId: string;
  evaluationTime: Date;
  overallScore: number;
  dimensionScores: {
    efficiency: number;
    reliability: number;
    resourceUsage: number;
    userExperience: number;
    adaptability: number;
  };
  strengths: string[];
  weaknesses: string[];
  recommendations: OptimizationRecommendation[];
  confidenceLevel: number;
  dataQuality: number;
  sampleSize: number;
  lastUpdated: Date;
}

export interface OptimizationRecommendation {
  id: string;
  type: 'performance' | 'reliability' | 'resource' | 'user_experience';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  expectedImprovement: {
    metric: string;
    currentValue: number;
    expectedValue: number;
    improvementPercentage: number;
  };
  implementationComplexity: 'easy' | 'medium' | 'hard';
  estimatedEffort: string;
  prerequisites: string[];
  risks: string[];
  createdAt: Date;
}

export interface UserFeedback {
  id: string;
  strategyId: string;
  executionId?: string;
  userId: string;
  rating: number; // 1-5
  feedbackType: 'execution_result' | 'strategy_quality' | 'performance' | 'bug_report' | 'suggestion';
  title: string;
  description: string;
  tags: string[];
  isVerified: boolean;
  helpfulCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PerformanceAnalysis {
  strategyId: string;
  timeRange: {
    start: Date;
    end: Date;
  };
  executionCount: number;
  averageMetrics: PerformanceMetrics;
  trends: {
    metric: string;
    direction: 'improving' | 'declining' | 'stable';
    changePercentage: number;
    significance: number;
  }[];
  bottlenecks: BottleneckAnalysis[];
  improvements: ImprovementSuggestion[];
  generatedAt: Date;
}

export interface BottleneckAnalysis {
  stepId: string;
  stepDescription: string;
  bottleneckType: 'time' | 'resource' | 'accuracy' | 'reliability';
  impact: number; // 0-1
  frequency: number; // 0-1
  severity: 'low' | 'medium' | 'high' | 'critical';
  rootCause: string;
  suggestedFixes: string[];
}

export interface ImprovementSuggestion {
  id: string;
  category: 'optimization' | 'bug_fix' | 'enhancement' | 'refactor';
  priority: number; // 1-10
  title: string;
  description: string;
  expectedBenefit: string;
  implementationSteps: string[];
  estimatedTime: string;
  riskLevel: 'low' | 'medium' | 'high';
}

// 账户类型
export interface Account {
  id: string;
  username: string;
  email?: string;
  nickname?: string;
  serverRegion?: string;
  gameVersion?: string;
  deviceInfo?: any;
  isActive: boolean;
  lastLoginAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

// 账户相关请求类型
export interface CreateAccountRequest {
  name: string;
  username: string;
  password: string;
  email?: string;
  nickname?: string;
  gameAccount: string;
  serverRegion?: string;
  gameVersion?: string;
  deviceInfo?: any;
  isActive?: boolean;
}

export interface UpdateAccountRequest {
  username?: string;
  password?: string;
  email?: string;
  nickname?: string;
  serverRegion?: string;
  gameVersion?: string;
  deviceInfo?: any;
  isActive?: boolean;
}

// 统计相关类型
export interface TaskStats {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  successRate: number;
  averageExecutionTime: number;
  totalRewards: any[];
  dailyStats: {
    date: string;
    completed: number;
    failed: number;
    rewards: any[];
  }[];
  weeklyStats: {
    week: string;
    completed: number;
    failed: number;
    rewards: any[];
  }[];
  monthlyStats: {
    month: string;
    completed: number;
    failed: number;
    rewards: any[];
  }[];
}

// API请求和响应类型
export interface StartExecutionRequest {
  strategyId: string;
  accountId: string;
  config?: any;
  executionConfig?: {
    skipValidation?: boolean;
    dryRun?: boolean;
    maxRetries?: number;
  };
  options?: {
    skipValidation?: boolean;
    dryRun?: boolean;
    maxRetries?: number;
  };
}

export interface StartExecutionResponse {
  executionId: string;
  status: string;
  message: string;
}

export interface UpdateExecutionStepRequest {
  stepIndex: number;
  stepId: string;
  status: 'running' | 'completed' | 'failed';
  progress?: number;
  error?: string;
  success: boolean;
}

export interface GetPerformanceAnalysisRequest {
  strategyId: string;
  timeRange?: {
    start: string;
    end: string;
  };
  includeBottlenecks?: boolean;
  includeTrends?: boolean;
}

export interface OptimizeStrategyRequest {
  strategyId: string;
  optimizationType: 'performance' | 'reliability' | 'resource' | 'all';
  analysisType?: 'quick' | 'detailed' | 'comprehensive';
  options?: {
    includeHistoricalData?: boolean;
    maxExecutionTime?: number;
    maxResourceUsage?: number;
    minSuccessRate?: number;
  };
  constraints?: {
    maxExecutionTime?: number;
    maxResourceUsage?: number;
    minSuccessRate?: number;
  };
}

export interface SubmitFeedbackRequest {
  strategyId: string;
  executionId?: string;
  rating: number;
  feedbackType: string;
  title: string;
  description: string;
  tags?: string[];
}

export interface TriggerAnalysisRequest {
  strategyIds: string[];
  analysisType: 'performance' | 'optimization' | 'full';
  priority?: 'low' | 'medium' | 'high';
}

export interface GetDashboardDataRequest {
  strategyId: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
}