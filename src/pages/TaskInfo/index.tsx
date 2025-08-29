// 任务信息管理页面
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  message,
  Tag,
  Progress,
  Descriptions,
  Tabs,
  Row,
  Col,
  Statistic,
  Alert,
  Tooltip
} from 'antd';
import {
  ReloadOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { TaskInfo, TaskReward, TaskCollectionInfo } from '../../types';

const { TabPane } = Tabs;
const { Option } = Select;

// 任务信息页面组件属性接口
interface TaskInfoPageProps {
  // 暂无属性，保留接口以备后续扩展
}

const TaskInfoPage: React.FC<TaskInfoPageProps> = () => {
  const [taskInfos, setTaskInfos] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [collectStatus, setCollectStatus] = useState<TaskCollectionInfo | null>(null);
  const [selectedTaskInfo, setSelectedTaskInfo] = useState<TaskInfo | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchText, setSearchText] = useState('');

  // 获取任务信息列表
  const fetchTaskInfos = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/tasks/info');
      if (response.ok) {
        const data = await response.json();
        setTaskInfos(data.data || []);
      } else {
        message.error('获取任务信息失败');
      }
    } catch (error) {
      console.error('获取任务信息失败:', error);
      message.error('获取任务信息失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取收集状态
  const fetchCollectStatus = async () => {
    try {
      const response = await fetch('/api/tasks/info/collect/status');
      if (response.ok) {
        const data = await response.json();
        setCollectStatus(data.data);
      }
    } catch (error) {
      console.error('获取收集状态失败:', error);
    }
  };

  // 启动任务信息收集
  const startCollection = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/tasks/info/collect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        message.success('任务信息收集已启动');
        fetchCollectStatus();
        // 定期刷新状态
        const interval = setInterval(() => {
          fetchCollectStatus();
        }, 2000);
        
        // 5分钟后停止刷新
        setTimeout(() => {
          clearInterval(interval);
          fetchTaskInfos();
        }, 300000);
      } else {
        message.error('启动任务信息收集失败');
      }
    } catch (error) {
      console.error('启动任务信息收集失败:', error);
      message.error('启动任务信息收集失败');
    } finally {
      setLoading(false);
    }
  };

  // 显示任务详情
  const showTaskDetail = (taskInfo: TaskInfo) => {
    setSelectedTaskInfo(taskInfo);
    setDetailModalVisible(true);
  };

  // 过滤任务信息
  const filteredTaskInfos = taskInfos.filter(taskInfo => {
    const matchesType = filterType === 'all' || taskInfo.type === filterType;
    const matchesSearch = !searchText || 
      taskInfo.name.toLowerCase().includes(searchText.toLowerCase()) ||
      taskInfo.description.toLowerCase().includes(searchText.toLowerCase());
    return matchesType && matchesSearch;
  });

  // 任务类型标签颜色
  const getTaskTypeColor = (type: string) => {
    switch (type) {
      case 'main': return 'red';
      case 'side': return 'blue';
      case 'daily': return 'green';
      case 'event': return 'orange';
      default: return 'default';
    }
  };

  // 任务类型名称
  const getTaskTypeName = (type: string) => {
    switch (type) {
      case 'main': return '主线任务';
      case 'side': return '支线任务';
      case 'daily': return '日常任务';
      case 'event': return '活动任务';
      default: return '未知类型';
    }
  };

  // 难度标签颜色
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'green';
      case 'normal': return 'blue';
      case 'hard': return 'orange';
      case 'extreme': return 'red';
      default: return 'default';
    }
  };

  // 难度名称
  const getDifficultyName = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '简单';
      case 'normal': return '普通';
      case 'hard': return '困难';
      case 'extreme': return '极难';
      default: return '未知';
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: TaskInfo) => (
        <Space>
          <span>{text}</span>
          {record.isRepeatable && <Tag color="cyan">可重复</Tag>}
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => (
        <Tag color={getTaskTypeColor(type)}>
          {getTaskTypeName(type)}
        </Tag>
      )
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (difficulty: string) => (
        <Tag color={getDifficultyColor(difficulty)}>
          {getDifficultyName(difficulty)}
        </Tag>
      )
    },
    {
      title: '预计时间',
      dataIndex: 'estimatedTime',
      key: 'estimatedTime',
      width: 100,
      render: (time: number) => (
        <span>
          <ClockCircleOutlined /> {Math.round(time / 60)}分钟
        </span>
      )
    },
    {
      title: '奖励',
      dataIndex: 'rewards',
      key: 'rewards',
      width: 150,
      render: (rewards: TaskReward[]) => (
        <Space wrap>
          {rewards.slice(0, 2).map((reward, index) => (
            <Tag key={index} color="gold">
              <TrophyOutlined /> {reward.name} x{reward.amount}
            </Tag>
          ))}
          {rewards.length > 2 && (
            <Tag>+{rewards.length - 2}项</Tag>
          )}
        </Space>
      )
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record: TaskInfo) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => showTaskDetail(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  useEffect(() => {
    fetchTaskInfos();
    fetchCollectStatus();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和操作 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <h2>任务信息管理</h2>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={startCollection}
              loading={loading}
            >
              启动信息收集
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchTaskInfos}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 收集状态 */}
      {collectStatus && (
        <Alert
          message={`收集状态: ${collectStatus.status === 'collecting' ? '进行中' : '已完成'}`}
          description={
            <div>
              <Progress 
                percent={Math.round(collectStatus.collectionProgress * 100)} 
                status={collectStatus.status === 'collecting' ? 'active' : 'success'}
                style={{ marginBottom: '8px' }}
              />
              <div>已收集: {collectStatus.collectedTasks} / {collectStatus.totalTasks} 个任务</div>
              <div>最后收集时间: {new Date(collectStatus.lastCollectionTime).toLocaleString()}</div>
            </div>
          }
          type={collectStatus.status === 'collecting' ? 'info' : 'success'}
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={taskInfos.length}
              prefix={<InfoCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="主线任务"
              value={taskInfos.filter(t => t.type === 'main').length}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="支线任务"
              value={taskInfos.filter(t => t.type === 'side').length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="日常任务"
              value={taskInfos.filter(t => t.type === 'daily').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和搜索 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索任务名称或描述"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col span={8}>
            <Select
              style={{ width: '100%' }}
              placeholder="选择任务类型"
              value={filterType}
              onChange={setFilterType}
            >
              <Option value="all">全部类型</Option>
              <Option value="main">主线任务</Option>
              <Option value="side">支线任务</Option>
              <Option value="daily">日常任务</Option>
              <Option value="event">活动任务</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 任务信息表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredTaskInfos}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTaskInfo && (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="任务名称" span={2}>
                  {selectedTaskInfo.name}
                </Descriptions.Item>
                <Descriptions.Item label="任务类型">
                  <Tag color={getTaskTypeColor(selectedTaskInfo.type)}>
                    {getTaskTypeName(selectedTaskInfo.type)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="难度">
                  <Tag color={getDifficultyColor(selectedTaskInfo.difficulty)}>
                    {getDifficultyName(selectedTaskInfo.difficulty)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="预计时间">
                  {Math.round(selectedTaskInfo.estimatedTime / 60)}分钟
                </Descriptions.Item>
                <Descriptions.Item label="可重复">
                  {selectedTaskInfo.isRepeatable ? '是' : '否'}
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {selectedTaskInfo.description}
                </Descriptions.Item>
                {selectedTaskInfo.prerequisites.length > 0 && (
                  <Descriptions.Item label="前置条件" span={2}>
                    <Space wrap>
                      {selectedTaskInfo.prerequisites.map((prereq, index) => (
                        <Tag key={index}>{prereq}</Tag>
                      ))}
                    </Space>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </TabPane>
            
            <TabPane tab="奖励信息" key="rewards">
              <Table
                dataSource={selectedTaskInfo.rewards}
                columns={[
                  {
                    title: '奖励名称',
                    dataIndex: 'name',
                    key: 'name'
                  },
                  {
                    title: '类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'currency' ? 'gold' : type === 'item' ? 'blue' : 'green'}>
                        {type === 'currency' ? '货币' : type === 'item' ? '物品' : '经验'}
                      </Tag>
                    )
                  },
                  {
                    title: '数量',
                    dataIndex: 'amount',
                    key: 'amount'
                  },
                  {
                    title: '描述',
                    dataIndex: 'description',
                    key: 'description'
                  }
                ]}
                pagination={false}
                size="small"
              />
            </TabPane>
            
            {selectedTaskInfo.steps && selectedTaskInfo.steps.length > 0 && (
              <TabPane tab="任务步骤" key="steps">
                <div>
                  {selectedTaskInfo.steps.map((step, index) => (
                    <Card key={index} size="small" style={{ marginBottom: '8px' }}>
                      <div><strong>步骤 {index + 1}:</strong> {step.description}</div>
                      <div><strong>类型:</strong> {step.stepType}</div>
                      {step.expectedResult && <div><strong>预期结果:</strong> {step.expectedResult}</div>}
                      {step.conditions && step.conditions.length > 0 && (
                        <div>
                          <strong>执行条件:</strong>
                          <Space wrap style={{ marginLeft: '8px' }}>
                            {step.conditions.map((condition, condIndex) => (
                              <Tag key={condIndex}>
                                {condition.type}: {condition.value}
                              </Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </TabPane>
            )}
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default TaskInfoPage;