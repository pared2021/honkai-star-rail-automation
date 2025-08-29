// 数据统计页面
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Select, 
  DatePicker, 
  Table, 
  Space,
  Button,
  Empty
} from 'antd';
import { 
  TrophyOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  DownloadOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { Account, Task, AccountStats } from '../../types';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface StatisticsProps {}

interface TaskStatistics {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalTime: number;
  averageTime: number;
  successRate: number;
}

const Statistics: React.FC<StatisticsProps> = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('all');
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [taskHistory, setTaskHistory] = useState<Task[]>([]);
  const [statistics, setStatistics] = useState<TaskStatistics>({
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    totalTime: 0,
    averageTime: 0,
    successRate: 0
  });
  const [loading, setLoading] = useState(false);

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/accounts');
      const data = await response.json();
      if (data.success) {
        setAccounts(data.data);
      }
    } catch (error) {
      console.error('获取账号列表失败:', error);
    }
  };

  // 获取任务历史
  const fetchTaskHistory = async () => {
    try {
      setLoading(true);
      const accountId = selectedAccountId === 'all' ? undefined : selectedAccountId;
      const response = await fetch('http://localhost:3001/api/task/history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ accountId })
      });
      const data = await response.json();
      if (data.success) {
        let tasks = data.data;
        
        // 根据日期范围过滤
        if (dateRange && dateRange[0] && dateRange[1]) {
          const startDate = dateRange[0].startOf('day');
          const endDate = dateRange[1].endOf('day');
          tasks = tasks.filter((task: Task) => {
            const taskDate = new Date(task.createdAt);
            return taskDate >= startDate.toDate() && taskDate <= endDate.toDate();
          });
        }
        
        setTaskHistory(tasks);
        calculateStatistics(tasks);
      }
    } catch (error) {
      console.error('获取任务历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 计算统计数据
  const calculateStatistics = (tasks: Task[]) => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.status === 'completed').length;
    const failedTasks = tasks.filter(task => task.status === 'failed').length;
    
    let totalTime = 0;
    tasks.forEach(task => {
      if (task.startTime && task.endTime) {
        totalTime += new Date(task.endTime).getTime() - new Date(task.startTime).getTime();
      }
    });
    
    const averageTime = totalTasks > 0 ? totalTime / totalTasks : 0;
    const successRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
    
    setStatistics({
      totalTasks,
      completedTasks,
      failedTasks,
      totalTime,
      averageTime,
      successRate
    });
  };

  // 刷新数据
  const refreshData = () => {
    fetchTaskHistory();
  };

  // 导出数据
  const exportData = () => {
    // TODO: 实现数据导出功能
    console.log('导出数据功能待实现');
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchAccounts();
  }, []);

  // 当筛选条件变化时重新获取数据
  useEffect(() => {
    fetchTaskHistory();
  }, [selectedAccountId, dateRange]);

  // 格式化时间
  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}小时${minutes % 60}分钟`;
    } else if (minutes > 0) {
      return `${minutes}分钟${seconds % 60}秒`;
    } else {
      return `${seconds}秒`;
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

  // 任务历史表格列
  const taskColumns = [
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
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          completed: { color: '#52c41a', text: '已完成' },
          failed: { color: '#ff4d4f', text: '失败' },
          cancelled: { color: '#d9d9d9', text: '已取消' }
        };
        const config = statusMap[status] || { color: '#1890ff', text: status };
        return <span style={{ color: config.color }}>{config.text}</span>;
      }
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
          return formatTime(duration);
        }
        return '-';
      }
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>数据统计</h1>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={exportData}>
            导出数据
          </Button>
          <Button icon={<ReloadOutlined />} onClick={refreshData} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col span={6}>
            <span style={{ marginRight: '8px' }}>账号:</span>
            <Select
              value={selectedAccountId}
              onChange={setSelectedAccountId}
              style={{ width: '100%' }}
            >
              <Option value="all">全部账号</Option>
              {accounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={8}>
            <span style={{ marginRight: '8px' }}>时间范围:</span>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%' }}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={statistics.totalTasks}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="完成任务"
              value={statistics.completedTasks}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={statistics.failedTasks}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="成功率"
              value={statistics.successRate}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ 
                color: statistics.successRate >= 80 ? '#52c41a' : 
                       statistics.successRate >= 60 ? '#faad14' : '#ff4d4f'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="总耗时"
              value={formatTime(statistics.totalTime)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="平均耗时"
              value={formatTime(statistics.averageTime)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 任务历史表格 */}
      <Card title="任务历史">
        {taskHistory.length > 0 ? (
          <Table
            columns={taskColumns}
            dataSource={taskHistory}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`
            }}
          />
        ) : (
          <Empty 
            description="暂无任务数据" 
            style={{ padding: '40px' }}
          />
        )}
      </Card>
    </div>
  );
};

export default Statistics;