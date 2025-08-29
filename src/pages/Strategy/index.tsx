// 攻略管理页面
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
  Tooltip,
  Rate,
  Timeline,
  List,
  Avatar,
  Popconfirm,
  Upload,
  Divider,
  Switch
} from 'antd';
import {
  ReloadOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  SearchOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  StarOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  UploadOutlined,
  DownloadOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { Strategy, StrategyEvaluation, StrategyAnalysisResult } from '../../types';
import PerformanceDashboard from '../../components/PerformanceDashboard';
import OptimizationSuggestions from '../../components/OptimizationSuggestions';
import FeedbackSystem from '../../components/FeedbackSystem';

const { TabPane } = Tabs;
const { Option } = Select;

// 预置攻略统计数据接口
interface PresetStats {
  totalStrategies: number;
  mainTaskStrategies: number;
  sideTaskStrategies: number;
  dailyTaskStrategies: number;
  eventTaskStrategies?: number;
}

interface StrategyPageProps {}

const StrategyPage: React.FC<StrategyPageProps> = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [evaluations, setEvaluations] = useState<{ [key: string]: StrategyEvaluation[] }>({});
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<StrategyAnalysisResult | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [filterTaskType, setFilterTaskType] = useState<string>('all');
  const [searchText, setSearchText] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState<string>('');
  
  // 预置攻略管理相关状态
  const [presetStrategies, setPresetStrategies] = useState<Strategy[]>([]);
  const [presetLoading, setPresetLoading] = useState(false);
  const [presetStats, setPresetStats] = useState<PresetStats | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [form] = Form.useForm();

  // 获取攻略列表
  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/tasks/strategies');
      if (response.ok) {
        const data = await response.json();
        setStrategies(data.data || []);
      } else {
        message.error('获取攻略列表失败');
      }
    } catch (error) {
      console.error('获取攻略列表失败:', error);
      message.error('获取攻略列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取攻略评估
  const fetchEvaluations = async (strategyId: string) => {
    try {
      const response = await fetch(`/api/tasks/strategies/${strategyId}/evaluations`);
      if (response.ok) {
        const data = await response.json();
        setEvaluations(prev => ({
          ...prev,
          [strategyId]: data.data || []
        }));
      }
    } catch (error) {
      console.error('获取攻略评估失败:', error);
    }
  };

  // 启动攻略分析
  const startAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/tasks/strategies/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalysisResult(data.data);
        message.success('攻略分析已启动');
        
        // 定期刷新分析状态
        const interval = setInterval(async () => {
          try {
            const statusResponse = await fetch('/api/tasks/strategies/analyze');
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              setAnalysisResult(statusData.data);
              
              if (!statusData.data.isAnalyzing) {
                clearInterval(interval);
                fetchStrategies();
              }
            }
          } catch (error) {
            console.error('获取分析状态失败:', error);
          }
        }, 3000);
        
        // 10分钟后停止刷新
        setTimeout(() => {
          clearInterval(interval);
        }, 600000);
      } else {
        message.error('启动攻略分析失败');
      }
    } catch (error) {
      console.error('启动攻略分析失败:', error);
      message.error('启动攻略分析失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取最优攻略
  const getBestStrategy = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/strategies/${taskId}/best`);
      if (response.ok) {
        const data = await response.json();
        if (data.data) {
          setSelectedStrategy(data.data);
          setDetailModalVisible(true);
          await fetchEvaluations(data.data.id);
        } else {
          message.info('该任务暂无攻略数据');
        }
      } else {
        message.error('获取最优攻略失败');
      }
    } catch (error) {
      console.error('获取最优攻略失败:', error);
      message.error('获取最优攻略失败');
    }
  };

  // 显示攻略详情
  const showStrategyDetail = async (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setDetailModalVisible(true);
    await fetchEvaluations(strategy.id);
  };

  // 过滤攻略
  const filteredStrategies = strategies.filter(strategy => {
    const matchesTaskType = filterTaskType === 'all' || true; // 暂时忽略任务类型过滤
    const matchesSearch = !searchText || 
      strategy.strategyName.toLowerCase().includes(searchText.toLowerCase()) ||
      strategy.description.toLowerCase().includes(searchText.toLowerCase());
    return matchesTaskType && matchesSearch;
  });

  // 获取评分颜色
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#1890ff';
    if (score >= 0.4) return '#faad14';
    return '#f5222d';
  };

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

  // 表格列定义
  const columns = [
    {
      title: '攻略名称',
      dataIndex: 'strategyName',
      key: 'strategyName',
      width: 200,
      render: (text: string, record: Strategy) => (
        <Space>
          <span>{text}</span>
          {record.isVerified && <Tag color="gold"><StarOutlined /> 已验证</Tag>}
        </Space>
      )
    },
    {
      title: '难度等级',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 100,
      render: (difficulty: string) => (
        <Tag color={difficulty === 'easy' ? 'green' : difficulty === 'medium' ? 'orange' : 'red'}>
          {difficulty === 'easy' ? '简单' : difficulty === 'medium' ? '中等' : '困难'}
        </Tag>
      )
    },
    {
      title: '成功率',
      dataIndex: 'successRate',
      key: 'successRate',
      width: 120,
      render: (score: number) => (
        <div>
          <Rate disabled value={score * 5} allowHalf style={{ fontSize: '12px' }} />
          <div style={{ color: getScoreColor(score), fontWeight: 'bold' }}>
            {(score * 100).toFixed(1)}%
          </div>
        </div>
      )
    },
    {
      title: '预计时间',
      dataIndex: 'estimatedTime',
      key: 'estimatedTime',
      width: 100,
      render: (time: number) => (
        <div>
          <ClockCircleOutlined /> {time}分钟
        </div>
      )
    },
    {
      title: '验证状态',
      dataIndex: 'isVerified',
      key: 'isVerified',
      width: 100,
      render: (isVerified: boolean) => (
        <div>
          <CheckCircleOutlined style={{ color: isVerified ? '#52c41a' : '#d9d9d9' }} /> 
          {isVerified ? '已验证' : '未验证'}
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString()
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
      render: (_, record: Strategy) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => showStrategyDetail(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 获取预置攻略数据
  const fetchPresetStrategies = async () => {
    setPresetLoading(true);
    try {
      const response = await fetch('/api/tasks/strategies?source=preset');
      if (response.ok) {
        const data = await response.json();
        setPresetStrategies(data.data || []);
      } else {
        message.error('获取预置攻略失败');
      }
    } catch (error) {
      console.error('获取预置攻略失败:', error);
      message.error('获取预置攻略失败');
    } finally {
      setPresetLoading(false);
    }
  };

  // 获取预置攻略统计信息
  const fetchPresetStats = async () => {
    try {
      const response = await fetch('/api/tasks/strategies/preset/stats');
      if (response.ok) {
        const data = await response.json();
        setPresetStats(data.data);
      }
    } catch (error) {
      console.error('获取预置攻略统计失败:', error);
    }
  };

  // 重新初始化预置攻略数据
  const reinitializePresetData = async () => {
    setPresetLoading(true);
    try {
      const response = await fetch('/api/tasks/strategies/preset/reinitialize', {
        method: 'POST'
      });
      if (response.ok) {
        message.success('预置攻略数据重新初始化成功');
        await fetchPresetStrategies();
        await fetchPresetStats();
      } else {
        message.error('重新初始化失败');
      }
    } catch (error) {
      console.error('重新初始化失败:', error);
      message.error('重新初始化失败');
    } finally {
      setPresetLoading(false);
    }
  };

  // 删除预置攻略
  const deletePresetStrategy = async (strategyId: string) => {
    try {
      const response = await fetch(`/api/tasks/strategies/${strategyId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        message.success('删除成功');
        await fetchPresetStrategies();
        await fetchPresetStats();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  // 编辑预置攻略
  const editPresetStrategy = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue({
      name: strategy.strategyName,
      description: strategy.description,
      taskType: 'main', // 默认任务类型
      steps: JSON.stringify(strategy.steps, null, 2)
    });
    setEditModalVisible(true);
  };

  // 保存编辑的攻略
  const saveEditedStrategy = async (values: any) => {
    try {
      const steps = JSON.parse(values.steps);
      const response = await fetch(`/api/tasks/strategies/${editingStrategy?.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...values,
          steps
        })
      });
      
      if (response.ok) {
        message.success('保存成功');
        setEditModalVisible(false);
        setEditingStrategy(null);
        form.resetFields();
        await fetchPresetStrategies();
      } else {
        message.error('保存失败');
      }
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败，请检查步骤格式');
    }
  };

  // 预置攻略表格列定义
  const presetColumns = [
    {
      title: '攻略名称',
      dataIndex: 'strategyName',
      key: 'strategyName',
      width: 200
    },
    {
      title: '难度等级',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 100,
      render: (difficulty: string) => (
        <Tag color={difficulty === 'easy' ? 'green' : difficulty === 'medium' ? 'orange' : 'red'}>
          {difficulty === 'easy' ? '简单' : difficulty === 'medium' ? '中等' : '困难'}
        </Tag>
      )
    },
    {
      title: '步骤数量',
      dataIndex: 'steps',
      key: 'stepsCount',
      width: 100,
      render: (steps: any[]) => steps?.length || 0
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string) => (
        <Tag color="blue">{source === 'preset' ? '内置' : '用户'}</Tag>
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
      width: 150,
      render: (_, record: Strategy) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => showStrategyDetail(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => editPresetStrategy(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个攻略吗？"
            onConfirm={() => deletePresetStrategy(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  useEffect(() => {
    fetchStrategies();
    fetchPresetStrategies();
    fetchPresetStats();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和操作 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <h2>攻略管理</h2>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={startAnalysis}
              loading={loading}
            >
              启动攻略分析
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchStrategies}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 分析状态 */}
      {analysisResult && (
        <Alert
          message={`分析状态: 已完成`}
          description={
            <div>
              <Progress 
                percent={100} 
                status={'success'}
                style={{ marginBottom: '8px' }}
              />
              <div>分析时间: {new Date(analysisResult.analysisTime).toLocaleString()}</div>
              <div>置信度: {(analysisResult.confidenceLevel * 100).toFixed(1)}%</div>
              <div>分析评分: {analysisResult.analysisScore.toFixed(1)}</div>
            </div>
          }
          type={'success'}
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总攻略数"
              value={strategies.length}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="最优攻略"
              value={strategies.filter(s => s.isVerified).length}
              valueStyle={{ color: '#faad14' }}
              prefix={<StarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均评分"
              value={(strategies.reduce((sum, s) => sum + s.successRate, 0) / strategies.length * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="高分攻略"
              value={strategies.filter(s => s.successRate >= 0.8).length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速查找最优攻略 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Input
              placeholder="输入任务ID查找最优攻略"
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
            />
          </Col>
          <Col span={4}>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => selectedTaskId && getBestStrategy(selectedTaskId)}
              disabled={!selectedTaskId}
            >
              查找最优攻略
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 筛选和搜索 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Input
              placeholder="搜索攻略名称或描述"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col span={8}>
            <Select
              style={{ width: '100%' }}
              placeholder="选择任务类型"
              value={filterTaskType}
              onChange={setFilterTaskType}
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

      {/* 主要内容区域 */}
      <Tabs defaultActiveKey="strategies">
        <Tabs.TabPane tab="攻略列表" key="strategies">
          {/* 攻略表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={filteredStrategies}
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
        </Tabs.TabPane>
        
        <Tabs.TabPane tab={<span><DatabaseOutlined />预置攻略管理</span>} key="preset">
          {/* 预置攻略统计 */}
          {presetStats && (
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="预置攻略总数"
                    value={presetStats.totalStrategies}
                    prefix={<DatabaseOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="主线任务攻略"
                    value={presetStats.mainTaskStrategies}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="支线任务攻略"
                    value={presetStats.sideTaskStrategies}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="日常任务攻略"
                    value={presetStats.dailyTaskStrategies}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
            </Row>
          )}
          
          {/* 预置攻略操作 */}
          <Card style={{ marginBottom: '16px' }}>
            <Row gutter={16} align="middle">
              <Col span={12}>
                <Space>
                  <Popconfirm
                    title="确定要重新初始化预置攻略数据吗？这将覆盖现有的预置攻略。"
                    onConfirm={reinitializePresetData}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="primary"
                      icon={<SyncOutlined />}
                      loading={presetLoading}
                    >
                      重新初始化预置数据
                    </Button>
                  </Popconfirm>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      fetchPresetStrategies();
                      fetchPresetStats();
                    }}
                    loading={presetLoading}
                  >
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>
          
          {/* 预置攻略表格 */}
          <Card>
            <Table
              columns={presetColumns}
              dataSource={presetStrategies}
              rowKey="id"
              loading={presetLoading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条预置攻略`
              }}
            />
          </Card>
        </Tabs.TabPane>
      </Tabs>

      {/* 编辑攻略模态框 */}
      <Modal
        title="编辑预置攻略"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingStrategy(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveEditedStrategy}
        >
          <Form.Item
            name="name"
            label="攻略名称"
            rules={[{ required: true, message: '请输入攻略名称' }]}
          >
            <Input placeholder="请输入攻略名称" />
          </Form.Item>
          
          <Form.Item
            name="taskType"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="请选择任务类型">
              <Option value="main">主线任务</Option>
              <Option value="side">支线任务</Option>
              <Option value="daily">日常任务</Option>
              <Option value="event">活动任务</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="攻略描述"
            rules={[{ required: true, message: '请输入攻略描述' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入攻略描述" />
          </Form.Item>
          
          <Form.Item
            name="steps"
            label="攻略步骤 (JSON格式)"
            rules={[
              { required: true, message: '请输入攻略步骤' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch {
                    return Promise.reject(new Error('请输入有效的JSON格式'));
                  }
                }
              }
            ]}
          >
            <Input.TextArea
              rows={10}
              placeholder="请输入JSON格式的攻略步骤"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 攻略详情模态框 */}
      <Modal
        title="攻略详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={1000}
      >
        {selectedStrategy && (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="攻略名称" span={2}>
                  <Space>
                    {selectedStrategy.strategyName}
                    {selectedStrategy.isVerified && <Tag color="gold"><StarOutlined /> 已验证攻略</Tag>}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="任务类型">
                  <Tag color={selectedStrategy.difficulty === 'easy' ? 'green' : selectedStrategy.difficulty === 'medium' ? 'blue' : 'red'}>
                    {selectedStrategy.difficulty === 'easy' ? '简单' : selectedStrategy.difficulty === 'medium' ? '中等' : '困难'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="总评分">
                  <Space>
                    <Rate disabled value={selectedStrategy.successRate * 5} allowHalf />
                    <span style={{ color: getScoreColor(selectedStrategy.successRate), fontWeight: 'bold' }}>
                      {(selectedStrategy.successRate * 100).toFixed(1)}%
                    </span>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="时间效率">
                  <div style={{ color: getScoreColor(selectedStrategy.successRate) }}>
                    <ClockCircleOutlined /> {selectedStrategy.estimatedTime}分钟
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="成功率">
                  <div style={{ color: getScoreColor(selectedStrategy.successRate) }}>
                    <CheckCircleOutlined /> {(selectedStrategy.successRate * 100).toFixed(1)}%
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="可靠性">
                  <div style={{ color: getScoreColor(selectedStrategy.successRate) }}>
                    <SafetyOutlined /> {(selectedStrategy.successRate * 100).toFixed(1)}%
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="资源消耗">
                  <div style={{ color: getScoreColor(selectedStrategy.successRate) }}>
                    <DollarOutlined /> {selectedStrategy.estimatedTime}分钟
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {selectedStrategy.description}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            
            <TabPane tab="攻略步骤" key="steps">
              <Timeline>
                {selectedStrategy.steps.map((step, index) => (
                  <Timeline.Item
                    key={index}
                    color={step.stepType === 'battle' ? 'red' : step.stepType === 'dialog' ? 'blue' : 'green'}
                  >
                    <Card size="small">
                      <div><strong>步骤 {index + 1}:</strong> {step.description}</div>
                      <div><strong>动作:</strong> {step.action.type}</div>
                      {step.action.parameters && Object.keys(step.action.parameters).length > 0 && (
                        <div><strong>参数:</strong> {JSON.stringify(step.action.parameters)}</div>
                      )}
                      {step.conditions && step.conditions.length > 0 && (
                        <div>
                          <strong>条件:</strong>
                          <Space wrap style={{ marginLeft: '8px' }}>
                            {step.conditions.map((condition, condIndex) => (
                              <Tag key={condIndex}>
                                {condition.type}: {condition.value}
                              </Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                      <div><strong>超时时间:</strong> {step.timeout}秒</div>
                    </Card>
                  </Timeline.Item>
                ))}
              </Timeline>
            </TabPane>
            
            <TabPane tab="性能分析" key="performance">
              <PerformanceDashboard strategyId={selectedStrategy.id} />
            </TabPane>
            
            <TabPane tab="优化建议" key="optimization">
              <OptimizationSuggestions strategyId={selectedStrategy.id} />
            </TabPane>
            
            <TabPane tab="用户反馈" key="feedback">
              <FeedbackSystem strategyId={selectedStrategy.id} />
            </TabPane>
            
            <TabPane tab="评估记录" key="evaluations">
              {evaluations[selectedStrategy.id] && evaluations[selectedStrategy.id].length > 0 ? (
                <List
                  dataSource={evaluations[selectedStrategy.id]}
                  renderItem={(evaluation) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Avatar 
                            style={{ 
                              backgroundColor: evaluation.success ? '#52c41a' : '#f5222d' 
                            }}
                            icon={evaluation.success ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                          />
                        }
                        title={
                          <Space>
                            <span>评估 #{evaluation.id.slice(-6)}</span>
                            <Tag color={evaluation.success ? 'success' : 'error'}>
                              {evaluation.success ? '成功' : '失败'}
                            </Tag>
                            <span>耗时: {evaluation.executionTime}秒</span>
                          </Space>
                        }
                        description={
                          <div>
                            <div>评估时间: {new Date(evaluation.executedAt).toLocaleString()}</div>
                            {evaluation.feedback && <div>反馈: {evaluation.feedback}</div>}
                            {evaluation.feedback && (
                              <div>
                                <strong>反馈:</strong>
                                <p>{evaluation.feedback}</p>
                              </div>
                            )}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <ExclamationCircleOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
                  <div style={{ marginTop: '16px', color: '#999' }}>暂无评估记录</div>
                </div>
              )}
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default StrategyPage;