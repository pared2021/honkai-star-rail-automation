// 任务管理页面
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Popconfirm,
  message,
  Tag,
  Progress,
  Tabs,
  Row,
  Col,
  InputNumber
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { useGameStatus } from '../../hooks/useGameStatus';
import GameStatusDialog from '../../components/GameStatusDialog';

interface Task {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  accountId: string;
  configId?: string;
  progress: number;
  startTime?: string;
  endTime?: string;
  createdAt: string;
  updatedAt: string;
}

interface TaskConfig {
  id: string;
  name: string;
  type: string;
  config: any;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface Account {
  id: string;
  username: string;
  password: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

const { TabPane } = Tabs;
const { Option } = Select;

interface TasksProps {}

const Tasks: React.FC<TasksProps> = () => {
  const [runningTasks, setRunningTasks] = useState<Task[]>([]);
  const [taskHistory, setTaskHistory] = useState<Task[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [startTaskModalVisible, setStartTaskModalVisible] = useState(false);
  const [selectedTaskType, setSelectedTaskType] = useState<string>('daily');
  const [form] = Form.useForm();
  
  // 游戏状态管理
  const {
    gameStatus,
    loading: gameStatusLoading,
    checkGameStatus,
    launchGame,
    showGameDialog,
    setShowGameDialog,
    checkAndPromptIfNeeded
  } = useGameStatus();

  // 获取运行中的任务
  const fetchRunningTasks = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/tasks/running');
      const data = await response.json();
      if (data.success) {
        setRunningTasks(data.data);
      }
    } catch (error) {
      console.error('获取运行任务失败:', error);
    }
  };

  // 获取任务历史
  const fetchTaskHistory = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/tasks/history');
      const data = await response.json();
      if (data.success) {
        setTaskHistory(data.data);
      }
    } catch (error) {
      console.error('获取任务历史失败:', error);
    }
  };

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      const response = { success: true, data: [] }; // await window.electronAPI.account.list();
      if (response.success) {
        setAccounts(response.data);
      }
    } catch (error) {
      console.error('获取账号列表失败:', error);
    }
  };

  // 处理启动任务按钮点击
  const handleStartTaskClick = async () => {
    // 检查游戏状态，如果游戏未启动则显示提示对话框
    const canProceed = await checkAndPromptIfNeeded('启动任务');
    if (canProceed) {
      setStartTaskModalVisible(true);
    }
  };

  // 启动任务
  const startTask = async (values: any) => {
    try {
      setLoading(true);
      
      // 再次检查游戏状态，确保游戏正在运行
      const status = await checkGameStatus();
      if (!status.isRunning) {
        message.error('游戏未启动，无法执行任务');
        return;
      }
      
      const response = { success: true, data: { taskId: 'mock-task-id' } }; // await window.electronAPI.task.start({
        // taskType: selectedTaskType,
        // accountId: values.accountId,
        // config: values
      // });
      
      if (response.success) {
        message.success('任务启动成功');
        setStartTaskModalVisible(false);
        form.resetFields();
        await fetchRunningTasks();
      } else {
        message.error('任务启动失败');
      }
    } catch (error) {
      message.error('任务启动失败');
      console.error('启动任务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 控制任务
  const controlTask = async (taskId: string, action: 'pause' | 'resume' | 'stop') => {
    try {
      const response = { success: true }; // await window.electronAPI.task.control({ taskId, action });
      if (response.success) {
        message.success(`任务${action === 'stop' ? '停止' : action === 'pause' ? '暂停' : '恢复'}成功`);
        await fetchRunningTasks();
      } else {
        message.error('操作失败');
      }
    } catch (error) {
      message.error('操作失败');
      console.error('控制任务失败:', error);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchRunningTasks();
    fetchTaskHistory();
    fetchAccounts();
    
    // 定时刷新运行中的任务
    const interval = setInterval(fetchRunningTasks, 3000);
    return () => clearInterval(interval);
  }, []);

  // 获取任务状态颜色
  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'processing';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      case 'pending': return 'warning';
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

  // 运行中任务表格列
  const runningTaskColumns = [
    {
      title: '任务类型',
      dataIndex: 'taskType',
      key: 'taskType',
      render: (taskType: string) => getTaskTypeName(taskType)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getTaskStatusColor(status)}>{status}</Tag>
      )
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Task) => (
        <Space>
          <Button 
            size="small" 
            icon={<PauseCircleOutlined />}
            onClick={() => controlTask(record.id, 'pause')}
          >
            暂停
          </Button>
          <Button 
            size="small" 
            icon={<StopOutlined />} 
            danger
            onClick={() => controlTask(record.id, 'stop')}
          >
            停止
          </Button>
        </Space>
      )
    }
  ];

  // 历史任务表格列
  const historyTaskColumns = [
    {
      title: '任务类型',
      dataIndex: 'taskType',
      key: 'taskType',
      render: (taskType: string) => getTaskTypeName(taskType)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getTaskStatusColor(status)}>{status}</Tag>
      )
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '结束时间',
      dataIndex: 'endTime',
      key: 'endTime',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '耗时',
      key: 'duration',
      render: (_, record: Task) => {
        if (record.startTime && record.endTime) {
          const duration = new Date(record.endTime).getTime() - new Date(record.startTime).getTime();
          return `${Math.round(duration / 1000)}秒`;
        }
        return '-';
      }
    }
  ];

  // 渲染任务配置表单
  const renderTaskConfigForm = () => {
    switch (selectedTaskType) {
      case 'daily':
        return (
          <>
            <Form.Item name="enableStamina" label="启用体力消耗" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="enableCommission" label="启用委托任务" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="staminaTarget" label="体力目标值">
              <InputNumber min={0} max={240} />
            </Form.Item>
            <Form.Item name="autoCollectRewards" label="自动收集奖励" valuePropName="checked">
              <Switch />
            </Form.Item>
          </>
        );
      case 'main':
        return (
          <>
            <Form.Item name="autoDialog" label="自动对话" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="autoBattle" label="自动战斗" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="skipCutscene" label="跳过过场动画" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="battleStrategy" label="战斗策略">
              <Select>
                <Option value="auto">自动</Option>
                <Option value="conservative">保守</Option>
                <Option value="aggressive">激进</Option>
              </Select>
            </Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>任务管理</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleStartTaskClick}
          loading={gameStatusLoading}
        >
          启动任务
        </Button>
      </div>

      <Tabs defaultActiveKey="running">
        <TabPane tab="运行中任务" key="running">
          <Card>
            <Table
              columns={runningTaskColumns}
              dataSource={runningTasks}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: '暂无运行中的任务' }}
            />
          </Card>
        </TabPane>
        
        <TabPane tab="任务历史" key="history">
          <Card>
            <Table
              columns={historyTaskColumns}
              dataSource={taskHistory}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: '暂无历史任务' }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 启动任务模态框 */}
      <Modal
        title="启动任务"
        open={startTaskModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setStartTaskModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={startTask}
          initialValues={{
            taskType: 'daily',
            enableStamina: true,
            enableCommission: true,
            staminaTarget: 240,
            autoCollectRewards: true,
            autoDialog: true,
            autoBattle: true,
            skipCutscene: false,
            battleStrategy: 'auto'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="taskType" label="任务类型" required>
                <Select onChange={setSelectedTaskType}>
                  <Option value="daily">日常任务</Option>
                  <Option value="main">主线任务</Option>
                  <Option value="side">支线任务</Option>
                  <Option value="custom">自定义任务</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="accountId" label="选择账号">
                <Select placeholder="选择账号（可选）">
                  {accounts.map(account => (
                    <Option key={account.id} value={account.id}>
                      {(account as any).name} ({(account as any).gameAccount})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          {renderTaskConfigForm()}
        </Form>
      </Modal>
      
      {/* 游戏状态检测对话框 */}
      <GameStatusDialog
        visible={showGameDialog}
        onClose={() => setShowGameDialog(false)}
        onLaunch={launchGame}
        onCancel={() => setShowGameDialog(false)}
        title="游戏未启动"
        message="检测到游戏未启动，启动任务需要游戏处于运行状态。是否现在启动游戏？"
      />
    </div>
  );
};

export default Tasks;