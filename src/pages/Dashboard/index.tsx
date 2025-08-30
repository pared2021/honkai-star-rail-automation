// 仪表板页面
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Alert, Progress, Typography, Space, Tag, message } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  UserOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { GameDetector } from '../../modules/GameDetector.js';
import { TaskExecutorManager } from '../../modules/TaskExecutor';
import { DailyCommissionTask } from '../../modules/DailyCommissionTask';
import { InputController } from '../../modules/InputController';
import { ImageRecognition } from '../../modules/ImageRecognition';
import { SceneDetector } from '../../modules/SceneDetector.js';
import { TemplateManager } from '../../modules/TemplateManager.js';
import { TaskType, TaskStatus } from '../../types/index.js';
import { GameScene } from '../../modules/TemplateManager.js';

interface SystemStats {
  totalAccounts: number;
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  systemUptime: number;
  memoryUsage: any;
  lastUpdated: string;
}

interface GameStatus {
  isRunning: boolean;
  isActive: boolean;
  windowInfo?: {
    title: string;
    width: number;
    height: number;
    x: number;
    y: number;
  };
  currentScene?: GameScene;
  sceneConfidence?: number;
}

interface DashboardProps {}

const Dashboard: React.FC<DashboardProps> = () => {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [gameStatus, setGameStatus] = useState<GameStatus>({ isRunning: false, isActive: false });
  const [runningTasks, setRunningTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [gameDetector] = useState(() => new GameDetector());
  const [sceneDetector] = useState(() => {
    const templateManager = new TemplateManager({
      templatesPath: 'templates'
    });
    return new SceneDetector(templateManager, {
      detectionInterval: 1000,
      confidenceThreshold: 0.8,
      autoDetection: false
    });
  });
  const [taskExecutorManager] = useState(() => {
    const manager = new TaskExecutorManager(1);
    return manager;
  });

  // 获取游戏状态
  const fetchGameStatus = async () => {
    try {
      const status = await gameDetector.forceRefresh();
      
      let currentScene = GameScene.UNKNOWN;
      let sceneConfidence = 0;
      
      // 如果游戏正在运行且窗口活跃，检测当前场景
      if (status.isRunning && status.isActive && sceneDetector.isDetectionRunning()) {
        try {
          const sceneResult = await sceneDetector.detectCurrentScene();
          currentScene = sceneResult.scene;
          sceneConfidence = sceneResult.confidence;
        } catch (sceneError) {
          console.warn('场景检测失败:', sceneError);
        }
      }
      
      setGameStatus({
          isRunning: status.isRunning,
          isActive: status.isActive,
          windowInfo: status.windowInfo,
          currentScene,
          sceneConfidence
        });
    } catch (error) {
      console.error('获取游戏状态失败:', error);
      message.error('获取游戏状态失败');
    }
  };

  // 获取运行中的任务
  const fetchRunningTasks = async () => {
    try {
      const taskStatuses = taskExecutorManager.getAllTaskStatus();
      const tasks = Object.entries(taskStatuses).map(([id, status]) => ({
        id,
        status,
        type: 'daily',
        progress: status === 'completed' ? 100 : status === 'running' ? 50 : 0
      }));
      
      setRunningTasks(tasks.map(task => ({
         id: task.id,
         name: task.id === 'dailyCommission' ? '每日委托' : task.id,
         status: task.status,
         progress: task.progress,
         type: task.type,
         startTime: new Date(),
         estimatedTime: 60000 // 1分钟预估时间
       })));
      
      // 计算系统统计信息
      const totalTasks = tasks.length;
      const completedTasks = tasks.filter(t => t.status === 'completed').length;
      const failedTasks = tasks.filter(t => t.status === 'failed').length;
      const runningTasks = tasks.filter(t => t.status === 'running').length;
      
      setSystemStats({
        totalAccounts: 1,
        activeTasks: runningTasks,
        completedTasks: completedTasks,
        failedTasks: failedTasks,
        systemUptime: Date.now(),
        memoryUsage: process.memoryUsage ? process.memoryUsage() : { used: 0, total: 0 },
        lastUpdated: new Date().toISOString()
      });
    } catch (error) {
      console.error('获取运行任务失败:', error);
      message.error('获取运行任务失败');
    }
  };

  // 刷新数据
  const refreshData = async () => {
    setLoading(true);
    await Promise.all([
      fetchGameStatus(),
      fetchRunningTasks()
    ]);
    setLoading(false);
  };

  // 停止任务
  const stopTask = async (taskId: string) => {
    try {
      taskExecutorManager.cancelTask(taskId);
      message.success('任务已停止');
      await fetchRunningTasks();
    } catch (error) {
      console.error('停止任务失败:', error);
      message.error('停止任务失败');
    }
  };

  // 启动每日委托任务
  const startDailyTask = async () => {
    try {
      setLoading(true);
      
      if (!gameStatus.isRunning) {
        message.error('请先启动游戏');
        return;
      }
      
      console.log('开始启动每日委托任务');
      // 初始化每日委托任务（如果还没有注册）
      const inputController = new InputController();
      const imageRecognition = new ImageRecognition();
      
      const dailyCommissionTask = new DailyCommissionTask(
        sceneDetector,
        inputController,
        imageRecognition,
        gameDetector
      );
      
      taskExecutorManager.registerExecutor('dailyCommission', dailyCommissionTask);
      console.log('每日委托任务已注册到管理器');
      
      // 为新注册的任务执行器添加事件监听
      const handleTaskStatusChange = () => {
        console.log('任务状态变化，刷新任务列表');
        fetchRunningTasks();
      };
      
      console.log('添加任务事件监听器');
      dailyCommissionTask.on('started', handleTaskStatusChange);
      dailyCommissionTask.on('completed', handleTaskStatusChange);
      dailyCommissionTask.on('failed', handleTaskStatusChange);
      dailyCommissionTask.on('cancelled', handleTaskStatusChange);
      
      // 执行每日委托任务
      console.log('开始执行每日委托任务');
      await taskExecutorManager.executeTask('dailyCommission');
      
      message.success('每日委托任务已启动');
      await fetchRunningTasks();
    } catch (error) {
      console.error('启动任务失败:', error);
      message.error('启动任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    const initializeModules = async () => {
      try {
        console.log('Dashboard组件初始化开始');
        if (gameDetector) {
          gameDetector.startDetection();
          await fetchGameStatus();
        }
        
        if (sceneDetector) {
          // 启动场景检测
          await sceneDetector.startDetection();
          
          // 监听场景变化事件
          const handleSceneChange = (event: any) => {
            console.log('场景变化:', event);
            // 场景变化时刷新游戏状态
            fetchGameStatus();
          };
          
          sceneDetector.on('sceneChange', handleSceneChange);
        }
        
        if (taskExecutorManager) {
          console.log('开始获取运行中的任务');
          await fetchRunningTasks();
          
          // 监听任务状态变化事件
          const handleTaskStatusChange = () => {
            console.log('任务状态变化，刷新任务列表');
            fetchRunningTasks();
          };
          
          // 为所有已注册的任务执行器添加事件监听
          const setupTaskExecutorListeners = () => {
            // 获取所有任务执行器并添加监听器
            const executors = (taskExecutorManager as any).executors;
            console.log('设置任务执行器监听器，当前执行器数量:', executors?.size || 0);
            if (executors) {
              for (const [id, executor] of executors) {
                console.log('为任务执行器添加监听器:', id);
                executor.on('started', handleTaskStatusChange);
                executor.on('completed', handleTaskStatusChange);
                executor.on('failed', handleTaskStatusChange);
                executor.on('cancelled', handleTaskStatusChange);
              }
            }
          };
          
          setupTaskExecutorListeners();
        }
      } catch (error) {
        console.error('初始化模块失败:', error);
        message.error('初始化模块失败');
      }
    };
    
    initializeModules();
    
    // 设置定时刷新
    const interval = setInterval(refreshData, 5000); // 每5秒刷新一次
    
    return () => {
      clearInterval(interval);
      gameDetector.stopDetection();
      sceneDetector.stopDetection();
      sceneDetector.removeAllListeners();
    };
  }, []);

  // 获取任务状态颜色
  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'processing';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  // 获取任务类型显示名称
  const getTaskTypeName = (taskType: string) => {
    switch (taskType) {
      case 'daily': return '日常任务';
      case 'main': return '主线任务';
      case 'side': return '支线任务';
      case 'custom': return '自定义任务';
      default: return taskType;
    }
  };

  // 获取场景显示名称
  const getSceneName = (scene: GameScene) => {
    switch (scene) {
      case GameScene.MAIN_MENU: return '主菜单';
      case GameScene.LOADING: return '加载中';
      case GameScene.BATTLE: return '战斗中';
      case GameScene.DIALOGUE: return '对话中';
      case GameScene.MAP: return '地图界面';
      case GameScene.INVENTORY: return '背包界面';
      case GameScene.SHOP: return '商店界面';
      case GameScene.SETTINGS: return '设置界面';
      case GameScene.UNKNOWN: return '未知场景';
      default: return scene || '未知';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>仪表板</h1>
        <Space>
          <Button 
            type="primary"
            icon={<PlayCircleOutlined />} 
            onClick={startDailyTask}
            disabled={!gameStatus.isRunning || runningTasks.length > 0}
          >
            启动每日委托
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={refreshData} 
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 游戏状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="游戏状态"
              value={gameStatus.isRunning ? '运行中' : '未运行'}
              valueStyle={{ 
                color: gameStatus.isRunning ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="运行任务数"
              value={runningTasks.length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="今日完成任务"
              value={systemStats?.completedTasks || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="场景检测状态"
              value={sceneDetector.isDetectionRunning() ? '运行中' : '已停止'}
              valueStyle={{ 
                color: sceneDetector.isDetectionRunning() ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 游戏状态详情 */}
      {!gameStatus.isRunning && (
        <Alert
          message="游戏未运行"
          description="请先启动《崩坏：星穹铁道》游戏，然后刷新状态。"
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {gameStatus.isRunning && (gameStatus as any).windowInfo && (
        <Card title="游戏窗口信息" style={{ marginBottom: '24px' }}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Statistic title="窗口标题" value={(gameStatus as any).windowInfo?.title || '未知'} />
            </Col>
            <Col span={6}>
              <Statistic title="窗口大小" value={`${(gameStatus as any).windowInfo?.width || 0}x${(gameStatus as any).windowInfo?.height || 0}`} />
            </Col>
            <Col span={6}>
              <Statistic title="窗口位置" value={`(${(gameStatus as any).windowInfo?.x || 0}, ${(gameStatus as any).windowInfo?.y || 0})`} />
            </Col>
            <Col span={6}>
              <Statistic 
                title="当前场景" 
                value={getSceneName(gameStatus.currentScene || GameScene.UNKNOWN)}
                suffix={gameStatus.sceneConfidence ? `(${Math.round(gameStatus.sceneConfidence * 100)}%)` : ''}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 运行中的任务 */}
      <Card title="运行中的任务">
        {runningTasks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            暂无运行中的任务
          </div>
        ) : (
          <div>
            {runningTasks.map(task => (
              <Card 
                key={task.id} 
                size="small" 
                style={{ marginBottom: '12px' }}
                extra={
                  <Space>
                    <Tag color={getTaskStatusColor(task.status)}>
                      {task.status}
                    </Tag>
                    <Button 
                      size="small" 
                      icon={<StopOutlined />} 
                      onClick={() => stopTask(task.id)}
                      danger
                    >
                      停止
                    </Button>
                  </Space>
                }
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{getTaskTypeName(task.taskType)}</strong>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      任务ID: {task.id}
                    </div>
                    {task.startTime && (
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        开始时间: {new Date(task.startTime).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;