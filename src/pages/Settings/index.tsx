// 设置页面
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Select,
  Space,
  message,
  Divider,
  Row,
  Col,
  Tabs
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  ControlOutlined,
  SettingOutlined,
  SafetyOutlined,
  BellOutlined,
  MonitorOutlined,
  FolderOpenOutlined
} from '@ant-design/icons';

interface GameSettings {
  gameExecutablePath: string;
  gameWindowTitle: string;
  autoStartGame: boolean;
  gameStartDelay: number;
}

interface AutomationSettings {
  clickDelay: number;
  imageMatchThreshold: number;
  maxRetryAttempts: number;
  screenshotInterval: number;
  enableLogging: boolean;
}

interface SystemSettings {
  autoStartOnBoot: boolean;
  minimizeToTray: boolean;
  enableNotifications: boolean;
  logLevel: string;
  maxLogFiles: number;
}

const { TabPane } = Tabs;
const { Option } = Select;

interface SettingsProps {}

interface AppSettings {
  // 游戏设置
  gameSettings: {
    detectionInterval: number;
    autoStart: boolean;
    gameWindowTitle: string;
    screenshotQuality: number;
  };
  // 游戏监控和启动设置
  gameMonitorSettings: {
    gamePath: string;
    autoLaunchGame: boolean;
    launchDelay: number;
    enableGameMonitoring: boolean;
    monitorInterval: number;
    enableFilterDetection: boolean;
    filterCheckInterval: number;
    enableInjectionDetection: boolean;
    enableDriverFilterDetection: boolean;
    autoTerminateOnExit: boolean;
  };
  // 任务设置
  taskSettings: {
    maxConcurrentTasks: number;
    taskTimeout: number;
    retryAttempts: number;
    autoRetry: boolean;
  };
  // 安全设置
  securitySettings: {
    enableSafeMode: boolean;
    randomDelay: boolean;
    minDelay: number;
    maxDelay: number;
    enableAntiDetection: boolean;
  };
  // 通知设置
  notificationSettings: {
    enableNotifications: boolean;
    notifyOnTaskComplete: boolean;
    notifyOnTaskFailed: boolean;
    notifyOnGameClosed: boolean;
    soundEnabled: boolean;
  };
}

