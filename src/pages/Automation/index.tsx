import React, { useState, useEffect } from 'react';
import {
  Card,
  Switch,
  Button,
  Form,
  InputNumber,
  Select,
  Slider,
  Row,
  Col,
  Statistic,
  Progress,
  Alert,
  List,
  Tag,
  Space,
  Divider,
  Modal,
  message,
  Tooltip
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useGameStatus } from '../../hooks/useGameStatus';
import GameStatusDialog from '../../components/GameStatusDialog';

const { Option } = Select;

interface AutomationConfig {
  id?: number;
  taskType: 'main' | 'side' | 'daily' | 'event' | 'all';
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
  notificationSettings: {
    onTaskComplete: boolean;
    onError: boolean;
    onOptimalStrategyFound: boolean;
  };
  createdAt?: Date;
  updatedAt?: Date;
}

interface AutomationStatus {
  isRunning: boolean;
  currentTasks: string[];
  lastExecutionTime?: Date;
  nextScheduledTime?: Date;
  totalTasksCompleted: number;
  successRate: number;
  errors: string[];
}

interface AutomationStatistics {
  totalTasksCompleted: number;
  successRate: number;
  averageExecutionTime: number;
  errorCount: number;
}

const Automation: React.FC = () => {
  const [form] = Form.useForm();
  const [config, setConfig] = useState<AutomationConfig | null>(null);
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [statistics, setStatistics] = useState<AutomationStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  
  // 游戏状态管理
  const {
    gameStatus,
    loading: gameStatusLoading,
    showGameDialog,
    setShowGameDialog,
    checkGameStatus,
    launchGame,
    checkAndPromptIfNeeded
  } = useGameStatus();

  // 获取自动化配置
  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/tasks/automation/config');
      const data = await response.json();
      if (data.success) {
        setConfig(data.data);
        form.setFieldsValue(data.data);
      }
    } catch (error) {
      console.error('获取自动化配置失败:', error);
      message.error('获取自动化配置失败');
    }
  };

  // 获取自动化状态
  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/tasks/automation/status');
      const data = await response.json();
      if (data.success) {
        setStatus(data.data);
      }
    } catch (error) {
      console.error('获取自动化状态失败:', error);
    }
  };

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/tasks/automation/statistics');
      const data = await response.json();
      if (data.success) {
        setStatistics(data.data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 处理启动自动化按钮点击
  const handleStartAutomationClick = async () => {
    // 检查游戏状态，如果游戏未启动则提示用户
    const canProceed = await checkAndPromptIfNeeded();
    if (canProceed) {
      await startAutomation();
    }
  };

  // 启动自动化
  const startAutomation = async () => {
    setLoading(true);
    try {
      // 再次检查游戏状态
      const isGameRunning = await checkGameStatus();
      if (!isGameRunning) {
        message.error('游戏未启动，无法启动自动化管理');
        setLoading(false);
        return;
      }

      const response = await fetch('/api/tasks/automation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config })
      });
      const data = await response.json();
      if (data.success) {
        message.success('自动化管理启动成功');
        await fetchStatus();
      } else {
        message.error(data.message || '启动失败');
      }
    } catch (error) {
      console.error('启动自动化失败:', error);
      message.error('启动自动化失败');
    } finally {
      setLoading(false);
    }
  };

  // 停止自动化
  const stopAutomation = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/tasks/automation/stop', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        message.success('自动化管理停止成功');
        await fetchStatus();
      } else {
        message.error(data.message || '停止失败');
      }
    } catch (error) {
      console.error('停止自动化失败:', error);
      message.error('停止自动化失败');
    } finally {
      setLoading(false);
    }
  };

  // 手动触发任务信息收集
  const triggerCollect = async () => {
    try {
      const response = await fetch('/api/tasks/automation/trigger/collect', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        message.success('任务信息收集已触发');
        await fetchStatus();
      } else {
        message.error(data.message || '触发失败');
      }
    } catch (error) {
      console.error('触发收集失败:', error);
      message.error('触发收集失败');
    }
  };

  // 手动触发攻略分析
  const triggerAnalyze = async () => {
    try {
      const response = await fetch('/api/tasks/automation/trigger/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      const data = await response.json();
      if (data.success) {
        message.success('攻略分析已触发');
        await fetchStatus();
      } else {
        message.error(data.message || '触发失败');
      }
    } catch (error) {
      console.error('触发分析失败:', error);
      message.error('触发分析失败');
    }
  };

  // 清理错误日志
  const clearErrors = async () => {
    try {
      const response = await fetch('/api/tasks/automation/clear-errors', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        message.success('错误日志已清理');
        await fetchStatus();
      } else {
        message.error(data.message || '清理失败');
      }
    } catch (error) {
      console.error('清理错误失败:', error);
      message.error('清理错误失败');
    }
  };

  // 保存配置
  const saveConfig = async (values: any) => {
    try {
      const response = await fetch('/api/tasks/automation/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });
      const data = await response.json();
      if (data.success) {
        message.success('配置保存成功');
        setConfig({ ...config, ...values });
        setConfigModalVisible(false);
      } else {
        message.error(data.message || '保存失败');
      }
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败');
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchStatus();
    fetchStatistics();

    // 定时刷新状态
    const interval = setInterval(() => {
      fetchStatus();
      fetchStatistics();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (isRunning: boolean) => {
    return isRunning ? '#52c41a' : '#d9d9d9';
  };

  const getTaskTypeLabel = (type: string) => {
    const labels = {
      main: '主线任务',
      side: '支线任务',
      daily: '日常任务',
      event: '活动任务',
      all: '所有任务'
    };
    return labels[type as keyof typeof labels] || type;
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">自动化管理</h1>
        <p className="text-gray-600">配置和控制任务自动化执行，减少手动操作</p>
      </div>

      {/* 状态概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行状态"
              value={status?.isRunning ? '运行中' : '已停止'}
              valueStyle={{ color: getStatusColor(status?.isRunning || false) }}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成任务"
              value={statistics?.totalTasksCompleted || 0}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="成功率"
              value={((statistics?.successRate || 0) * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ 
                color: (statistics?.successRate || 0) > 0.8 ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="错误数量"
              value={statistics?.errorCount || 0}
              valueStyle={{ color: (statistics?.errorCount || 0) > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 控制面板 */}
      <Card title="控制面板" className="mb-6">
        <Space size="large">
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleStartAutomationClick}
            loading={loading || gameStatusLoading}
            disabled={status?.isRunning}
          >
            启动自动化
          </Button>
          <Button
            icon={<PauseCircleOutlined />}
            onClick={stopAutomation}
            loading={loading}
            disabled={!status?.isRunning}
          >
            停止自动化
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setConfigModalVisible(true)}
          >
            配置设置
          </Button>
          <Button
            icon={<InfoCircleOutlined />}
            onClick={triggerCollect}
            disabled={status?.currentTasks.includes('任务信息收集')}
          >
            收集任务信息
          </Button>
          <Button
            icon={<TrophyOutlined />}
            onClick={triggerAnalyze}
            disabled={status?.currentTasks.includes('攻略分析')}
          >
            分析攻略
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={clearErrors}
            disabled={!status?.errors.length}
          >
            清理错误
          </Button>
        </Space>
      </Card>

      {/* 当前状态 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} md={12}>
          <Card title="当前任务" size="small">
            {status?.currentTasks.length ? (
              <List
                size="small"
                dataSource={status.currentTasks}
                renderItem={(task) => (
                  <List.Item>
                    <Tag color="processing">{task}</Tag>
                  </List.Item>
                )}
              />
            ) : (
              <div className="text-gray-500 text-center py-4">暂无运行中的任务</div>
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="错误日志" size="small">
            {status?.errors.length ? (
              <List
                size="small"
                dataSource={status.errors.slice(-5)}
                renderItem={(error) => (
                  <List.Item>
                    <Alert
                      message={error}
                      type="error"
                      showIcon
                      className="w-full"
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div className="text-gray-500 text-center py-4">暂无错误</div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 配置信息 */}
      {config && (
        <Card title="当前配置" size="small">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">任务类型：</span>
                <Tag color="blue">{getTaskTypeLabel(config.taskType)}</Tag>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">执行间隔：</span>
                <span>{config.intervalMinutes} 分钟</span>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">最低成功率：</span>
                <span>{(config.minSuccessRate * 100).toFixed(0)}%</span>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">自动收集信息：</span>
                <Tag color={config.autoCollectInfo ? 'green' : 'red'}>
                  {config.autoCollectInfo ? '开启' : '关闭'}
                </Tag>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">自动分析攻略：</span>
                <Tag color={config.autoAnalyzeStrategy ? 'green' : 'red'}>
                  {config.autoAnalyzeStrategy ? '开启' : '关闭'}
                </Tag>
              </div>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <div className="mb-2">
                <span className="font-medium">自动执行任务：</span>
                <Tag color={config.autoExecuteTasks ? 'green' : 'red'}>
                  {config.autoExecuteTasks ? '开启' : '关闭'}
                </Tag>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* 配置模态框 */}
      <Modal
        title="自动化配置"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveConfig}
          initialValues={config}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="任务类型"
                name="taskType"
                rules={[{ required: true, message: '请选择任务类型' }]}
              >
                <Select>
                  <Option value="all">所有任务</Option>
                  <Option value="main">主线任务</Option>
                  <Option value="side">支线任务</Option>
                  <Option value="daily">日常任务</Option>
                  <Option value="event">活动任务</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="执行间隔（分钟）"
                name="intervalMinutes"
                rules={[{ required: true, message: '请输入执行间隔' }]}
              >
                <InputNumber min={5} max={1440} className="w-full" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>自动化功能</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="自动收集任务信息"
                name="autoCollectInfo"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="自动分析攻略"
                name="autoAnalyzeStrategy"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="自动选择最优攻略"
                name="autoSelectBestStrategy"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="自动执行任务"
                name="autoExecuteTasks"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider>执行参数</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="最低成功率"
                name="minSuccessRate"
              >
                <Slider
                  min={0.5}
                  max={1}
                  step={0.05}
                  marks={{
                    0.5: '50%',
                    0.8: '80%',
                    1: '100%'
                  }}
                  tipFormatter={(value) => `${(value! * 100).toFixed(0)}%`}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="最大重试次数"
                name="maxRetryCount"
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>资源管理</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="最大并发任务数"
                name={['resourceManagement', 'maxConcurrentTasks']}
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="体力阈值"
                name={['resourceManagement', 'energyThreshold']}
              >
                <InputNumber min={0} max={100} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="自动恢复体力"
                name={['resourceManagement', 'autoRestoreEnergy']}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider>任务优先级</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                label="主线任务"
                name={['prioritySettings', 'main']}
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="支线任务"
                name={['prioritySettings', 'side']}
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="日常任务"
                name={['prioritySettings', 'daily']}
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="活动任务"
                name={['prioritySettings', 'event']}
              >
                <InputNumber min={1} max={10} className="w-full" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>通知设置</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="任务完成通知"
                name={['notificationSettings', 'onTaskComplete']}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="错误通知"
                name={['notificationSettings', 'onError']}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="最优攻略发现通知"
                name={['notificationSettings', 'onOptimalStrategyFound']}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
      
      {/* 游戏状态检测对话框 */}
      <GameStatusDialog
        visible={showGameDialog}
        onClose={() => setShowGameDialog(false)}
        onLaunch={launchGame}
        onCancel={() => setShowGameDialog(false)}
        title="游戏未启动"
        message="检测到游戏未启动，启动自动化管理需要游戏处于运行状态。是否现在启动游戏？"
      />
    </div>
  );
};

export default Automation;