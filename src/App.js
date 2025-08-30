import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Layout, Menu, theme } from 'antd';
import { DashboardOutlined, PlaySquareOutlined, SettingOutlined, UserOutlined, BarChartOutlined, InfoCircleOutlined, TrophyOutlined, RobotOutlined, MinusOutlined, BorderOutlined, CloseOutlined, MonitorOutlined } from '@ant-design/icons';
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
const menuItems = [
    {
        key: 'dashboard',
        icon: _jsx(DashboardOutlined, {}),
        label: '仪表板'
    },
    {
        key: 'tasks',
        icon: _jsx(PlaySquareOutlined, {}),
        label: '任务管理'
    },
    {
        key: 'taskinfo',
        icon: _jsx(InfoCircleOutlined, {}),
        label: '任务信息'
    },
    {
        key: 'strategy',
        icon: _jsx(TrophyOutlined, {}),
        label: '攻略管理'
    },
    {
        key: 'automation',
        icon: _jsx(RobotOutlined, {}),
        label: '自动化管理'
    },
    {
        key: 'gamemonitor',
        icon: _jsx(MonitorOutlined, {}),
        label: '游戏监控'
    },
    {
        key: 'accounts',
        icon: _jsx(UserOutlined, {}),
        label: '账号管理'
    },
    {
        key: 'statistics',
        icon: _jsx(BarChartOutlined, {}),
        label: '数据统计'
    },
    {
        key: 'settings',
        icon: _jsx(SettingOutlined, {}),
        label: '设置'
    }
];
function App() {
    const [collapsed, setCollapsed] = useState(false);
    const [selectedKey, setSelectedKey] = useState('dashboard');
    // Auto launch manager moved to backend
    const { token: { colorBgContainer, borderRadiusLG }, } = theme.useToken();
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
                }
                catch (error) {
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
                    }
                    else {
                        console.warn('自动启动失败:', launchData.message);
                    }
                }
                else {
                    console.log('跳过自动启动:', conditionsData.data?.reason || '条件不满足');
                }
            }
            catch (error) {
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
                return _jsx(Dashboard, {});
            case 'tasks':
                return _jsx(Tasks, {});
            case 'taskinfo':
                return _jsx(TaskInfo, {});
            case 'strategy':
                return _jsx(Strategy, {});
            case 'automation':
                return _jsx(Automation, {});
            case 'gamemonitor':
                return _jsx(GameMonitor, {});
            case 'accounts':
                return _jsx(Accounts, {});
            case 'statistics':
                return _jsx(Statistics, {});
            case 'settings':
                return _jsx(Settings, {});
            default:
                return _jsx(Dashboard, {});
        }
    };
    // 窗口控制按钮
    const handleWindowControl = async (action) => {
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
        }
        catch (error) {
            console.error('窗口控制失败:', error);
        }
    };
    return (_jsxs(Layout, { style: { height: '100vh' }, children: [_jsxs(Header, { style: {
                    padding: 0,
                    background: colorBgContainer,
                    borderBottom: '1px solid #f0f0f0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    height: '48px',
                    WebkitAppRegion: 'drag'
                }, children: [_jsx("div", { style: {
                            paddingLeft: '16px',
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#1890ff'
                        }, children: "\u5D29\u574F\uFF1A\u661F\u7A79\u94C1\u9053\u81EA\u52A8\u5316\u7A0B\u5E8F" }), _jsxs("div", { style: {
                            display: 'flex',
                            WebkitAppRegion: 'no-drag'
                        }, children: [_jsx("button", { onClick: () => handleWindowControl('minimize'), style: {
                                    border: 'none',
                                    background: 'transparent',
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }, children: _jsx(MinusOutlined, {}) }), _jsx("button", { onClick: () => handleWindowControl('maximize'), style: {
                                    border: 'none',
                                    background: 'transparent',
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }, children: _jsx(BorderOutlined, {}) }), _jsx("button", { onClick: () => handleWindowControl('close'), style: {
                                    border: 'none',
                                    background: 'transparent',
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    color: '#ff4d4f'
                                }, children: _jsx(CloseOutlined, {}) })] })] }), _jsxs(Layout, { children: [_jsxs(Sider, { trigger: null, collapsible: true, collapsed: collapsed, style: {
                            background: colorBgContainer,
                            borderRight: '1px solid #f0f0f0'
                        }, children: [_jsx("div", { style: {
                                    height: '64px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    borderBottom: '1px solid #f0f0f0'
                                }, children: !collapsed && (_jsx("span", { style: { fontSize: '16px', fontWeight: 'bold' }, children: "\u83DC\u5355" })) }), _jsx(Menu, { mode: "inline", selectedKeys: [selectedKey], style: { borderRight: 0, background: 'transparent' }, items: menuItems, onClick: ({ key }) => setSelectedKey(key) }), _jsx("div", { style: {
                                    position: 'absolute',
                                    bottom: '16px',
                                    left: '50%',
                                    transform: 'translateX(-50%)'
                                }, children: _jsx("button", { onClick: () => setCollapsed(!collapsed), style: {
                                        border: 'none',
                                        background: 'transparent',
                                        cursor: 'pointer',
                                        fontSize: '16px',
                                        padding: '8px'
                                    }, children: collapsed ? '»' : '«' }) })] }), _jsx(Layout, { children: _jsx(Content, { style: {
                                margin: 0,
                                minHeight: 280,
                                background: colorBgContainer,
                                borderRadius: borderRadiusLG,
                                overflow: 'auto'
                            }, children: renderContent() }) })] })] }));
}
export default App;
