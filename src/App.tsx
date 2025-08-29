import React, { useState, useEffect } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  PlaySquareOutlined,
  SettingOutlined,
  UserOutlined,
  BarChartOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
  RobotOutlined,
  MinusOutlined,
  BorderOutlined,
  CloseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MonitorOutlined
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard/index';
import Tasks from './pages/Tasks/index';
import Accounts from './pages/Accounts/index';
import Statistics from './pages/Statistics/index';
import Settings from './pages/Settings/index';
import TaskInfo from './pages/TaskInfo/index';
import Strategy from './pages/Strategy/index';
import Automation from './pages/Automation';
import GameMonitor from './pages/GameMonitor/index';
// AutoLaunchManager moved to backend API
import './App.css';

const { Header, Sider, Content } = Layout;

type MenuItem = {
  key: string;
  icon: React.ReactNode;
  label: string;
};

const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '仪表板'
  },
  {
    key: 'tasks',
    icon: <PlaySquareOutlined />,
    label: '任务管理'
  },
  {
    key: 'taskinfo',
    icon: <InfoCircleOutlined />,
    label: '任务信息'
  },
  {
    key: 'strategy',
    icon: <TrophyOutlined />,
    label: '攻略管理'
  },
  {
    key: 'automation',
    icon: <RobotOutlined />,
    label: '自动化管理'
  },
  {
    key: 'gamemonitor',
    icon: <MonitorOutlined />,
    label: '游戏监控'
  },
  {
    key: 'accounts',
    icon: <UserOutlined />,
    label: '账号管理'
  },
  {
    key: 'statistics',
    icon: <BarChartOutlined />,
    label: '数据统计'
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '设置'
  }
];

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKey, setSelectedKey] = useState('dashboard');
  // Auto launch manager moved to backend
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 应用启动时的半自动启动逻辑
  useEffect(() => {
    const initializeAutoLaunch = async () => {
      try {
        // 从localStorage获取游戏设置
        let gameSettings = null;
        try {
          const savedSettings = localStorage.getItem('app_settings');
          if (savedSettings) {
            const appSettings = JSON.parse(savedSettings);
            gameSettings = appSettings.gameMonitorSettings;
          }
        } catch (error) {
          console.error('读取游戏设置失败:', error);
          return;
        }
        
        // 严格检查：只有在明确开启自动启动且配置完整时才执行
        if (!gameSettings || 
            !gameSettings.autoLaunchGame || 
            !gameSettings.gamePath || 
            gameSettings.gamePath.trim() === '') {
          console.log('自动启动条件不满足:', {
            hasSettings: !!gameSettings,
            autoLaunchEnabled: gameSettings?.autoLaunchGame,
            hasGamePath: !!gameSettings?.gamePath
          });
          return;
        }
        
        console.log('检测到自动启动已开启，准备执行自动启动...');
        
        // 通过API检查自动启动条件
        const conditionsResponse = await fetch('/api/game/auto-launch/check', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            enabled: gameSettings.autoLaunchGame || false,
            gamePath: gameSettings.gamePath,
            autoLaunch: gameSettings.autoLaunchGame,
            launchDelay: gameSettings.launchDelay,
            enableMonitoring: gameSettings.enableGameMonitoring,
            startMonitoring: gameSettings.enableGameMonitoring || false,
            monitoringInterval: gameSettings.monitorInterval,
            monitoringDelay: gameSettings.launchDelay || 0,
            enableFilterDetection: gameSettings.enableFilterDetection,
            filterDetectionInterval: gameSettings.filterCheckInterval,
            detectInjection: gameSettings.enableInjectionDetection,
            detectDriverFilters: gameSettings.enableDriverFilterDetection,
            terminateOnExit: gameSettings.autoTerminateOnExit,
            retryAttempts: 3,
            retryDelay: 5000
          })
        });
        
        const conditionsData = await conditionsResponse.json();
        
        if (conditionsData.success && conditionsData.data.canLaunch) {
          console.log('执行自动启动逻辑...');
          
          // 通过API执行自动启动
          const launchResponse = await fetch('/api/game/auto-launch/execute', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(gameSettings)
          });
          
          const launchData = await launchResponse.json();
          
          if (launchData.success) {
            console.log('自动启动成功:', launchData.message);
            if (launchData.data.launched) {
              console.log('游戏已启动');
            }
            if (launchData.data.monitoringStarted) {
              console.log('游戏监控已启动');
            }
          } else {
            console.warn('自动启动失败:', launchData.message);
          }
        } else {
          console.log('跳过自动启动:', conditionsData.data?.reason || '条件不满足');
        }
      } catch (error) {
        console.error('自动启动初始化失败:', error);
      }
    };

    // 延迟执行自动启动，确保应用完全加载
    const timer = setTimeout(initializeAutoLaunch, 2000);
    
    return () => {
      clearTimeout(timer);
    };
  }, []);

  // 渲染页面内容
  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return <Dashboard />;
      case 'tasks':
        return <Tasks />;
      case 'taskinfo':
        return <TaskInfo />;
      case 'strategy':
        return <Strategy />;
      case 'automation':
        return <Automation />;
      case 'gamemonitor':
        return <GameMonitor />;
      case 'accounts':
        return <Accounts />;
      case 'statistics':
        return <Statistics />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  // 窗口控制按钮
  const handleWindowControl = async (action: 'minimize' | 'maximize' | 'close') => {
    try {
      switch (action) {
          case 'minimize':
            // await window.electronAPI.app.minimize();
            break;
          case 'maximize':
            // await window.electronAPI.app.maximize();
            break;
          case 'close':
            // await window.electronAPI.app.close();
            break;
        }
    } catch (error) {
      console.error('窗口控制失败:', error);
    }
  };

  return (
    <Layout style={{ height: '100vh' }}>
      {/* 自定义标题栏 */}
      <Header 
        style={{ 
          padding: 0, 
          background: colorBgContainer,
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '48px',
          WebkitAppRegion: 'drag'
        } as any}
      >
        <div style={{ 
          paddingLeft: '16px', 
          fontSize: '16px', 
          fontWeight: 'bold',
          color: '#1890ff'
        }}>
          崩坏：星穹铁道自动化程序
        </div>
        
        <div style={{ 
          display: 'flex', 
          WebkitAppRegion: 'no-drag'
        } as any}>
          <button
            onClick={() => handleWindowControl('minimize')}
            style={{
              border: 'none',
              background: 'transparent',
              padding: '12px 16px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            <MinusOutlined />
          </button>
          <button
            onClick={() => handleWindowControl('maximize')}
            style={{
              border: 'none',
              background: 'transparent',
              padding: '12px 16px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            <BorderOutlined />
          </button>
          <button
            onClick={() => handleWindowControl('close')}
            style={{
              border: 'none',
              background: 'transparent',
              padding: '12px 16px',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#ff4d4f'
            }}
          >
            <CloseOutlined />
          </button>
        </div>
      </Header>

      <Layout>
        {/* 侧边栏 */}
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          style={{
            background: colorBgContainer,
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <div style={{ 
            height: '64px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0'
          }}>
            {!collapsed && (
              <span style={{ fontSize: '16px', fontWeight: 'bold' }}>菜单</span>
            )}
          </div>
          
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ borderRight: 0, background: 'transparent' }}
            items={menuItems}
            onClick={({ key }) => setSelectedKey(key)}
          />
          
          <div style={{ 
            position: 'absolute', 
            bottom: '16px', 
            left: '50%', 
            transform: 'translateX(-50%)'
          }}>
            <button
              onClick={() => setCollapsed(!collapsed)}
              style={{
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '8px'
              }}
            >
              {collapsed ? '»' : '«'}
            </button>
          </div>
        </Sider>

        {/* 主内容区 */}
        <Layout>
          <Content
            style={{
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              overflow: 'auto'
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
