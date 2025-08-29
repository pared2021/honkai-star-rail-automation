import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Badge,
  Button,
  Alert,
  Descriptions,
  Progress,
  Tag,
  Space,
  Tooltip,
  message,
  Modal,
  List,
  Typography
} from 'antd';
import {
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MonitorOutlined,
  ControlOutlined,
  EyeOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import type {
  GameMonitorStatus,
  GameProcessInfo,
  GameWindowInfo,
  ThirdPartyToolInfo,
  GameMonitorStats,
  GameEvent
} from '../../types';

const { Title, Text } = Typography;

interface GameMonitorPageProps {}

const GameMonitorPage: React.FC<GameMonitorPageProps> = () => {
  const [gameStatus, setGameStatus] = useState<GameMonitorStatus>({
    isRunning: false,
    isMonitoring: false,
    processInfo: null,
    windowInfo: null,
    thirdPartyTools: [],
    lastCheck: new Date(),
    errors: []
  });
  
  const [monitorStats, setMonitorStats] = useState<GameMonitorStats>({
    totalChecks: 0,
    successfulChecks: 0,
    failedChecks: 0,
    averageResponseTime: 0,
    uptime: 0,
    lastError: null
  });
  
  const [recentEvents, setRecentEvents] = useState<GameEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterReportVisible, setFilterReportVisible] = useState(false);
  const [filterReport, setFilterReport] = useState<any>(null);

  // 获取游戏状态
  const fetchGameStatus = async () => {
    try {
      const response = await fetch('/api/game/status');
      const data = await response.json();
      if (data.success) {
        setGameStatus(data.data);
      }
    } catch (error) {
      console.error('获取游戏状态失败:', error);
    }
  };

  // 获取监控统计
  const fetchMonitorStats = async () => {
    try {
      const response = await fetch('/api/game/monitor/stats');
      const data = await response.json();
      if (data.success) {
        setMonitorStats(data.data);
      }
    } catch (error) {
      console.error('获取监控统计失败:', error);
    }
  };

  // 启动游戏监控
  const startMonitoring = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/game/monitor/start', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        message.success('游戏监控已启动');
        await fetchGameStatus();
      } else {
        message.error(data.message || '启动监控失败');
      }
    } catch (error) {
      message.error('启动监控失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 停止游戏监控
  const stopMonitoring = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/game/monitor/stop', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        message.success('游戏监控已停止');
        await fetchGameStatus();
      } else {
        message.error(data.message || '停止监控失败');
      }
    } catch (error) {
      message.error('停止监控失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 启动游戏
  const launchGame = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/game/launch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          gamePath: '', // 从设置中获取
          waitForReady: true,
          timeout: 30000
        })
      });
      const data = await response.json();
      if (data.success) {
        message.success('游戏启动成功');
        await fetchGameStatus();
      } else {
        message.error(data.message || '游戏启动失败');
      }
    } catch (error) {
      message.error('游戏启动失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 终止游戏
  const terminateGame = async () => {
    Modal.confirm({
      title: '确认终止游戏',
      content: '确定要强制终止游戏进程吗？这可能导致游戏数据丢失。',
      onOk: async () => {
        try {
          const response = await fetch('/api/game/terminate', {
            method: 'POST'
          });
          const data = await response.json();
          if (data.success) {
            message.success('游戏已终止');
            await fetchGameStatus();
          } else {
            message.error(data.message || '终止游戏失败');
          }
        } catch (error) {
          message.error('终止游戏失败');
        }
      }
    });
  };

  // 生成滤镜检测报告
  const generateFilterReport = async () => {
    try {
      const response = await fetch('/api/game/filter-report');
      const data = await response.json();
      if (data.success) {
        setFilterReport(data.data);
        setFilterReportVisible(true);
      } else {
        message.error(data.message || '生成滤镜报告失败');
      }
    } catch (error) {
      message.error('生成滤镜报告失败');
    }
  };

  // 定时刷新状态
  useEffect(() => {
    fetchGameStatus();
    fetchMonitorStats();
    
    const interval = setInterval(() => {
      if (gameStatus.isMonitoring) {
        fetchGameStatus();
        fetchMonitorStats();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [gameStatus.isMonitoring]);

  // 渲染游戏状态徽章
  const renderGameStatusBadge = () => {
    if (gameStatus.isRunning) {
      return <Badge status="success" text="运行中" />;
    } else {
      return <Badge status="error" text="未运行" />;
    }
  };

  // 渲染监控状态徽章
  const renderMonitorStatusBadge = () => {
    if (gameStatus.isMonitoring) {
      return <Badge status="processing" text="监控中" />;
    } else {
      return <Badge status="default" text="未监控" />;
    }
  };

  // 渲染第三方工具警告
  const renderThirdPartyWarnings = () => {
    if (gameStatus.thirdPartyTools.length === 0) {
      return (
        <Alert
          message="未检测到第三方工具"
          type="success"
          icon={<CheckCircleOutlined />}
          showIcon
        />
      );
    }

    return (
      <Alert
        message={`检测到 ${gameStatus.thirdPartyTools.length} 个第三方工具`}
        description={
          <List
            size="small"
            dataSource={gameStatus.thirdPartyTools}
            renderItem={(tool: ThirdPartyToolInfo) => (
              <List.Item>
                <Space>
                  <Tag color="warning">{tool.name}</Tag>
                  <Text type="secondary">{tool.description}</Text>
                  {tool.risk === 'high' && <WarningOutlined style={{ color: '#ff4d4f' }} />}
                </Space>
              </List.Item>
            )}
          />
        }
        type="warning"
        icon={<WarningOutlined />}
        showIcon
      />
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>
          <MonitorOutlined className="mr-2" />
          游戏监控中心
        </Title>
      </div>

      {/* 控制面板 */}
      <Card title="控制面板" className="mb-4">
        <Space size="middle">
          {!gameStatus.isMonitoring ? (
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={startMonitoring}
              loading={isLoading}
            >
              启动监控
            </Button>
          ) : (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={stopMonitoring}
              loading={isLoading}
            >
              停止监控
            </Button>
          )}
          
          {!gameStatus.isRunning ? (
            <Button
              type="default"
              icon={<ControlOutlined />}
              onClick={launchGame}
              loading={isLoading}
            >
              启动游戏
            </Button>
          ) : (
            <Button
              danger
              icon={<CloseCircleOutlined />}
              onClick={terminateGame}
              loading={isLoading}
            >
              终止游戏
            </Button>
          )}
          
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchGameStatus();
              fetchMonitorStats();
            }}
          >
            刷新状态
          </Button>
          
          <Button
            icon={<SafetyOutlined />}
            onClick={generateFilterReport}
          >
            滤镜检测报告
          </Button>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        {/* 游戏状态 */}
        <Col span={12}>
          <Card title="游戏状态" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="运行状态">
                {renderGameStatusBadge()}
              </Descriptions.Item>
              <Descriptions.Item label="监控状态">
                {renderMonitorStatusBadge()}
              </Descriptions.Item>
              <Descriptions.Item label="最后检查">
                {gameStatus.lastCheck.toLocaleString()}
              </Descriptions.Item>
              {gameStatus.processInfo && (
                <>
                  <Descriptions.Item label="进程ID">
                    {gameStatus.processInfo.pid}
                  </Descriptions.Item>
                  <Descriptions.Item label="内存使用">
                    {Math.round(gameStatus.processInfo.memoryUsage / 1024 / 1024)} MB
                  </Descriptions.Item>
                  <Descriptions.Item label="CPU使用率">
                    <Progress
                      percent={gameStatus.processInfo.cpuUsage}
                      size="small"
                      status={gameStatus.processInfo.cpuUsage > 80 ? 'exception' : 'normal'}
                    />
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>
          </Card>
        </Col>

        {/* 窗口信息 */}
        <Col span={12}>
          <Card title="窗口信息" size="small">
            {gameStatus.windowInfo ? (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="窗口标题">
                  {gameStatus.windowInfo.title}
                </Descriptions.Item>
                <Descriptions.Item label="分辨率">
                  {gameStatus.windowInfo.width} × {gameStatus.windowInfo.height}
                </Descriptions.Item>
                <Descriptions.Item label="窗口状态">
                  <Tag color={gameStatus.windowInfo.isVisible ? 'green' : 'red'}>
                    {gameStatus.windowInfo.isVisible ? '可见' : '隐藏'}
                  </Tag>
                  <Tag color={gameStatus.windowInfo.isFocused ? 'blue' : 'default'}>
                    {gameStatus.windowInfo.isFocused ? '焦点' : '非焦点'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="位置">
                  ({gameStatus.windowInfo.x}, {gameStatus.windowInfo.y})
                </Descriptions.Item>
              </Descriptions>
            ) : (
              <Text type="secondary">未检测到游戏窗口</Text>
            )}
          </Card>
        </Col>

        {/* 监控统计 */}
        <Col span={12}>
          <Card title="监控统计" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="总检查次数">
                {monitorStats.totalChecks}
              </Descriptions.Item>
              <Descriptions.Item label="成功率">
                <Progress
                  percent={monitorStats.totalChecks > 0 ? 
                    Math.round((monitorStats.successfulChecks / monitorStats.totalChecks) * 100) : 0
                  }
                  size="small"
                />
              </Descriptions.Item>
              <Descriptions.Item label="平均响应时间">
                {monitorStats.averageResponseTime} ms
              </Descriptions.Item>
              <Descriptions.Item label="运行时间">
                {Math.round(monitorStats.uptime / 1000)} 秒
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* 第三方工具检测 */}
        <Col span={12}>
          <Card title="第三方工具检测" size="small">
            {renderThirdPartyWarnings()}
          </Card>
        </Col>

        {/* 错误信息 */}
        {gameStatus.errors.length > 0 && (
          <Col span={24}>
            <Card title="错误信息" size="small">
              <List
                size="small"
                dataSource={gameStatus.errors}
                renderItem={(error: string) => (
                  <List.Item>
                    <Alert message={error} type="error" showIcon />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* 滤镜检测报告模态框 */}
      <Modal
        title="滤镜检测报告"
        open={filterReportVisible}
        onCancel={() => setFilterReportVisible(false)}
        footer={[
          <Button key="close" onClick={() => setFilterReportVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {filterReport && (
          <div>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="检测时间">
                {new Date(filterReport.timestamp).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="检测结果">
                <Tag color={filterReport.hasFilters ? 'red' : 'green'}>
                  {filterReport.hasFilters ? '发现滤镜' : '无滤镜'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="进程检测" span={2}>
                {filterReport.processDetection.length > 0 ? (
                  <List
                    size="small"
                    dataSource={filterReport.processDetection}
                    renderItem={(item: any) => (
                      <List.Item>
                        <Tag color="orange">{item.name}</Tag>
                        <Text>{item.description}</Text>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Text type="secondary">未发现可疑进程</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="注入检测" span={2}>
                {filterReport.injectionDetection.length > 0 ? (
                  <List
                    size="small"
                    dataSource={filterReport.injectionDetection}
                    renderItem={(item: any) => (
                      <List.Item>
                        <Tag color="red">{item.dll}</Tag>
                        <Text>{item.description}</Text>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Text type="secondary">未发现进程注入</Text>
                )}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default GameMonitorPage;