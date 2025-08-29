// 核心类型定义

// 游戏状态相关类型
export interface GameStatus {
  isRunning: boolean;
  isActive: boolean;
  windowInfo?: {
    title: string;
    width: number;
    height: number;
    x: number;
    y: number;
  };
  currentScene?: string;
}

// 账号相关类型
export interface Account {
  id: string;
  name: string;
  gameAccount: string;
  isActive: boolean;
  createdAt: Date;
  lastLoginAt?: Date;
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
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';

// 扩展的任务配置接口
export interface ExtendedTaskConfig {
  steps?: Array<{
    name: string;
    type?: string;
    duration?: number;
  }>;
  expectedRewards?: TaskReward[];
  expectedExperience?: number;
  customData?: Record<string, unknown>;
}

// 任务配置类型联合
export type TaskConfigData = DailyTaskConfig | MainTaskConfig | ExtendedTaskConfig | Record<string, unknown>;

// 任务结果类型
export interface TaskResult {
  success: boolean;
  rewards?: TaskReward[];
  experience?: number;
  completionTime?: number;
  errors?: string[];
  data?: {
    steps?: string[];
    duration?: number;
    rewards?: TaskReward[];
    experience?: number;
    customData?: Record<string, unknown>;
    eventRewards?: TaskReward[];
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface Task {
  id: string;
  accountId: string;
  taskType: TaskType;
  status: TaskStatus;
  config: TaskConfigData;
  startTime?: Date;
  endTime?: Date;
  result?: TaskResult;
  createdAt: Date;
  
  // 新增字段：任务信息收集相关
  taskInfo?: {
    taskInfoId?: string; // 关联的TaskInfo ID
    collectionStatus: 'not_collected' | 'collecting' | 'collected' | 'outdated';
    lastInfoUpdate?: Date;
    infoReliability?: number; // 0-1，信息可靠性
    infoSource?: 'game_data' | 'community' | 'official_guide' | 'user_generated';
  };
  
  // 新增字段：攻略相关
  strategy?: {
    strategyId?: string; // 使用的攻略ID
    strategyVersion?: string; // 攻略版本
    selectionMethod: 'manual' | 'auto_recommended' | 'ai_optimized';
    customizations?: {
      modifiedSteps: string[]; // 修改的步骤ID
      addedSteps: StrategyStep[]; // 添加的步骤
      removedSteps: string[]; // 移除的步骤ID
    };
    performance?: {
      expectedTime: number; // 预期执行时间
      actualTime?: number; // 实际执行时间
      successProbability: number; // 成功概率
      efficiency: number; // 效率评分
    };
  };
  
  // 新增字段：执行监控
  monitoring?: {
    enableRealTimeTracking: boolean;
    trackingInterval: number; // 秒
    performanceMetrics: {
      cpuUsage: number[];
      memoryUsage: number[];
      networkLatency: number[];
      timestamps: Date[];
    };
    alerts: {
      id: string;
      type: 'performance' | 'error' | 'timeout' | 'resource';
      message: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      timestamp: Date;
      resolved: boolean;
    }[];
  };
  
  // 新增字段：智能调度相关
  scheduling?: {
    priority: number; // 1-10，优先级
    scheduledStartTime?: Date;
    estimatedDuration: number; // 分钟
    resourceRequirements: {
      cpu: 'low' | 'medium' | 'high';
      memory: 'low' | 'medium' | 'high';
      network: 'none' | 'low' | 'medium' | 'high';
    };
    dependencies: {
      taskId: string;
      dependencyType: 'prerequisite' | 'resource_conflict' | 'sequence';
    }[];
    constraints: {
      timeWindow?: {
        start: Date;
        end: Date;
      };
      resourceLimits?: {
        maxConcurrentTasks: number;
        maxResourceUsage: number;
      };
    };
  };
  
  // 新增字段：学习和优化
  learning?: {
    enableLearning: boolean;
    learningData: {
      executionPatterns: {
        pattern: string;
        frequency: number;
        successRate: number;
      }[];
      errorPatterns: {
        error: string;
        frequency: number;
        context: string;
      }[];
      optimizationSuggestions: {
        type: 'time' | 'resource' | 'reliability' | 'strategy';
        suggestion: string;
        impact: number; // 0-1，预期影响
        confidence: number; // 0-1，置信度
      }[];
    };
    adaptiveSettings: {
      autoAdjustTimeout: boolean;
      autoSelectStrategy: boolean;
      autoOptimizeSchedule: boolean;
    };
  };
}

// 任务配置类型
export interface TaskConfig {
  id: string;
  taskType: TaskType;
  configName: string;
  configData: TaskConfigData;
  isDefault: boolean;
  createdAt: Date;
}

// 日常任务配置
export interface DailyTaskConfig {
  enableStamina: boolean;
  enableCommission: boolean;
  staminaTarget: number;
  autoCollectRewards: boolean;
  steps?: Array<{
    name: string;
    type?: string;
    duration?: number;
  }>;
  expectedRewards?: TaskReward[];
  expectedExperience?: number;
  customData?: Record<string, unknown>;
}

// 主线任务配置
export interface MainTaskConfig {
  autoDialog: boolean;
  autoBattle: boolean;
  skipCutscene: boolean;
  battleStrategy: string;
  steps?: Array<{
    name: string;
    type?: string;
    duration?: number;
  }>;
  expectedRewards?: TaskReward[];
  expectedExperience?: number;
  customData?: Record<string, unknown>;
}

// 任务日志类型
export type LogLevel = 'info' | 'warn' | 'warning' | 'error' | 'debug';

// 日志元数据类型
export interface LogMetadata {
  stepId?: string;
  actionType?: string;
  duration?: number;
  errorCode?: string;
  [key: string]: unknown;
}

export interface TaskLog {
  id: string;
  taskId: string;
  level: LogLevel;
  message: string;
  timestamp: Date;
  metadata?: LogMetadata;
}

// 统计数据类型
export interface AccountStats {
  id: string;
  accountId: string;
  date: string; // YYYY-MM-DD 格式
  loginCount: number;
  totalPlayTime: number; // 分钟
  tasksCompleted: number;
  tasksFailed: number;
  totalRuntime: number;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

// 日常统计数据类型
export interface DailyStats {
  id: string;
  accountId: string;
  date: string; // YYYY-MM-DD 格式
  loginCount: number;
  totalPlayTime: number; // 分钟
  tasksCompleted: number;
  tasksFailed: number;
  totalRuntime: number;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

// 游戏状态类型
export interface GameStatus {
  isRunning: boolean;
  isActive: boolean;
  windowInfo?: {
    title: string;
    width: number;
    height: number;
    x: number;
    y: number;
  };
  currentScene?: string;
}

// API响应类型
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 任务启动请求类型
export interface StartTaskRequest {
  taskType: TaskType;
  accountId?: string;
  config: TaskConfigData;
}

// 任务控制请求类型
export interface TaskControlRequest {
  taskId: string;
  action: 'pause' | 'resume' | 'stop';
}

// 任务分类和子分类类型
export type TaskCategory = 'story' | 'exploration' | 'combat' | 'collection' | 'social' | 'system';
export type TaskSubCategory = 
  | 'main_story' | 'side_story' | 'character_story'
  | 'world_exploration' | 'treasure_hunt' | 'puzzle'
  | 'boss_fight' | 'elite_enemy' | 'mob_clearing'
  | 'material_gathering' | 'item_collection' | 'achievement'
  | 'npc_interaction' | 'team_activity' | 'guild_mission'
  | 'daily_login' | 'weekly_reset' | 'event_participation';

// 任务依赖关系类型
export interface TaskDependency {
  taskId: string;
  dependencyType: 'prerequisite' | 'parallel' | 'sequence' | 'optional';
  description: string;
}

// 任务完成条件类型
export interface TaskCompletionCondition {
  type: 'kill_enemy' | 'collect_item' | 'reach_location' | 'interact_npc' | 'complete_dialogue' | 'custom';
  target: string;
  currentProgress: number;
  requiredProgress: number;
  isCompleted: boolean;
}

// 任务资源需求类型
export interface TaskResourceRequirement {
  type: 'stamina' | 'energy' | 'currency' | 'item' | 'character_level' | 'equipment';
  name: string;
  required: number;
  current?: number;
  isAvailable: boolean;
}

// 任务时间窗口类型
export interface TaskTimeWindow {
  startTime?: Date;
  endTime?: Date;
  duration?: number; // 分钟
  isTimeLimited: boolean;
  resetType?: 'daily' | 'weekly' | 'monthly' | 'never';
  nextResetTime?: Date;
}

// 任务信息收集相关类型
export interface TaskInfo {
  id: string;
  taskType: TaskType;
  taskName: string;
  name: string; // 任务名称别名
  type: TaskType; // 任务类型别名
  description: string;
  prerequisites: string[]; // 前置条件
  rewards: TaskReward[];
  estimatedTime: number; // 预估完成时间（分钟）
  difficulty: 'easy' | 'medium' | 'hard' | 'extreme';
  location: string; // 任务位置
  npcName?: string; // 相关NPC
  chapter?: string; // 所属章节（主线任务）
  questLine?: string; // 任务线（支线任务）
  isRepeatable: boolean;
  collectTime: Date;
  lastUpdated: Date;
  steps?: StrategyStep[]; // 任务步骤
  confidence?: number; // 信息准确度 0-1
  requirements?: string[]; // 任务需求
  
  // 新增字段：任务分类和子分类
  category?: TaskCategory;
  subCategory?: TaskSubCategory;
  tags?: string[]; // 任务标签
  
  // 新增字段：任务依赖关系
  dependencies?: TaskDependency[];
  dependents?: string[]; // 依赖此任务的其他任务ID
  
  // 新增字段：任务完成条件
  completionConditions?: TaskCompletionCondition[];
  progressTracking?: {
    isTrackable: boolean;
    trackingMethod: 'automatic' | 'manual' | 'hybrid';
    updateInterval: number; // 秒
  };
  
  // 新增字段：任务资源需求
  resourceRequirements?: TaskResourceRequirement[];
  recommendedLevel?: {
    character: number;
    equipment?: number;
    skill?: number;
  };
  
  // 新增字段：任务时间窗口
  timeWindow?: TaskTimeWindow;
  availability?: {
    isAvailable: boolean;
    availabilityReason?: string;
    nextAvailableTime?: Date;
  };
  
  // 新增字段：任务元数据
  metadata?: {
    source: 'game_data' | 'community' | 'official_guide' | 'user_generated';
    reliability: number; // 0-1，信息可靠性
    lastVerified: Date;
    verificationCount: number;
    reportedIssues: string[];
  };
}

// 扩展的任务信息接口
export interface ExtendedTaskInfo {
  id: string;
  taskId: string;
  
  // 基本信息
  name: string;
  description: string;
  category?: TaskCategory;
  subCategory?: TaskSubCategory;
  tags?: string[];
  
  // 依赖和关系
  dependencies?: TaskDependency[];
  completionConditions?: TaskCompletionCondition[];
  resourceRequirements?: TaskResourceRequirement[];
  
  // 时间相关
  timeWindows?: TaskTimeWindow[];
  estimatedDuration?: number; // 预估持续时间（分钟）
  actualDuration?: number; // 实际持续时间
  
  // 可用性和状态
  availability?: {
    isAvailable: boolean;
    availabilityConditions: string[];
    cooldownPeriod?: number; // 冷却时间（分钟）
    maxDailyAttempts?: number;
    currentDailyAttempts: number;
  };
  
  // 奖励信息
  rewards: TaskReward[];
  
  // 难度和复杂度
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  complexity?: {
    steps: number;
    decisionPoints: number;
    variability: 'low' | 'medium' | 'high';
  };
  
  // 成功率和统计
  statistics?: {
    totalAttempts: number;
    successfulAttempts: number;
    successRate: number;
    averageCompletionTime: number;
    lastSuccessTime?: Date;
    lastFailureTime?: Date;
  };
  
  // 元数据
  metadata?: {
    source: 'manual' | 'auto_detected' | 'imported' | 'generated';
    confidence: number; // 信息准确度 0-1
    lastVerified: Date;
    verificationMethod: 'manual' | 'automated' | 'crowdsourced';
    dataQuality: {
      completeness: number; // 完整度 0-1
      accuracy: number; // 准确度 0-1
      freshness: number; // 新鲜度 0-1
    };
    customFields: Record<string, any>;
  };
  
  createdAt: Date;
  lastUpdated: Date;
}

// 任务奖励类型
export interface TaskReward {
  type: 'exp' | 'credits' | 'materials' | 'items' | 'stellar_jade';
  name: string;
  amount: number;
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
}

// 策略版本控制类型
export interface StrategyVersion {
  version: string;
  changelog: string;
  compatibility: {
    gameVersion: string;
    minClientVersion?: string;
    maxClientVersion?: string;
  };
  deprecatedAt?: Date;
  isStable: boolean;
}

// 策略适用条件类型
export interface StrategyApplicability {
  characterLevel: {
    min: number;
    max?: number;
  };
  equipmentRequirements: {
    type: string;
    minLevel?: number;
    required: boolean;
  }[];
  gameProgress: {
    chapter?: string;
    questLine?: string;
    prerequisiteTasks: string[];
  };
  timeConstraints: {
    availableTime: number; // 分钟
    preferredTimeSlot?: 'morning' | 'afternoon' | 'evening' | 'night' | 'any';
  };
  resourceConstraints: {
    stamina?: number;
    currency?: number;
    items?: { name: string; quantity: number }[];
  };
}

// 策略性能指标类型
export interface StrategyPerformanceIndicators {
  executionCount: number;
  successCount: number;
  failureCount: number;
  averageExecutionTime: number;
  averageSuccessRate: number;
  reliabilityScore: number; // 0-1
  efficiencyScore: number; // 0-1
  userRating: {
    average: number; // 0-5
    totalRatings: number;
    distribution: { [key: number]: number }; // 1-5星分布
  };
  lastPerformanceUpdate: Date;
}

// 攻略相关类型
export interface Strategy {
  id?: string;
  taskInfoId: string;
  strategyName: string;
  description: string;
  steps: StrategyStep[];
  estimatedTime: number; // 预估执行时间
  successRate: number; // 成功率（0-1）
  difficulty: 'easy' | 'medium' | 'hard';
  requirements: string[]; // 执行要求
  tips: string[]; // 攻略提示
  author: string;
  version: string;
  isVerified: boolean; // 是否已验证
  createdAt: Date;
  lastUpdated: Date;
  
  // 新增字段：版本控制
  versionHistory?: StrategyVersion[];
  currentVersion?: StrategyVersion;
  isDeprecated?: boolean;
  
  // 新增字段：适用条件
  applicability?: StrategyApplicability;
  tags?: string[];
  category?: 'speed' | 'safety' | 'resource_efficient' | 'beginner_friendly' | 'advanced';
  
  // 新增字段：性能指标
  performance?: StrategyPerformanceIndicators;
  
  // 新增字段：策略元数据
  metadata?: {
    source: 'official' | 'community' | 'ai_generated' | 'user_created';
    language: string;
    region: string;
    gameMode: string[];
    lastTested: Date;
    testEnvironment: {
      gameVersion: string;
      platform: string;
      resolution: string;
    };
  };
}

// 攻略分析模式类型
export interface AnalysisPatterns {
  commonSteps: string[];
  averageTime: number;
  successPatterns: SuccessPattern[];
}

// 成功模式类型
export interface SuccessPattern {
  stepType: string;
  frequency: number;
  successRate: number;
  conditions: string[];
}

// 评分详情类型
export interface ScoreDetails {
  timeScore: number;
  difficultyScore: number;
  successScore: number;
  reliabilityScore: number;
  resourceScore: number;
  overallScore: number;
}

// 测试结果类型
export interface TestResults {
  executionTime: number;
  successCount: number;
  failureCount: number;
  averageScore: number;
}

// 步骤执行参数类型
export interface StepExecutionParameters {
  priority: 'low' | 'medium' | 'high' | 'critical';
  executionMode: 'sequential' | 'parallel' | 'conditional';
  errorHandling: {
    onFailure: 'retry' | 'skip' | 'abort' | 'fallback';
    maxRetries: number;
    retryDelay: number; // 秒
    fallbackStepId?: string;
  };
  performance: {
    expectedDuration: number; // 秒
    maxDuration: number; // 秒
    resourceUsage: {
      cpu: 'low' | 'medium' | 'high';
      memory: 'low' | 'medium' | 'high';
      network: 'none' | 'low' | 'medium' | 'high';
    };
  };
  validation: {
    preConditions: StrategyCondition[];
    postConditions: StrategyCondition[];
    successCriteria: {
      type: 'image_match' | 'text_match' | 'state_change' | 'custom';
      criteria: string;
      threshold: number;
    }[];
  };
}

// 步骤监控数据类型
export interface StepMonitoringData {
  executionCount: number;
  successCount: number;
  failureCount: number;
  averageExecutionTime: number;
  lastExecutionTime: number;
  commonFailureReasons: {
    reason: string;
    count: number;
    lastOccurrence: Date;
  }[];
  performanceMetrics: {
    minExecutionTime: number;
    maxExecutionTime: number;
    standardDeviation: number;
  };
  lastUpdated: Date;
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
  timeout: number; // 超时时间（秒）
  retryCount: number; // 重试次数
  isOptional: boolean;
  conditions?: StrategyCondition[]; // 执行条件
  
  // 新增字段：执行参数
  executionParameters?: StepExecutionParameters;
  
  // 新增字段：步骤依赖
  dependencies?: {
    stepId: string;
    dependencyType: 'prerequisite' | 'parallel' | 'mutex';
  }[];
  
  // 新增字段：步骤变体
  variants?: {
    id: string;
    name: string;
    condition: StrategyCondition;
    action: StrategyAction;
    isDefault: boolean;
  }[];
  
  // 新增字段：监控数据
  monitoring?: StepMonitoringData;
  
  // 新增字段：步骤元数据
  metadata?: {
    difficulty: 'trivial' | 'easy' | 'medium' | 'hard' | 'expert';
    category: 'movement' | 'combat' | 'interaction' | 'ui_operation' | 'system';
    tags: string[];
    notes: string;
    screenshots?: string[]; // 截图路径
    videoGuide?: string; // 视频指南路径
    lastModified: Date;
    modifiedBy: string;
  };
}

// 攻略动作类型
export interface StrategyAction {
  type: 'click' | 'key_press' | 'move' | 'wait' | 'image_recognition' | 'text_recognition' | 'custom';
  target?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    imagePath?: string;
    text?: string;
    key?: string;
  };
  parameters?: {
    duration?: number;
    intensity?: number;
    threshold?: number;
    [key: string]: unknown;
  };
}

// 攻略条件类型
export interface StrategyCondition {
  type: 'image_exists' | 'text_exists' | 'window_title' | 'time_range' | 'custom';
  value: string;
  operator: 'equals' | 'contains' | 'not_equals' | 'greater_than' | 'less_than';
}

// 攻略评估类型
export interface StrategyEvaluation {
  id: string;
  strategyId: string;
  accountId: string;
  executionTime: number; // 实际执行时间
  success: boolean;
  errorMessage?: string;
  completionRate: number; // 完成度（0-1）
  efficiency: number; // 效率评分（0-100）
  feedback?: string; // 用户反馈
  executedAt: Date;
}

// 自动化配置类型
// 自动化级别类型
export type AutomationLevel = 'fully_automatic' | 'semi_automatic' | 'manual_confirmation';

// 自动化模式配置
export interface AutomationModeConfig {
  level: AutomationLevel;
  
  // 完全自动模式配置
  fullyAutomatic?: {
    enableAllTasks: boolean;
    autoStartOnSchedule: boolean;
    autoHandleErrors: boolean;
    autoOptimizeStrategies: boolean;
    maxConcurrentTasks: number;
    continuousOperation: boolean;
  };
  
  // 半自动模式配置
  semiAutomatic?: {
    requireConfirmationFor: {
      taskExecution: boolean;
      strategyChanges: boolean;
      errorRecovery: boolean;
      resourceIntensiveTasks: boolean;
      newTaskTypes: boolean;
    };
    autoConfirmAfterTimeout: boolean;
    confirmationTimeoutSeconds: number;
    fallbackToManual: boolean;
  };
  
  // 手动确认模式配置
  manualConfirmation?: {
    confirmBeforeEachTask: boolean;
    confirmBeforeEachStep: boolean;
    showDetailedPreview: boolean;
    allowBatchConfirmation: boolean;
    requireExplicitApproval: boolean;
  };
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
  
  // 新增：自动化模式配置
  automationMode: AutomationModeConfig;
  
  // 新增：智能优先级调整
  smartPriorityAdjustment: {
    enabled: boolean;
    basedOnHistoricalData: boolean;
    basedOnCurrentLoad: boolean;
    basedOnResourceAvailability: boolean;
    adjustmentFrequency: 'real_time' | 'hourly' | 'daily';
    learningEnabled: boolean;
    adaptationRate: number; // 0-1，学习适应速度
  };
  
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
  
  // 增强的错误恢复配置
  errorRecovery: {
    enableErrorRecovery: boolean;
    pauseOnError: boolean;
    autoRetryOnTransientErrors: boolean;
    maxAutoRetryAttempts: number;
    retryDelaySeconds: number;
    escalationRules: {
      errorType: string;
      action: 'retry' | 'skip' | 'pause' | 'notify' | 'fallback';
      maxAttempts: number;
      fallbackStrategy?: string;
    }[];
    errorLearning: {
      enabled: boolean;
      trackErrorPatterns: boolean;
      suggestPrevention: boolean;
    };
  };
  
  // 增强的通知设置
  notificationSettings: {
    onTaskComplete: boolean;
    onError: boolean;
    onOptimalStrategyFound: boolean;
    onConfirmationRequired: boolean;
    onAutomationModeChange: boolean;
    onPriorityAdjustment: boolean;
    channels: {
      inApp: boolean;
      email: boolean;
      webhook?: string;
    };
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 手动确认系统相关类型
export interface ConfirmationRequest {
  id: string;
  type: 'task_execution' | 'strategy_change' | 'error_recovery' | 'resource_intensive' | 'batch_operation';
  title: string;
  description: string;
  details: {
    taskId?: string;
    strategyId?: string;
    errorDetails?: string;
    resourceRequirements?: {
      cpu: number;
      memory: number;
      duration: number;
    };
    affectedTasks?: string[];
    estimatedImpact?: {
      timeChange: number;
      resourceChange: number;
      riskLevel: 'low' | 'medium' | 'high';
    };
  };
  options: {
    approve: {
      label: string;
      action: string;
      consequences?: string[];
    };
    reject: {
      label: string;
      action: string;
      alternatives?: string[];
    };
    modify?: {
      label: string;
      availableModifications: {
        parameter: string;
        currentValue: any;
        suggestedValues: any[];
        description: string;
      }[];
    };
  };
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timeoutSeconds?: number;
  defaultAction: 'approve' | 'reject' | 'pause';
  createdAt: Date;
  expiresAt?: Date;
  status: 'pending' | 'approved' | 'rejected' | 'modified' | 'expired' | 'cancelled';
}

export interface ConfirmationResponse {
  requestId: string;
  action: 'approve' | 'reject' | 'modify' | 'cancel';
  modifications?: Record<string, any>;
  reason?: string;
  respondedAt: Date;
  respondedBy: string; // 用户ID或系统标识
}

// 智能优先级调整相关类型
export interface PriorityAdjustmentRule {
  id: string;
  name: string;
  condition: {
    type: 'time_based' | 'resource_based' | 'performance_based' | 'user_defined';
    parameters: {
      timeWindow?: {
        start: string; // HH:mm 格式
        end: string;
        daysOfWeek?: number[]; // 0-6，周日到周六
      };
      resourceThresholds?: {
        cpuUsage?: number;
        memoryUsage?: number;
        networkLatency?: number;
      };
      performanceMetrics?: {
        successRate?: number;
        averageExecutionTime?: number;
        errorRate?: number;
      };
      customCondition?: string; // 自定义条件表达式
    };
  };
  adjustment: {
    taskTypes: TaskType[];
    priorityChange: number; // -10 到 +10
    action: 'increase' | 'decrease' | 'set_absolute';
    absoluteValue?: number; // 当action为set_absolute时使用
  };
  enabled: boolean;
  createdAt: Date;
  lastTriggered?: Date;
  triggerCount: number;
}

export interface PriorityAdjustmentHistory {
  id: string;
  ruleId: string;
  taskType: TaskType;
  oldPriority: number;
  newPriority: number;
  reason: string;
  triggeredBy: 'rule' | 'manual' | 'ai_learning';
  timestamp: Date;
  impact: {
    affectedTasks: number;
    performanceChange?: number;
    userSatisfaction?: number;
  };
}

// 通知设置类型
export interface NotificationSettings {
  enableTaskComplete: boolean;
  enableTaskFailed: boolean;
  enableSystemError: boolean;
  enableDailyReport: boolean;
  soundEnabled: boolean;
  popupEnabled: boolean;
}

// 任务收集状态类型
export type TaskCollectionStatus = 'pending' | 'collecting' | 'completed' | 'failed' | 'updated';

export interface TaskCollectionInfo {
  taskType: TaskType;
  totalTasks: number;
  collectedTasks: number;
  lastCollectionTime: Date;
  collectionProgress: number; // 0-1
  errors: string[];
  status: TaskCollectionStatus;
}

// 攻略优化相关类型
export interface StrategyOptimization {
  optimizationId: string;
  strategyId: string;
  optimizationType: 'time' | 'resource' | 'success_rate' | 'comprehensive';
  
  // 优化目标
  objectives: {
    primary: OptimizationObjective;
    secondary?: OptimizationObjective[];
  };
  
  // 优化约束
  constraints: {
    maxExecutionTime?: number; // 最大执行时间（分钟）
    maxResourceUsage?: number; // 最大资源使用率
    minSuccessRate?: number; // 最小成功率
    requiredSteps?: string[]; // 必须包含的步骤
    forbiddenSteps?: string[]; // 禁止的步骤
  };
  
  // 优化算法配置
  algorithm: {
    type: 'genetic' | 'simulated_annealing' | 'gradient_descent' | 'reinforcement_learning';
    parameters: {
      populationSize?: number;
      generations?: number;
      mutationRate?: number;
      crossoverRate?: number;
      learningRate?: number;
      explorationRate?: number;
    };
    convergenceCriteria: {
      maxIterations: number;
      targetImprovement: number;
      stagnationThreshold: number;
    };
  };
  
  // 优化结果
  result?: {
    optimizedStrategy: Strategy;
    improvementMetrics: {
      timeImprovement: number; // 百分比
      resourceImprovement: number;
      successRateImprovement: number;
      overallScore: number;
    };
    iterations: number;
    convergenceTime: number; // 毫秒
    confidence: number; // 0-1
  };
  
  // 优化历史
  history: {
    iteration: number;
    strategy: Strategy;
    score: number;
    metrics: {
      executionTime: number;
      resourceUsage: number;
      successRate: number;
    };
    timestamp: Date;
  }[];
  
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  updatedAt: Date;
}

export interface OptimizationObjective {
  metric: 'execution_time' | 'resource_usage' | 'success_rate' | 'cost' | 'user_satisfaction';
  target: 'minimize' | 'maximize';
  weight: number; // 0-1，权重
  threshold?: number; // 阈值
}

// 任务执行指标类型
export interface TaskExecutionMetricsData {
  taskId: string;
  executionId: string;
  
  // 时间指标
  timing: {
    startTime: Date;
    endTime?: Date;
    totalDuration?: number; // 毫秒
    phases: {
      phase: string;
      startTime: Date;
      endTime?: Date;
      duration?: number;
    }[];
    waitTime: number; // 等待时间
    activeTime: number; // 活跃执行时间
    idleTime: number; // 空闲时间
  };
  
  // 性能指标
  executionPerformance: {
    cpu: {
      average: number; // 平均CPU使用率
      peak: number; // 峰值CPU使用率
      samples: {
        timestamp: Date;
        usage: number;
      }[];
    };
    memory: {
      average: number; // 平均内存使用量（MB）
      peak: number; // 峰值内存使用量
      samples: {
        timestamp: Date;
        usage: number;
      }[];
    };
    network: {
      totalBytes: number; // 总网络流量
      averageLatency: number; // 平均延迟
      peakLatency: number; // 峰值延迟
      requests: {
        timestamp: Date;
        latency: number;
        bytes: number;
        success: boolean;
      }[];
    };
    disk: {
      readBytes: number;
      writeBytes: number;
      operations: {
        timestamp: Date;
        operation: 'read' | 'write';
        bytes: number;
        duration: number;
      }[];
    };
  };
  
  // 执行质量指标
  executionQuality: {
    successRate: number; // 成功率
    errorCount: number; // 错误次数
    warningCount: number; // 警告次数
    retryCount: number; // 重试次数
    accuracy: number; // 准确性评分
    completeness: number; // 完整性评分
    errors: {
      timestamp: Date;
      type: string;
      message: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      context?: any;
    }[];
  };
  
  // 用户体验指标
  userExperience: {
    responsiveness: number; // 响应性评分
    smoothness: number; // 流畅性评分
    reliability: number; // 可靠性评分
    userSatisfaction?: number; // 用户满意度
    feedbackEvents: {
      timestamp: Date;
      type: 'positive' | 'negative' | 'neutral';
      description: string;
      rating?: number; // 1-5
    }[];
  };
  
  // 资源效率指标
  efficiency: {
    resourceUtilization: number; // 资源利用率
    throughput: number; // 吞吐量
    costEffectiveness: number; // 成本效益
    energyConsumption?: number; // 能耗（可选）
    wasteMetrics: {
      timeWaste: number; // 时间浪费
      resourceWaste: number; // 资源浪费
      operationWaste: number; // 操作浪费
    };
  };
  
  // 比较基准
  benchmarks: {
    baseline: {
      executionTime: number;
      resourceUsage: number;
      successRate: number;
    };
    target: {
      executionTime: number;
      resourceUsage: number;
      successRate: number;
    };
    comparison: {
      timeImprovement: number; // 相对于基准的改进百分比
      resourceImprovement: number;
      qualityImprovement: number;
    };
  };
  
  // 环境信息
  environment: {
    systemInfo: {
      os: string;
      cpu: string;
      memory: number;
      diskSpace: number;
    };
    gameInfo: {
      version: string;
      settings: any;
      mods?: string[];
    };
    networkInfo: {
      connectionType: string;
      bandwidth: number;
      latency: number;
    };
  };
  
  // 元数据
  metadata: {
    collectionMethod: 'automatic' | 'manual' | 'hybrid';
    samplingRate: number; // 采样率
    dataQuality: number; // 数据质量评分
    completeness: number; // 数据完整性
    tags: string[];
    notes?: string;
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 攻略性能指标类型
export interface StrategyPerformanceMetricsData {
  strategyId: string;
  version: string;
  evaluationId: string;
  
  // 执行效率指标
  efficiency: {
    averageExecutionTime: number; // 平均执行时间（分钟）
    medianExecutionTime: number; // 中位数执行时间
    executionTimeVariance: number; // 执行时间方差
    timeDistribution: {
      percentile25: number;
      percentile50: number;
      percentile75: number;
      percentile90: number;
      percentile95: number;
    };
    speedIndex: number; // 速度指数（相对于基准）
  };
  
  // 成功率指标
  reliability: {
    overallSuccessRate: number; // 总体成功率
    recentSuccessRate: number; // 近期成功率
    successRateTrend: 'improving' | 'stable' | 'declining';
    failureAnalysis: {
      commonFailures: {
        reason: string;
        frequency: number;
        impact: 'low' | 'medium' | 'high';
      }[];
      failurePatterns: {
        pattern: string;
        occurrences: number;
        context: string;
      }[];
    };
    recoveryRate: number; // 从失败中恢复的比率
  };
  
  // 资源使用指标
  resourceUsage: {
    cpu: {
      average: number;
      peak: number;
      efficiency: number; // CPU效率评分
    };
    memory: {
      average: number;
      peak: number;
      leakDetection: boolean;
    };
    network: {
      totalTraffic: number;
      averageBandwidth: number;
      latencyImpact: number;
    };
    gameResources: {
      energyConsumption: number;
      itemUsage: {
        itemType: string;
        quantity: number;
        efficiency: number;
      }[];
    };
  };
  
  // 适应性指标
  adaptability: {
    environmentCompatibility: {
      gameVersions: string[];
      systemRequirements: {
        minSpecs: any;
        recommendedSpecs: any;
        compatibility: number; // 0-1
      };
    };
    scenarioFlexibility: {
      applicableScenarios: string[];
      adaptationSuccess: number; // 适应成功率
      customizationLevel: 'low' | 'medium' | 'high';
    };
    learningCapability: {
      improvementRate: number; // 改进速度
      adaptationTime: number; // 适应新环境的时间
      knowledgeRetention: number; // 知识保持率
    };
  };
  
  // 用户体验指标
  userExperience: {
    easeOfUse: number; // 易用性评分
    setupComplexity: 'simple' | 'moderate' | 'complex';
    maintenanceRequirement: 'low' | 'medium' | 'high';
    userSatisfaction: {
      averageRating: number; // 1-5
      ratingDistribution: {
        rating: number;
        count: number;
      }[];
      feedback: {
        positive: string[];
        negative: string[];
        suggestions: string[];
      };
    };
    learningCurve: {
      timeToMastery: number; // 掌握所需时间
      difficultyLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
      prerequisiteSkills: string[];
    };
  };
  
  // 竞争力分析
  competitiveness: {
    marketPosition: {
      ranking: number;
      totalStrategies: number;
      categoryRanking: {
        category: string;
        rank: number;
        total: number;
      }[];
    };
    benchmarkComparison: {
      vsTopStrategy: {
        timeDifference: number;
        successRateDifference: number;
        resourceDifference: number;
      };
      vsAverageStrategy: {
        timeDifference: number;
        successRateDifference: number;
        resourceDifference: number;
      };
    };
    uniqueAdvantages: string[];
    weaknesses: string[];
  };
  
  // 历史趋势
  trends: {
    performanceHistory: {
      date: Date;
      metrics: {
        executionTime: number;
        successRate: number;
        resourceUsage: number;
        userRating: number;
      };
    }[];
    seasonalPatterns: {
      season: string;
      performanceMultiplier: number;
      notes: string;
    }[];
    versionComparison: {
      version: string;
      releaseDate: Date;
      improvements: string[];
      regressions: string[];
      overallChange: number; // 相对改进百分比
    }[];
  };
  
  // 预测指标
  predictions: {
    futurePerformance: {
      timeHorizon: number; // 预测时间范围（天）
      expectedSuccessRate: number;
      expectedExecutionTime: number;
      confidence: number; // 预测置信度
    };
    maintenanceNeeds: {
      nextUpdateRecommended: Date;
      criticalIssues: string[];
      improvementOpportunities: string[];
    };
    obsolescenceRisk: {
      riskLevel: 'low' | 'medium' | 'high';
      timeToObsolescence: number; // 预计过时时间（天）
      mitigationStrategies: string[];
    };
  };
  
  // 元数据
  metadata: {
    evaluationPeriod: {
      startDate: Date;
      endDate: Date;
      sampleSize: number;
    };
    dataQuality: {
      completeness: number;
      accuracy: number;
      reliability: number;
    };
    evaluationMethod: 'automated' | 'manual' | 'hybrid';
    tags: string[];
    notes?: string;
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 智能调度相关类型
export interface IntelligentScheduling {
  schedulerId: string;
  name: string;
  description?: string;
  
  // 调度策略
  strategy: {
    algorithm: 'priority_based' | 'round_robin' | 'shortest_job_first' | 'machine_learning' | 'genetic_algorithm';
    parameters: {
      timeSliceMs?: number; // 时间片（毫秒）
      priorityWeights?: {
        urgency: number;
        importance: number;
        resourceRequirement: number;
        userPreference: number;
      };
      learningRate?: number; // 机器学习算法的学习率
      explorationRate?: number; // 探索率
    };
    adaptiveSettings: {
      enableDynamicAdjustment: boolean;
      adjustmentInterval: number; // 调整间隔（分钟）
      performanceThreshold: number; // 性能阈值
    };
  };
  
  // 资源管理
  resourceManagement: {
    maxConcurrentTasks: number;
    resourceLimits: {
      cpu: number; // 最大CPU使用率
      memory: number; // 最大内存使用量（MB）
      network: number; // 最大网络带宽
      gameInstances: number; // 最大游戏实例数
    };
    resourceAllocation: {
      strategy: 'fair_share' | 'priority_based' | 'demand_based' | 'predictive';
      reservationPolicy: 'strict' | 'flexible' | 'adaptive';
      overcommitRatio: number; // 超额分配比率
    };
    loadBalancing: {
      enabled: boolean;
      algorithm: 'least_loaded' | 'round_robin' | 'weighted_round_robin' | 'consistent_hashing';
      healthCheckInterval: number; // 健康检查间隔（秒）
    };
  };
  
  // 时间管理
  timeManagement: {
    workingHours: {
      enabled: boolean;
      schedule: {
        dayOfWeek: number; // 0-6，0为周日
        startTime: string; // HH:MM格式
        endTime: string;
      }[];
      timezone: string;
    };
    deadlineManagement: {
      enableStrictDeadlines: boolean;
      bufferTime: number; // 缓冲时间（分钟）
      escalationPolicy: {
        levels: {
          threshold: number; // 剩余时间百分比
          action: 'notify' | 'prioritize' | 'reallocate_resources' | 'abort';
        }[];
      };
    };
    timeEstimation: {
      method: 'historical_average' | 'machine_learning' | 'expert_system' | 'hybrid';
      confidenceLevel: number; // 置信度
      updateFrequency: 'real_time' | 'periodic' | 'on_completion';
    };
  };
  
  // 依赖管理
  dependencyManagement: {
    resolutionStrategy: 'topological_sort' | 'critical_path' | 'parallel_execution' | 'adaptive';
    conflictResolution: {
      policy: 'first_come_first_served' | 'priority_based' | 'resource_aware' | 'user_defined';
      timeoutMs: number; // 冲突解决超时
    };
    circularDependencyHandling: {
      detection: boolean;
      resolution: 'break_cycle' | 'merge_tasks' | 'user_intervention';
    };
  };
  
  // 性能优化
  optimization: {
    objectives: {
      primary: 'minimize_time' | 'maximize_throughput' | 'minimize_resource_usage' | 'maximize_success_rate';
      secondary?: ('minimize_time' | 'maximize_throughput' | 'minimize_resource_usage' | 'maximize_success_rate')[];
    };
    constraints: {
      maxExecutionTime?: number; // 最大执行时间（分钟）
      maxResourceUsage?: number; // 最大资源使用率
      minSuccessRate?: number; // 最小成功率
    };
    adaptiveOptimization: {
      enabled: boolean;
      learningWindow: number; // 学习窗口（任务数）
      optimizationInterval: number; // 优化间隔（小时）
    };
  };
  
  // 监控和分析
  monitoring: {
    realTimeMetrics: {
      enabled: boolean;
      updateInterval: number; // 更新间隔（秒）
      metrics: ('queue_length' | 'average_wait_time' | 'resource_utilization' | 'success_rate' | 'throughput')[];
    };
    alerting: {
      enabled: boolean;
      thresholds: {
        queueLength: number;
        waitTime: number; // 分钟
        resourceUsage: number; // 百分比
        errorRate: number; // 百分比
      };
      notifications: {
        channels: ('email' | 'sms' | 'webhook' | 'in_app')[];
        escalation: {
          levels: {
            delay: number; // 升级延迟（分钟）
            recipients: string[];
          }[];
        };
      };
    };
    analytics: {
      historicalAnalysis: boolean;
      predictiveAnalysis: boolean;
      reportGeneration: {
        frequency: 'daily' | 'weekly' | 'monthly';
        format: ('pdf' | 'html' | 'json' | 'csv')[];
        recipients: string[];
      };
    };
  };
  
  // 用户交互
  userInterface: {
    dashboardConfig: {
      widgets: {
        type: 'queue_status' | 'resource_usage' | 'performance_metrics' | 'task_timeline' | 'alerts';
        position: { x: number; y: number; width: number; height: number; };
        config: any;
      }[];
      refreshInterval: number; // 刷新间隔（秒）
    };
    userControls: {
      allowManualOverride: boolean;
      allowPriorityAdjustment: boolean;
      allowResourceReallocation: boolean;
      requireApprovalFor: ('high_priority_tasks' | 'resource_intensive_tasks' | 'long_running_tasks')[];
    };
    notifications: {
      taskCompletion: boolean;
      errorAlerts: boolean;
      performanceWarnings: boolean;
      scheduleChanges: boolean;
    };
  };
  
  // 历史数据和学习
  learning: {
    dataRetention: {
      taskHistory: number; // 保留天数
      performanceMetrics: number;
      errorLogs: number;
    };
    machineLearning: {
      enabled: boolean;
      models: {
        taskDurationPrediction: {
          algorithm: string;
          accuracy: number;
          lastTrained: Date;
        };
        resourceUsagePrediction: {
          algorithm: string;
          accuracy: number;
          lastTrained: Date;
        };
        failurePrediction: {
          algorithm: string;
          accuracy: number;
          lastTrained: Date;
        };
      };
      trainingSchedule: {
        frequency: 'daily' | 'weekly' | 'monthly';
        autoRetraining: boolean;
        performanceThreshold: number; // 重训练阈值
      };
    };
    knowledgeBase: {
      bestPractices: {
        pattern: string;
        recommendation: string;
        confidence: number;
        usage: number;
      }[];
      commonIssues: {
        issue: string;
        solution: string;
        frequency: number;
      }[];
    };
  };
  
  // 配置和状态
  configuration: {
    version: string;
    environment: 'development' | 'testing' | 'production';
    features: {
      featureName: string;
      enabled: boolean;
      config?: any;
    }[];
  };
  
  status: {
    state: 'inactive' | 'starting' | 'active' | 'paused' | 'stopping' | 'error';
    health: 'healthy' | 'warning' | 'critical';
    lastHealthCheck: Date;
    uptime: number; // 运行时间（秒）
    statistics: {
      totalTasksScheduled: number;
      totalTasksCompleted: number;
      totalTasksFailed: number;
      averageWaitTime: number;
      averageExecutionTime: number;
      resourceUtilization: {
        cpu: number;
        memory: number;
        network: number;
      };
    };
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 调度任务项
export interface ScheduledTask {
  id: string;
  taskId: string;
  schedulerId: string;
  
  // 调度信息
  scheduling: {
    priority: number;
    estimatedDuration: number;
    scheduledStartTime: Date;
    actualStartTime?: Date;
    estimatedEndTime: Date;
    actualEndTime?: Date;
    queuePosition: number;
  };
  
  // 资源分配
  resourceAllocation: {
    cpu: number;
    memory: number;
    network: number;
    gameInstance?: string;
  };
  
  // 依赖关系
  dependencies: {
    prerequisiteTasks: string[];
    blockedTasks: string[];
    resourceConflicts: string[];
  };
  
  // 状态跟踪
  status: {
    state: 'queued' | 'waiting_dependencies' | 'resource_allocation' | 'executing' | 'completed' | 'failed' | 'cancelled';
    progress: number; // 0-100
    lastUpdate: Date;
    statusHistory: {
      state: string;
      timestamp: Date;
      reason?: string;
    }[];
  };
  
  // 性能指标
  metrics: {
    waitTime: number; // 等待时间（毫秒）
    executionTime?: number; // 执行时间
    resourceUsage: {
      cpu: number[];
      memory: number[];
      network: number[];
      timestamps: Date[];
    };
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 任务信息收集配置
export interface TaskInfoCollectionConfig {
  id: string;
  name: string;
  description: string;
  isEnabled: boolean;
  
  // 收集范围配置
  scope: {
    taskTypes: TaskType[]; // 要收集的任务类型
    categories: TaskCategory[]; // 要收集的任务分类
    difficulty: ('easy' | 'medium' | 'hard' | 'extreme')[]; // 要收集的难度等级
    includeRepeatable: boolean;
    includeTimeLimited: boolean;
    includeDeprecated: boolean;
  };
  
  // 收集策略配置
  strategy: {
    method: 'automatic' | 'manual' | 'hybrid';
    sources: ('game_data' | 'community' | 'official_guide' | 'user_generated')[];
    priority: 'speed' | 'accuracy' | 'completeness';
    updateFrequency: 'real_time' | 'hourly' | 'daily' | 'weekly' | 'manual';
    batchSize: number; // 批处理大小
    concurrency: number; // 并发数
  };
  
  // 数据质量配置
  quality: {
    enableValidation: boolean;
    minReliability: number; // 0-1，最小可靠性要求
    minConfidence: number; // 0-1，最小置信度要求
    requireVerification: boolean;
    autoCorrection: boolean;
    duplicateHandling: 'merge' | 'replace' | 'keep_latest' | 'manual_review';
    conflictResolution: 'auto' | 'manual' | 'weighted_average';
  };
  
  // 存储配置
  storage: {
    enableCaching: boolean;
    cacheExpiry: number; // 小时
    enableBackup: boolean;
    backupFrequency: 'daily' | 'weekly' | 'monthly';
    compressionEnabled: boolean;
    encryptionEnabled: boolean;
  };
  
  // 监控和报告配置
  monitoring: {
    enableMetrics: boolean;
    enableAlerts: boolean;
    alertThresholds: {
      errorRate: number; // 错误率阈值
      collectionDelay: number; // 收集延迟阈值（分钟）
      dataQualityScore: number; // 数据质量评分阈值
    };
    reportingFrequency: 'daily' | 'weekly' | 'monthly';
    includePerformanceMetrics: boolean;
  };
  
  // 过滤和转换配置
  processing: {
    enableFiltering: boolean;
    filters: {
      field: string;
      operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'regex';
      value: string | number;
      isActive: boolean;
    }[];
    enableTransformation: boolean;
    transformations: {
      field: string;
      operation: 'normalize' | 'format' | 'calculate' | 'extract' | 'custom';
      parameters: Record<string, unknown>;
      isActive: boolean;
    }[];
  };
  
  // 集成配置
  integration: {
    enableApiExport: boolean;
    apiEndpoints: string[];
    enableWebhooks: boolean;
    webhookUrls: string[];
    enableThirdPartySync: boolean;
    syncTargets: {
      name: string;
      type: 'database' | 'api' | 'file' | 'cloud_storage';
      config: Record<string, unknown>;
      isActive: boolean;
    }[];
  };
  
  // 元数据
  metadata: {
    createdBy: string;
    createdAt: Date;
    lastModifiedBy: string;
    lastModifiedAt: Date;
    version: string;
    tags: string[];
    notes: string;
  };
}

// 攻略分析结果类型
export interface StrategyAnalysisResult {
  taskInfoId: string;
  recommendedStrategy: Strategy;
  alternativeStrategies: Strategy[];
  analysisScore: number; // 分析评分
  confidenceLevel: number; // 置信度
  analysisTime: Date;
  factors: AnalysisFactor[]; // 分析因子
}

// 分析因子类型
export interface AnalysisFactor {
  name: string;
  weight: number; // 权重
  score: number; // 得分
  description: string;
}

// 游戏监控相关类型
export interface GameProcessInfo {
  processId: number;
  processName: string;
  pid?: number;
  windowTitle: string;
  isRunning: boolean;
  startTime: Date;
  memoryUsage: number; // MB
  cpuUsage: number; // 百分比
}

export interface GameWindowInfo {
  title: string;
  className: string;
  width: number;
  height: number;
  x: number;
  y: number;
  isVisible: boolean;
  isMinimized: boolean;
  isMaximized: boolean;
  isFullscreen: boolean;
  isFocused?: boolean;
}

export interface ThirdPartyToolInfo {
  name: string;
  processName: string;
  type: 'overlay' | 'recorder' | 'injection' | 'filter' | 'game_enhancer' | 'gpu_tool' | 'graphics_filter' | 'recording_tool' | 'unknown';
  isDetected: boolean;
  description: string;
  riskLevel: 'low' | 'medium' | 'high';
  risk?: 'low' | 'medium' | 'high';
  windowTitle?: string;
  detectionMethods?: string[];
}

export interface GameMonitorStatus {
  isRunning: boolean;
  isMonitoring: boolean;
  processInfo: GameProcessInfo | null;
  windowInfo: GameWindowInfo | null;
  thirdPartyTools: ThirdPartyToolInfo[];
  lastCheck: Date;
  errors: string[];
  gameProcess?: GameProcessInfo | null;
  gameWindow?: GameWindowInfo | null;
  isGameRunning?: boolean;
  isGameResponding?: boolean;
  hasInterference?: boolean;
  lastCheckTime?: Date;
  warnings?: string[];
}

// 游戏启动相关类型
export interface GameLaunchConfig {
  id?: string;
  gameName?: string;
  gamePath: string;
  launcherPath?: string;
  launchArguments?: string;
  workingDirectory?: string;
  autoLaunch: boolean;
  launchDelay: number; // 启动延迟（秒）
  waitForGameReady: boolean;
  maxWaitTime: number; // 最大等待时间（秒）
  terminateOnExit?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface GameLaunchResult {
  success: boolean;
  processId?: number;
  error?: string;
  message?: string;
  errorMessage?: string;
  launchTime: Date;
  readyTime?: Date;
  totalWaitTime: number;
}

// 游戏设置相关类型
export interface GameSettings {
  id: string;
  accountId: string;
  launchConfig: GameLaunchConfig;
  autoLaunch?: boolean;
  gamePath?: string;
  launchDelay?: number;
  enableMonitoring?: boolean;
  monitorSettings: {
    enabled: boolean;
    checkInterval: number; // 秒
    enableFilterDetection: boolean;
    filterCheckInterval: number; // 秒
    enableInjectionDetection: boolean;
    enableDriverFilterDetection: boolean;
    autoTerminateOnExit: boolean;
    enableProcessMonitor: boolean;
    enableWindowMonitor: boolean;
    enableThirdPartyDetection: boolean;
    alertOnInterference: boolean;
    autoRestartOnCrash: boolean;
  };
  displaySettings: {
    expectedResolution: {
      width: number;
      height: number;
    };
    allowedResolutions: Array<{
      width: number;
      height: number;
    }>;
    requireFullscreen: boolean;
    detectResolutionChanges: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
}

// 游戏状态事件类型
export type GameEventType = 
  | 'game_started'
  | 'game_stopped'
  | 'game_crashed'
  | 'window_changed'
  | 'resolution_changed'
  | 'third_party_detected'
  | 'interference_detected'
  | 'game_not_responding'
  | 'filter_detected';

// 游戏事件数据类型
export interface GameEventData {
  processId?: number;
  windowTitle?: string;
  resolution?: { width: number; height: number };
  toolName?: string;
  errorCode?: string;
  duration?: number;
  [key: string]: unknown;
}

export interface GameEvent {
  id: string;
  type: GameEventType;
  timestamp: Date;
  data: GameEventData;
  severity: 'info' | 'warning' | 'error';
  message: string;
}

// 游戏监控统计类型
export interface GameMonitorStats {
  id?: string;
  accountId?: string;
  date?: string; // YYYY-MM-DD
  totalGameTime?: number; // 总游戏时间（分钟）
  launchCount?: number; // 启动次数
  crashCount?: number; // 崩溃次数
  interferenceCount?: number; // 干扰检测次数
  averageStartupTime?: number; // 平均启动时间（秒）
  thirdPartyToolsDetected?: string[]; // 检测到的第三方工具
  createdAt?: Date;
  updatedAt?: Date;
  totalChecks: number;
  successfulChecks: number;
  failedChecks: number;
  averageResponseTime: number;
  uptime: number;
  lastError: string | null;
}

// 自动启动设置类型
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

// 自动启动结果类型
export interface AutoLaunchResult {
  success: boolean;
  message: string;
  launched?: boolean;
  monitoringStarted?: boolean;
  error?: string;
}

// 自动启动条件检查结果类型
export interface AutoLaunchConditions {
  canLaunch: boolean;
  reason: string;
  suggestions: string[];
}

// ===== Stage 1: 新增类型定义 =====

// 任务信息收集配置类型
export interface TaskInfoCollectionSettings {
  id: string;
  accountId: string;
  enabled: boolean;
  collectionInterval: number; // 收集间隔（分钟）
  autoCollectOnTaskStart: boolean;
  autoCollectOnTaskComplete: boolean;
  collectionMethods: {
    gameDataExtraction: boolean;
    imageRecognition: boolean;
    textRecognition: boolean;
    apiIntegration: boolean;
    communityData: boolean;
  };
  dataQuality: {
    minReliabilityThreshold: number; // 0-1
    requireVerification: boolean;
    maxDataAge: number; // 小时
    enableCrossPlatformValidation: boolean;
  };
  storage: {
    enableLocalCache: boolean;
    cacheExpiration: number; // 小时
    enableCloudSync: boolean;
    compressionEnabled: boolean;
  };
  privacy: {
    anonymizeData: boolean;
    excludePersonalInfo: boolean;
    dataRetentionPeriod: number; // 天
  };
  createdAt: Date;
  updatedAt: Date;
}

// 攻略优化配置类型
export interface StrategyOptimizationConfig {
  id: string;
  strategyId: string;
  optimizationGoals: {
    minimizeTime: boolean;
    maximizeSuccessRate: boolean;
    minimizeResourceUsage: boolean;
    maximizeRewards: boolean;
    minimizeRisk: boolean;
  };
  optimizationWeights: {
    timeWeight: number; // 0-1
    successRateWeight: number; // 0-1
    resourceWeight: number; // 0-1
    rewardWeight: number; // 0-1
    riskWeight: number; // 0-1
  };
  constraints: {
    maxExecutionTime: number; // 分钟
    minSuccessRate: number; // 0-1
    maxResourceUsage: {
      cpu: number; // 百分比
      memory: number; // MB
      network: number; // KB/s
    };
    requiredRewards: TaskReward[];
  };
  optimizationMethods: {
    geneticAlgorithm: boolean;
    simulatedAnnealing: boolean;
    reinforcementLearning: boolean;
    heuristicOptimization: boolean;
    machineLearning: boolean;
  };
  learningParameters: {
    learningRate: number;
    explorationRate: number;
    memorySize: number;
    batchSize: number;
    updateFrequency: number; // 次数
  };
  validationSettings: {
    enableCrossValidation: boolean;
    validationSplitRatio: number; // 0-1
    minValidationSamples: number;
    enableABTesting: boolean;
  };
  createdAt: Date;
  lastOptimized: Date;
  optimizationHistory: {
    version: string;
    improvements: {
      metric: string;
      oldValue: number;
      newValue: number;
      improvement: number; // 百分比
    }[];
    timestamp: Date;
  }[];
}

// 任务执行指标类型
export interface TaskExecutionMetricsData {
  id: string;
  taskId: string;
  accountId: string;
  executionId: string;
  startTime: Date;
  endTime?: Date;
  duration?: number; // 秒
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  
  // 性能指标
  performanceData: {
    cpuUsage: {
      average: number;
      peak: number;
      samples: number[];
      timestamps: Date[];
    };
    memoryUsage: {
      average: number; // MB
      peak: number; // MB
      samples: number[];
      timestamps: Date[];
    };
    networkUsage: {
      bytesReceived: number;
      bytesSent: number;
      requestCount: number;
      averageLatency: number; // ms
    };
    diskIO: {
      bytesRead: number;
      bytesWritten: number;
      operationCount: number;
    };
  };
  
  // 执行质量指标
  qualityMetrics: {
    accuracy: number; // 0-1
    precision: number; // 0-1
    completeness: number; // 0-1
    reliability: number; // 0-1
    consistency: number; // 0-1
  };
  
  // 错误和异常
  errors: {
    errorCount: number;
    criticalErrors: number;
    warningCount: number;
    errorTypes: {
      type: string;
      count: number;
      lastOccurrence: Date;
    }[];
    recoveryAttempts: number;
    successfulRecoveries: number;
  };
  
  // 步骤级别指标
  stepMetrics: {
    stepId: string;
    stepName: string;
    startTime: Date;
    endTime?: Date;
    duration?: number; // 秒
    success: boolean;
    retryCount: number;
    errorMessage?: string;
    performance: {
      cpuUsage: number;
      memoryUsage: number;
      networkLatency?: number;
    };
  }[];
  
  // 资源利用率
  resourceUtilization: {
    overallEfficiency: number; // 0-1
    resourceWaste: number; // 0-1
    bottleneckSteps: string[];
    optimizationOpportunities: {
      step: string;
      type: 'cpu' | 'memory' | 'network' | 'disk';
      potentialImprovement: number; // 百分比
    }[];
  };
  
  createdAt: Date;
  updatedAt: Date;
}

// 攻略性能指标类型
export interface StrategyPerformanceMetricsData {
  id: string;
  strategyId: string;
  version: string;
  evaluationPeriod: {
    startDate: Date;
    endDate: Date;
    totalExecutions: number;
  };
  
  // 成功率指标
  successMetrics: {
    overallSuccessRate: number; // 0-1
    successRateByAccount: {
      accountId: string;
      successRate: number;
      executionCount: number;
    }[];
    successRateByTimeOfDay: {
      hour: number;
      successRate: number;
      executionCount: number;
    }[];
    successRateByDayOfWeek: {
      dayOfWeek: number; // 0-6
      successRate: number;
      executionCount: number;
    }[];
    successRateTrend: {
      date: Date;
      successRate: number;
      executionCount: number;
    }[];
  };
  
  // 时间性能指标
  timeMetrics: {
    averageExecutionTime: number; // 秒
    medianExecutionTime: number; // 秒
    minExecutionTime: number; // 秒
    maxExecutionTime: number; // 秒
    standardDeviation: number;
    timeDistribution: {
      range: string; // "0-60s", "60-120s", etc.
      count: number;
      percentage: number;
    }[];
    timeByStep: {
      stepId: string;
      stepName: string;
      averageTime: number;
      percentage: number; // 占总时间的百分比
    }[];
  };
  
  // 资源效率指标
  efficiencyMetrics: {
    resourceEfficiency: number; // 0-1
    cpuEfficiency: number; // 0-1
    memoryEfficiency: number; // 0-1
    networkEfficiency: number; // 0-1
    costEffectiveness: number; // 0-1
    energyEfficiency: number; // 0-1
  };
  
  // 可靠性指标
  reliabilityMetrics: {
    stability: number; // 0-1
    consistency: number; // 0-1
    predictability: number; // 0-1
    errorRate: number; // 0-1
    recoveryRate: number; // 0-1
    mtbf: number; // Mean Time Between Failures (小时)
    mttr: number; // Mean Time To Recovery (分钟)
  };
  
  // 用户满意度指标
  satisfactionMetrics: {
    averageRating: number; // 1-5
    ratingDistribution: {
      rating: number;
      count: number;
      percentage: number;
    }[];
    userFeedback: {
      positive: number;
      neutral: number;
      negative: number;
    };
    recommendationScore: number; // 0-100 (NPS)
  };
  
  // 比较指标
  comparativeMetrics: {
    rankingAmongStrategies: number;
    performanceVsBenchmark: number; // 百分比差异
    improvementOverPreviousVersion: {
      successRate: number; // 百分比改进
      executionTime: number; // 百分比改进
      resourceUsage: number; // 百分比改进
    };
  };
  
  // 预测指标
  predictiveMetrics: {
    expectedFuturePerformance: {
      successRate: number;
      executionTime: number;
      confidence: number; // 0-1
    };
    degradationRate: number; // 性能下降率
    maintenanceNeeded: boolean;
    estimatedLifespan: number; // 天
  };
  
  lastUpdated: Date;
  nextUpdateScheduled: Date;
}

// 智能调度配置类型
export interface IntelligentSchedulingConfig {
  id: string;
  accountId: string;
  enabled: boolean;
  
  // 调度策略
  schedulingStrategy: {
    algorithm: 'fifo' | 'priority' | 'round_robin' | 'shortest_job_first' | 'ai_optimized';
    priorityWeights: {
      taskType: number; // 0-1
      urgency: number; // 0-1
      resourceRequirement: number; // 0-1
      successProbability: number; // 0-1
      userPreference: number; // 0-1
    };
    loadBalancing: {
      enabled: boolean;
      maxConcurrentTasks: number;
      resourceThresholds: {
        cpu: number; // 百分比
        memory: number; // 百分比
        network: number; // 百分比
      };
    };
  };
  
  // 时间管理
  timeManagement: {
    workingHours: {
      enabled: boolean;
      startTime: string; // "HH:MM"
      endTime: string; // "HH:MM"
      timezone: string;
      weekdays: boolean[];
    };
    taskTimeWindows: {
      taskType: TaskType;
      preferredStartTime: string;
      preferredEndTime: string;
      maxDuration: number; // 分钟
      allowOvertime: boolean;
    }[];
    breakManagement: {
      enabled: boolean;
      minBreakDuration: number; // 分钟
      maxContinuousWork: number; // 分钟
      breakFrequency: number; // 每小时
    };
  };
  
  // 资源管理
  resourceManagement: {
    dynamicAllocation: boolean;
    resourcePrediction: boolean;
    resourceReservation: {
      enabled: boolean;
      reservationWindow: number; // 分钟
      priorityTasks: TaskType[];
    };
    resourceOptimization: {
      enabled: boolean;
      optimizationInterval: number; // 分钟
      targetUtilization: number; // 0-1
    };
  };
  
  // 依赖管理
  dependencyManagement: {
    automaticDependencyResolution: boolean;
    dependencyTimeout: number; // 分钟
    circularDependencyDetection: boolean;
    dependencyOptimization: boolean;
  };
  
  // 预测和学习
  predictiveScheduling: {
    enabled: boolean;
    predictionHorizon: number; // 小时
    learningFromHistory: boolean;
    adaptiveScheduling: boolean;
    uncertaintyHandling: {
      bufferTime: number; // 百分比
      contingencyPlanning: boolean;
      riskAssessment: boolean;
    };
  };
  
  // 异常处理
  exceptionHandling: {
    automaticRescheduling: boolean;
    failureRecovery: {
      maxRetries: number;
      retryDelay: number; // 分钟
      escalationRules: {
        condition: string;
        action: 'retry' | 'reschedule' | 'cancel' | 'notify';
        delay: number; // 分钟
      }[];
    };
    conflictResolution: {
      strategy: 'priority' | 'first_come_first_serve' | 'resource_based' | 'user_choice';
      automaticResolution: boolean;
    };
  };
  
  // 性能监控
  performanceMonitoring: {
    enabled: boolean;
    metricsCollection: {
      schedulingLatency: boolean;
      resourceUtilization: boolean;
      taskCompletionRate: boolean;
      userSatisfaction: boolean;
    };
    alerting: {
      enabled: boolean;
      thresholds: {
        schedulingDelay: number; // 分钟
        resourceUtilization: number; // 百分比
        failureRate: number; // 百分比
      };
      notificationMethods: ('email' | 'sms' | 'push' | 'in_app')[];
    };
  };
  
  // 用户偏好
  userPreferences: {
    preferredTaskOrder: TaskType[];
    avoidancePatterns: {
      taskType: TaskType;
      timeRanges: {
        startTime: string;
        endTime: string;
      }[];
      reason: string;
    }[];
    customRules: {
      id: string;
      name: string;
      condition: string;
      action: string;
      priority: number;
      enabled: boolean;
    }[];
  };
  
  createdAt: Date;
  updatedAt: Date;
  lastOptimization: Date;
  optimizationHistory: {
    timestamp: Date;
    changes: string[];
    performanceImpact: {
      metric: string;
      oldValue: number;
      newValue: number;
      improvement: number; // 百分比
    }[];
  }[];
}