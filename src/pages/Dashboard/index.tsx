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
import { TaskExecutor } from '../../modules/TaskExecutor.js';
import { TaskType, TaskStatus } from '../../types/index.js';

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
  currentScene?: string;
}

interface DashboardProps {}

const Dashboard: React.FC<DashboardProps> = () => {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [gameStatus, setGameStatus] = useState<GameStatus>({ isRunning: false, isActive: false });
  const [runningTasks, setRunningTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [gameDetector] = useState(() => new GameDetector());
  const [taskExecutor] = useState(() => new TaskExecutor());

  // 获取游戏状态
  const fetchGameStatus = async () => {
    try {
      const status = await gameDetector.forceRefresh();
      const processInfo = await gameDetector.getGameProcessInfo();
      
      setGameStatus({
          isRunning: status.isRunning,
          isActive: status.isActive,
          windowInfo: status.windowInfo
        });
    } catch (error) {
      console.error('获取游戏状态失败:', error);
      message.error('获取游戏状态失败');
    }
  };

  // 获取运行中的任务
  const fetchRunningTasks = async () => {
    try {
      const stats = taskExecutor.getStats();
      const runningTasks = taskExecutor.getRunningTasks();
      
      setRunningTasks(runningTasks.map(task => ({
          id: task.id,
          name: task.taskType,
          type: task.taskType,
          status: task.status,
          startTime: task.startTime,
          progress: 0
        })));
      
      setSystemStats({
        totalAccounts: 1,
        activeTasks: stats.running,
        completedTasks: stats.completed,
        failedTasks: stats.failed,
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
      taskExecutor.stopAllTasks();
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
      if (!gameStatus.isRunning) {
        message.error('请先启动游戏');
        return;
      }
      
      const dailyTask = {
        id: `daily_${Date.now()}`,
        accountId: 'default',
        taskType: TaskType.DAILY,
        status: 'pending' as TaskStatus,
        config: {
          enableStamina: true,
          enableCommission: true,
          staminaTarget: 240,
          autoCollectRewards: true
        },
        createdAt: new Date()
      };
      
      taskExecutor.addTask(dailyTask);
      message.success('每日委托任务已启动');
      await fetchRunningTasks();
    } catch (error) {
      console.error('启动任务失败:', error);
      message.error('启动任务失败');
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    const initializeModules = async () => {
      try {
        if (gameDetector) {
          gameDetector.startDetection();
          await fetchGameStatus();
        }
        
        if (taskExecutor) {
          await fetchRunningTasks();
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
              <Statistic title="当前场景" value={(gameStatus as any).currentScene || '未知'} />
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