const Settings: React.FC<SettingsProps> = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  // 从localStorage加载设置
  const loadSettingsFromStorage = (): AppSettings => {
    try {
      const savedSettings = localStorage.getItem('app_settings');
      if (savedSettings) {
        return JSON.parse(savedSettings);
      }
    } catch (error) {
      console.error('加载设置失败:', error);
    }
    
    // 返回默认设置
    return {
      gameSettings: {
        detectionInterval: 1000,
        autoStart: false,
        gameWindowTitle: '崩坏：星穹铁道',
        screenshotQuality: 80
      },
      gameMonitorSettings: {
        gamePath: '',
        autoLaunchGame: false,
        launchDelay: 5000,
        enableGameMonitoring: true,
        monitorInterval: 5000,
        enableFilterDetection: true,
        filterCheckInterval: 30000,
        enableInjectionDetection: true,
        enableDriverFilterDetection: true,
        autoTerminateOnExit: false
      },
      taskSettings: {
        maxConcurrentTasks: 3,
        taskTimeout: 300000,
        retryAttempts: 3,
        autoRetry: true
      },
      securitySettings: {
        enableSafeMode: true,
        randomDelay: true,
        minDelay: 500,
        maxDelay: 2000,
        enableAntiDetection: true
      },
      notificationSettings: {
        enableNotifications: true,
        notifyOnTaskComplete: true,
        notifyOnTaskFailed: true,
        notifyOnGameClosed: true,
        soundEnabled: true
      }
    };
  };

  const [settings, setSettings] = useState<AppSettings>(loadSettingsFromStorage());

  // 加载设置
  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/settings');
      const data = await response.json();
      if (data.success) {
        setSettings(data.data);
        form.setFieldsValue(data.data);
      } else {
        form.setFieldsValue(settings);
      }
    } catch (error) {
      console.error('加载设置失败:', error);
      message.error('加载设置失败');
      form.setFieldsValue(settings);
    }
  };

  // 保存设置
  const saveSettings = async (values: AppSettings) => {
    try {
      setLoading(true);
      
      // 保存设置到localStorage
      localStorage.setItem('app_settings', JSON.stringify(values));
      
      // 更新状态
      setSettings(values);
      message.success('设置保存成功');
    } catch (error) {
      console.error('保存设置失败:', error);
      message.error('保存设置失败');
    } finally {
      setLoading(false);
    }
  };

  // 重置设置
  const resetSettings = () => {
    form.setFieldsValue(settings);
    message.info('设置已重置');
  };

  // 恢复默认设置
  const restoreDefaults = () => {
    const defaultSettings: AppSettings = {
      gameSettings: {
        detectionInterval: 1000,
        autoStart: false,
        gameWindowTitle: '崩坏：星穹铁道',
        screenshotQuality: 80
      },
      gameMonitorSettings: {
        gamePath: '',
        autoLaunchGame: false,
        launchDelay: 5000,
        enableGameMonitoring: true,
        monitorInterval: 5000,
        enableFilterDetection: true,
        filterCheckInterval: 30000,
        enableInjectionDetection: true,
        enableDriverFilterDetection: true,
        autoTerminateOnExit: false
      },
      taskSettings: {
        maxConcurrentTasks: 3,
        taskTimeout: 300000,
        retryAttempts: 3,
        autoRetry: true
      },
      securitySettings: {
        enableSafeMode: true,
        randomDelay: true,
        minDelay: 500,
        maxDelay: 2000,
        enableAntiDetection: true
      },
      notificationSettings: {
        enableNotifications: true,
        notifyOnTaskComplete: true,
        notifyOnTaskFailed: true,
        notifyOnGameClosed: true,
        soundEnabled: true
      }
    };
    
    form.setFieldsValue(defaultSettings);
    message.info('已恢复默认设置');
  };

  // 组件挂载时加载设置
  useEffect(() => {
    loadSettings();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>设置</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={resetSettings}>
            重置
          </Button>
          <Button onClick={restoreDefaults}>
            恢复默认
          </Button>
          <Button 
            type="primary" 
            icon={<SaveOutlined />} 
            loading={loading}
            onClick={() => form.submit()}
          >
            保存设置
          </Button>
        </Space>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={saveSettings}
        initialValues={settings}
      >
        <Tabs defaultActiveKey="game">
          {/* 游戏设置 */}
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                游戏设置
              </span>
            } 
            key="game"
          >
            <Card>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Form.Item
                    name={['gameSettings', 'detectionInterval']}
                    label="游戏检测间隔（毫秒）"
                    tooltip="检测游戏状态的时间间隔，值越小检测越频繁但消耗更多资源"
                  >
                    <InputNumber min={500} max={5000} step={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['gameSettings', 'screenshotQuality']}
                    label="截图质量（%）"
                    tooltip="截图的压缩质量，影响图像识别精度和文件大小"
                  >
                    <InputNumber min={10} max={100} step={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['gameSettings', 'gameWindowTitle']}
                    label="游戏窗口标题"
                    tooltip="用于识别游戏窗口的标题关键词"
                  >
                    <Input placeholder="崩坏：星穹铁道" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['gameSettings', 'autoStart']}
                    label="自动启动检测"
                    valuePropName="checked"
                    tooltip="程序启动时自动开始游戏检测"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* 游戏监控设置 */}
          <TabPane 
            tab={
              <span>
                <MonitorOutlined />
                游戏监控
              </span>
            } 
            key="gameMonitor"
          >
            <div>
              <Card title="游戏启动设置" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Form.Item
                      name={['gameMonitorSettings', 'gamePath']}
                      label="游戏安装路径"
                      tooltip="游戏可执行文件的完整路径"
                    >
                      <Input.Group compact>
                        <Input
                          style={{ width: 'calc(100% - 40px)' }}
                          placeholder="请选择游戏可执行文件路径"
                        />
                        <Button
                          icon={<FolderOpenOutlined />}
                          onClick={() => {
                            message.info('文件选择功能开发中...');
                          }}
                        />
                      </Input.Group>
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item
                      name={['gameMonitorSettings', 'autoLaunchGame']}
                      label="自动启动游戏"
                      valuePropName="checked"
                      tooltip="开启后，程序启动时会自动检测并启动游戏。如果关闭，只有在执行任务或自动化时才会提示启动游戏。"
                      extra={
                        <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                          <div>• 开启：程序启动时自动启动游戏</div>
                          <div>• 关闭：仅在需要时提示启动游戏（半自动模式）</div>
                          <div style={{ color: '#ff7875' }}>注意：需要先设置正确的游戏路径</div>
                        </div>
                      }
                    >
                      <Switch 
                        checkedChildren="自动启动" 
                        unCheckedChildren="半自动模式" 
                        style={{ minWidth: '100px' }}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'launchDelay']}
                      label="启动延迟（毫秒）"
                      tooltip="启动游戏前的等待时间，建议设置3-10秒"
                    >
                      <InputNumber min={0} max={30000} step={1000} style={{ width: '100%' }} placeholder="5000" />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item
                      name={['gameMonitorSettings', 'autoTerminateOnExit']}
                      label="程序退出时关闭游戏"
                      valuePropName="checked"
                      tooltip="程序退出时自动关闭游戏进程"
                    >
                      <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
              <Card title="游戏监控设置" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'enableGameMonitoring']}
                      label="启用游戏状态监控"
                      valuePropName="checked"
                      tooltip="监控游戏运行状态"
                    >
                      <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'monitorInterval']}
                      label="监控间隔（毫秒）"
                      tooltip="游戏状态监控的时间间隔"
                    >
                      <InputNumber min={1000} max={60000} step={1000} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
              <Card title="滤镜检测设置">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'enableFilterDetection']}
                      label="启用滤镜检测"
                      valuePropName="checked"
                      tooltip="检测游戏中的滤镜程序"
                    >
                      <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'filterCheckInterval']}
                      label="检测间隔（毫秒）"
                      tooltip="滤镜检测的时间间隔"
                    >
                      <InputNumber min={10000} max={300000} step={10000} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'enableInjectionDetection']}
                      label="检测进程注入"
                      valuePropName="checked"
                      tooltip="检测是否有程序注入到游戏进程"
                    >
                      <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['gameMonitorSettings', 'enableDriverFilterDetection']}
                      label="检测驱动级滤镜"
                      valuePropName="checked"
                      tooltip="检测驱动级别的滤镜程序"
                    >
                      <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </div>
          </TabPane>

          {/* 任务设置 */}
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                任务设置
              </span>
            } 
            key="task"
          >
            <Card>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Form.Item
                    name={['taskSettings', 'maxConcurrentTasks']}
                    label="最大并发任务数"
                    tooltip="同时运行的最大任务数量"
                  >
                    <InputNumber min={1} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['taskSettings', 'taskTimeout']}
                    label="任务超时时间（毫秒）"
                    tooltip="单个任务的最大执行时间"
                  >
                    <InputNumber min={60000} max={3600000} step={60000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['taskSettings', 'retryAttempts']}
                    label="重试次数"
                    tooltip="任务失败时的重试次数"
                  >
                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['taskSettings', 'autoRetry']}
                    label="自动重试"
                    valuePropName="checked"
                    tooltip="任务失败时自动重试"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* 安全设置 */}
          <TabPane 
            tab={
              <span>
                <SafetyOutlined />
                安全设置
              </span>
            } 
            key="security"
          >
            <Card>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Form.Item
                    name={['securitySettings', 'enableSafeMode']}
                    label="启用安全模式"
                    valuePropName="checked"
                    tooltip="启用安全模式以降低被检测的风险"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['securitySettings', 'enableAntiDetection']}
                    label="启用反检测"
                    valuePropName="checked"
                    tooltip="启用反检测机制"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['securitySettings', 'randomDelay']}
                    label="随机延迟"
                    valuePropName="checked"
                    tooltip="在操作间添加随机延迟"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['securitySettings', 'minDelay']}
                    label="最小延迟（毫秒）"
                    tooltip="随机延迟的最小值"
                  >
                    <InputNumber min={100} max={5000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['securitySettings', 'maxDelay']}
                    label="最大延迟（毫秒）"
                    tooltip="随机延迟的最大值"
                  >
                    <InputNumber min={500} max={10000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* 通知设置 */}
          <TabPane 
            tab={
              <span>
                <BellOutlined />
                通知设置
              </span>
            } 
            key="notification"
          >
            <Card>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Form.Item
                    name={['notificationSettings', 'enableNotifications']}
                    label="启用通知"
                    valuePropName="checked"
                    tooltip="启用系统通知"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['notificationSettings', 'soundEnabled']}
                    label="声音提醒"
                    valuePropName="checked"
                    tooltip="启用声音提醒"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['notificationSettings', 'notifyOnTaskComplete']}
                    label="任务完成通知"
                    valuePropName="checked"
                    tooltip="任务完成时发送通知"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['notificationSettings', 'notifyOnTaskFailed']}
                    label="任务失败通知"
                    valuePropName="checked"
                    tooltip="任务失败时发送通知"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['notificationSettings', 'notifyOnGameClosed']}
                    label="游戏关闭通知"
                    valuePropName="checked"
                    tooltip="检测到游戏关闭时发送通知"
                  >
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>
      </Form>
    </div>
  );
};

export default Settings;