import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, Button, Alert, Descriptions, Progress, Tag, Space, message, Modal, List, Typography } from 'antd';
import { PlayCircleOutlined, StopOutlined, ReloadOutlined, WarningOutlined, CheckCircleOutlined, CloseCircleOutlined, MonitorOutlined, ControlOutlined, SafetyOutlined } from '@ant-design/icons';
const { Title, Text } = Typography;
const GameMonitorPage = () => {
    const [gameStatus, setGameStatus] = useState({
        isRunning: false,
        isMonitoring: false,
        processInfo: null,
        windowInfo: null,
        thirdPartyTools: [],
        lastCheck: new Date(),
        errors: []
    });
    const [monitorStats, setMonitorStats] = useState({
        totalChecks: 0,
        successfulChecks: 0,
        failedChecks: 0,
        averageResponseTime: 0,
        uptime: 0,
        lastError: null
    });
    const [recentEvents, setRecentEvents] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [filterReportVisible, setFilterReportVisible] = useState(false);
    const [filterReport, setFilterReport] = useState(null);
    // 获取游戏状态
    const fetchGameStatus = async () => {
        try {
            const response = await fetch('/api/game/status');
            const data = await response.json();
            if (data.success) {
                setGameStatus(data.data);
            }
        }
        catch (error) {
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
        }
        catch (error) {
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
            }
            else {
                message.error(data.message || '启动监控失败');
            }
        }
        catch (error) {
            message.error('启动监控失败');
        }
        finally {
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
            }
            else {
                message.error(data.message || '停止监控失败');
            }
        }
        catch (error) {
            message.error('停止监控失败');
        }
        finally {
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
            }
            else {
                message.error(data.message || '游戏启动失败');
            }
        }
        catch (error) {
            message.error('游戏启动失败');
        }
        finally {
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
                    }
                    else {
                        message.error(data.message || '终止游戏失败');
                    }
                }
                catch (error) {
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
            }
            else {
                message.error(data.message || '生成滤镜报告失败');
            }
        }
        catch (error) {
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
            return _jsx(Badge, { status: "success", text: "\u8FD0\u884C\u4E2D" });
        }
        else {
            return _jsx(Badge, { status: "error", text: "\u672A\u8FD0\u884C" });
        }
    };
    // 渲染监控状态徽章
    const renderMonitorStatusBadge = () => {
        if (gameStatus.isMonitoring) {
            return _jsx(Badge, { status: "processing", text: "\u76D1\u63A7\u4E2D" });
        }
        else {
            return _jsx(Badge, { status: "default", text: "\u672A\u76D1\u63A7" });
        }
    };
    // 渲染第三方工具警告
    const renderThirdPartyWarnings = () => {
        if (gameStatus.thirdPartyTools.length === 0) {
            return (_jsx(Alert, { message: "\u672A\u68C0\u6D4B\u5230\u7B2C\u4E09\u65B9\u5DE5\u5177", type: "success", icon: _jsx(CheckCircleOutlined, {}), showIcon: true }));
        }
        return (_jsx(Alert, { message: `检测到 ${gameStatus.thirdPartyTools.length} 个第三方工具`, description: _jsx(List, { size: "small", dataSource: gameStatus.thirdPartyTools, renderItem: (tool) => (_jsx(List.Item, { children: _jsxs(Space, { children: [_jsx(Tag, { color: "warning", children: tool.name }), _jsx(Text, { type: "secondary", children: tool.description }), tool.risk === 'high' && _jsx(WarningOutlined, { style: { color: '#ff4d4f' } })] }) })) }), type: "warning", icon: _jsx(WarningOutlined, {}), showIcon: true }));
    };
    return (_jsxs("div", { className: "p-6", children: [_jsx("div", { className: "mb-6", children: _jsxs(Title, { level: 2, children: [_jsx(MonitorOutlined, { className: "mr-2" }), "\u6E38\u620F\u76D1\u63A7\u4E2D\u5FC3"] }) }), _jsx(Card, { title: "\u63A7\u5236\u9762\u677F", className: "mb-4", children: _jsxs(Space, { size: "middle", children: [!gameStatus.isMonitoring ? (_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), onClick: startMonitoring, loading: isLoading, children: "\u542F\u52A8\u76D1\u63A7" })) : (_jsx(Button, { danger: true, icon: _jsx(StopOutlined, {}), onClick: stopMonitoring, loading: isLoading, children: "\u505C\u6B62\u76D1\u63A7" })), !gameStatus.isRunning ? (_jsx(Button, { type: "default", icon: _jsx(ControlOutlined, {}), onClick: launchGame, loading: isLoading, children: "\u542F\u52A8\u6E38\u620F" })) : (_jsx(Button, { danger: true, icon: _jsx(CloseCircleOutlined, {}), onClick: terminateGame, loading: isLoading, children: "\u7EC8\u6B62\u6E38\u620F" })), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                fetchGameStatus();
                                fetchMonitorStats();
                            }, children: "\u5237\u65B0\u72B6\u6001" }), _jsx(Button, { icon: _jsx(SafetyOutlined, {}), onClick: generateFilterReport, children: "\u6EE4\u955C\u68C0\u6D4B\u62A5\u544A" })] }) }), _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Card, { title: "\u6E38\u620F\u72B6\u6001", size: "small", children: _jsxs(Descriptions, { column: 1, size: "small", children: [_jsx(Descriptions.Item, { label: "\u8FD0\u884C\u72B6\u6001", children: renderGameStatusBadge() }), _jsx(Descriptions.Item, { label: "\u76D1\u63A7\u72B6\u6001", children: renderMonitorStatusBadge() }), _jsx(Descriptions.Item, { label: "\u6700\u540E\u68C0\u67E5", children: gameStatus.lastCheck.toLocaleString() }), gameStatus.processInfo && (_jsxs(_Fragment, { children: [_jsx(Descriptions.Item, { label: "\u8FDB\u7A0BID", children: gameStatus.processInfo.pid }), _jsxs(Descriptions.Item, { label: "\u5185\u5B58\u4F7F\u7528", children: [Math.round(gameStatus.processInfo.memoryUsage / 1024 / 1024), " MB"] }), _jsx(Descriptions.Item, { label: "CPU\u4F7F\u7528\u7387", children: _jsx(Progress, { percent: gameStatus.processInfo.cpuUsage, size: "small", status: gameStatus.processInfo.cpuUsage > 80 ? 'exception' : 'normal' }) })] }))] }) }) }), _jsx(Col, { span: 12, children: _jsx(Card, { title: "\u7A97\u53E3\u4FE1\u606F", size: "small", children: gameStatus.windowInfo ? (_jsxs(Descriptions, { column: 1, size: "small", children: [_jsx(Descriptions.Item, { label: "\u7A97\u53E3\u6807\u9898", children: gameStatus.windowInfo.title }), _jsxs(Descriptions.Item, { label: "\u5206\u8FA8\u7387", children: [gameStatus.windowInfo.width, " \u00D7 ", gameStatus.windowInfo.height] }), _jsxs(Descriptions.Item, { label: "\u7A97\u53E3\u72B6\u6001", children: [_jsx(Tag, { color: gameStatus.windowInfo.isVisible ? 'green' : 'red', children: gameStatus.windowInfo.isVisible ? '可见' : '隐藏' }), _jsx(Tag, { color: gameStatus.windowInfo.isFocused ? 'blue' : 'default', children: gameStatus.windowInfo.isFocused ? '焦点' : '非焦点' })] }), _jsxs(Descriptions.Item, { label: "\u4F4D\u7F6E", children: ["(", gameStatus.windowInfo.x, ", ", gameStatus.windowInfo.y, ")"] })] })) : (_jsx(Text, { type: "secondary", children: "\u672A\u68C0\u6D4B\u5230\u6E38\u620F\u7A97\u53E3" })) }) }), _jsx(Col, { span: 12, children: _jsx(Card, { title: "\u76D1\u63A7\u7EDF\u8BA1", size: "small", children: _jsxs(Descriptions, { column: 1, size: "small", children: [_jsx(Descriptions.Item, { label: "\u603B\u68C0\u67E5\u6B21\u6570", children: monitorStats.totalChecks }), _jsx(Descriptions.Item, { label: "\u6210\u529F\u7387", children: _jsx(Progress, { percent: monitorStats.totalChecks > 0 ?
                                                Math.round((monitorStats.successfulChecks / monitorStats.totalChecks) * 100) : 0, size: "small" }) }), _jsxs(Descriptions.Item, { label: "\u5E73\u5747\u54CD\u5E94\u65F6\u95F4", children: [monitorStats.averageResponseTime, " ms"] }), _jsxs(Descriptions.Item, { label: "\u8FD0\u884C\u65F6\u95F4", children: [Math.round(monitorStats.uptime / 1000), " \u79D2"] })] }) }) }), _jsx(Col, { span: 12, children: _jsx(Card, { title: "\u7B2C\u4E09\u65B9\u5DE5\u5177\u68C0\u6D4B", size: "small", children: renderThirdPartyWarnings() }) }), gameStatus.errors.length > 0 && (_jsx(Col, { span: 24, children: _jsx(Card, { title: "\u9519\u8BEF\u4FE1\u606F", size: "small", children: _jsx(List, { size: "small", dataSource: gameStatus.errors, renderItem: (error) => (_jsx(List.Item, { children: _jsx(Alert, { message: error, type: "error", showIcon: true }) })) }) }) }))] }), _jsx(Modal, { title: "\u6EE4\u955C\u68C0\u6D4B\u62A5\u544A", open: filterReportVisible, onCancel: () => setFilterReportVisible(false), footer: [
                    _jsx(Button, { onClick: () => setFilterReportVisible(false), children: "\u5173\u95ED" }, "close")
                ], width: 800, children: filterReport && (_jsx("div", { children: _jsxs(Descriptions, { column: 2, bordered: true, size: "small", children: [_jsx(Descriptions.Item, { label: "\u68C0\u6D4B\u65F6\u95F4", children: new Date(filterReport.timestamp).toLocaleString() }), _jsx(Descriptions.Item, { label: "\u68C0\u6D4B\u7ED3\u679C", children: _jsx(Tag, { color: filterReport.hasFilters ? 'red' : 'green', children: filterReport.hasFilters ? '发现滤镜' : '无滤镜' }) }), _jsx(Descriptions.Item, { label: "\u8FDB\u7A0B\u68C0\u6D4B", span: 2, children: filterReport.processDetection.length > 0 ? (_jsx(List, { size: "small", dataSource: filterReport.processDetection, renderItem: (item) => (_jsxs(List.Item, { children: [_jsx(Tag, { color: "orange", children: item.name }), _jsx(Text, { children: item.description })] })) })) : (_jsx(Text, { type: "secondary", children: "\u672A\u53D1\u73B0\u53EF\u7591\u8FDB\u7A0B" })) }), _jsx(Descriptions.Item, { label: "\u6CE8\u5165\u68C0\u6D4B", span: 2, children: filterReport.injectionDetection.length > 0 ? (_jsx(List, { size: "small", dataSource: filterReport.injectionDetection, renderItem: (item) => (_jsxs(List.Item, { children: [_jsx(Tag, { color: "red", children: item.dll }), _jsx(Text, { children: item.description })] })) })) : (_jsx(Text, { type: "secondary", children: "\u672A\u53D1\u73B0\u8FDB\u7A0B\u6CE8\u5165" })) })] }) })) })] }));
};
export default GameMonitorPage;
