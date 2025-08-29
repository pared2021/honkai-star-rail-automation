import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 仪表板页面
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Alert, Space, Tag, message } from 'antd';
import { PlayCircleOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons';
import { GameDetector } from '../../modules/GameDetector.js';
import { TaskExecutor } from '../../modules/TaskExecutor.js';
import { TaskType } from '../../types/index.js';
const Dashboard = () => {
    const [systemStats, setSystemStats] = useState(null);
    const [gameStatus, setGameStatus] = useState({ isRunning: false, isActive: false });
    const [runningTasks, setRunningTasks] = useState([]);
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
        }
        catch (error) {
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
        }
        catch (error) {
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
    const stopTask = async (taskId) => {
        try {
            taskExecutor.stopAllTasks();
            message.success('任务已停止');
            await fetchRunningTasks();
        }
        catch (error) {
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
                status: 'pending',
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
        }
        catch (error) {
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
            }
            catch (error) {
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
    const getTaskStatusColor = (status) => {
        switch (status) {
            case 'running': return 'processing';
            case 'completed': return 'success';
            case 'failed': return 'error';
            case 'cancelled': return 'default';
            default: return 'default';
        }
    };
    // 获取任务类型显示名称
    const getTaskTypeName = (taskType) => {
        switch (taskType) {
            case 'daily': return '日常任务';
            case 'main': return '主线任务';
            case 'side': return '支线任务';
            case 'custom': return '自定义任务';
            default: return taskType;
        }
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: [_jsx("h1", { style: { margin: 0 }, children: "\u4EEA\u8868\u677F" }), _jsxs(Space, { children: [_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), onClick: startDailyTask, disabled: !gameStatus.isRunning || runningTasks.length > 0, children: "\u542F\u52A8\u6BCF\u65E5\u59D4\u6258" }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: refreshData, loading: loading, children: "\u5237\u65B0" })] })] }), _jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u6E38\u620F\u72B6\u6001", value: gameStatus.isRunning ? '运行中' : '未运行', valueStyle: {
                                    color: gameStatus.isRunning ? '#3f8600' : '#cf1322'
                                } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u8FD0\u884C\u4EFB\u52A1\u6570", value: runningTasks.length, valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u4ECA\u65E5\u5B8C\u6210\u4EFB\u52A1", value: systemStats?.completedTasks || 0, valueStyle: { color: '#52c41a' } }) }) })] }), !gameStatus.isRunning && (_jsx(Alert, { message: "\u6E38\u620F\u672A\u8FD0\u884C", description: "\u8BF7\u5148\u542F\u52A8\u300A\u5D29\u574F\uFF1A\u661F\u7A79\u94C1\u9053\u300B\u6E38\u620F\uFF0C\u7136\u540E\u5237\u65B0\u72B6\u6001\u3002", type: "warning", showIcon: true, style: { marginBottom: '24px' } })), gameStatus.isRunning && gameStatus.windowInfo && (_jsx(Card, { title: "\u6E38\u620F\u7A97\u53E3\u4FE1\u606F", style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 6, children: _jsx(Statistic, { title: "\u7A97\u53E3\u6807\u9898", value: gameStatus.windowInfo?.title || '未知' }) }), _jsx(Col, { span: 6, children: _jsx(Statistic, { title: "\u7A97\u53E3\u5927\u5C0F", value: `${gameStatus.windowInfo?.width || 0}x${gameStatus.windowInfo?.height || 0}` }) }), _jsx(Col, { span: 6, children: _jsx(Statistic, { title: "\u7A97\u53E3\u4F4D\u7F6E", value: `(${gameStatus.windowInfo?.x || 0}, ${gameStatus.windowInfo?.y || 0})` }) }), _jsx(Col, { span: 6, children: _jsx(Statistic, { title: "\u5F53\u524D\u573A\u666F", value: gameStatus.currentScene || '未知' }) })] }) })), _jsx(Card, { title: "\u8FD0\u884C\u4E2D\u7684\u4EFB\u52A1", children: runningTasks.length === 0 ? (_jsx("div", { style: { textAlign: 'center', padding: '40px', color: '#999' }, children: "\u6682\u65E0\u8FD0\u884C\u4E2D\u7684\u4EFB\u52A1" })) : (_jsx("div", { children: runningTasks.map(task => (_jsx(Card, { size: "small", style: { marginBottom: '12px' }, extra: _jsxs(Space, { children: [_jsx(Tag, { color: getTaskStatusColor(task.status), children: task.status }), _jsx(Button, { size: "small", icon: _jsx(StopOutlined, {}), onClick: () => stopTask(task.id), danger: true, children: "\u505C\u6B62" })] }), children: _jsx("div", { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: _jsxs("div", { children: [_jsx("strong", { children: getTaskTypeName(task.taskType) }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '4px' }, children: ["\u4EFB\u52A1ID: ", task.id] }), task.startTime && (_jsxs("div", { style: { fontSize: '12px', color: '#666' }, children: ["\u5F00\u59CB\u65F6\u95F4: ", new Date(task.startTime).toLocaleString()] }))] }) }) }, task.id))) })) })] }));
};
export default Dashboard;
