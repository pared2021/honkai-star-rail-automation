import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card, Switch, Button, Form, InputNumber, Select, Slider, Row, Col, Statistic, Alert, List, Tag, Space, Divider, Modal, message } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, SettingOutlined, ClearOutlined, InfoCircleOutlined, TrophyOutlined, RobotOutlined } from '@ant-design/icons';
import { useGameStatus } from '../../hooks/useGameStatus';
import GameStatusDialog from '../../components/GameStatusDialog';
const { Option } = Select;
const Automation = () => {
    const [form] = Form.useForm();
    const [config, setConfig] = useState(null);
    const [status, setStatus] = useState(null);
    const [statistics, setStatistics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [configModalVisible, setConfigModalVisible] = useState(false);
    // 游戏状态管理
    const { gameStatus, loading: gameStatusLoading, showGameDialog, setShowGameDialog, checkGameStatus, launchGame, checkAndPromptIfNeeded } = useGameStatus();
    // 获取自动化配置
    const fetchConfig = async () => {
        try {
            const response = await fetch('/api/tasks/automation/config');
            const data = await response.json();
            if (data.success) {
                setConfig(data.data);
                form.setFieldsValue(data.data);
            }
        }
        catch (error) {
            console.error('获取自动化配置失败:', error);
            message.error('获取自动化配置失败');
        }
    };
    // 获取自动化状态
    const fetchStatus = async () => {
        try {
            const response = await fetch('/api/tasks/automation/status');
            const data = await response.json();
            if (data.success) {
                setStatus(data.data);
            }
        }
        catch (error) {
            console.error('获取自动化状态失败:', error);
        }
    };
    // 获取统计信息
    const fetchStatistics = async () => {
        try {
            const response = await fetch('/api/tasks/automation/statistics');
            const data = await response.json();
            if (data.success) {
                setStatistics(data.data);
            }
        }
        catch (error) {
            console.error('获取统计信息失败:', error);
        }
    };
    // 处理启动自动化按钮点击
    const handleStartAutomationClick = async () => {
        // 检查游戏状态，如果游戏未启动则提示用户
        const canProceed = await checkAndPromptIfNeeded();
        if (canProceed) {
            await startAutomation();
        }
    };
    // 启动自动化
    const startAutomation = async () => {
        setLoading(true);
        try {
            // 再次检查游戏状态
            const isGameRunning = await checkGameStatus();
            if (!isGameRunning) {
                message.error('游戏未启动，无法启动自动化管理');
                setLoading(false);
                return;
            }
            const response = await fetch('/api/tasks/automation/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ config })
            });
            const data = await response.json();
            if (data.success) {
                message.success('自动化管理启动成功');
                await fetchStatus();
            }
            else {
                message.error(data.message || '启动失败');
            }
        }
        catch (error) {
            console.error('启动自动化失败:', error);
            message.error('启动自动化失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 停止自动化
    const stopAutomation = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/tasks/automation/stop', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                message.success('自动化管理停止成功');
                await fetchStatus();
            }
            else {
                message.error(data.message || '停止失败');
            }
        }
        catch (error) {
            console.error('停止自动化失败:', error);
            message.error('停止自动化失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 手动触发任务信息收集
    const triggerCollect = async () => {
        try {
            const response = await fetch('/api/tasks/automation/trigger/collect', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                message.success('任务信息收集已触发');
                await fetchStatus();
            }
            else {
                message.error(data.message || '触发失败');
            }
        }
        catch (error) {
            console.error('触发收集失败:', error);
            message.error('触发收集失败');
        }
    };
    // 手动触发攻略分析
    const triggerAnalyze = async () => {
        try {
            const response = await fetch('/api/tasks/automation/trigger/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            const data = await response.json();
            if (data.success) {
                message.success('攻略分析已触发');
                await fetchStatus();
            }
            else {
                message.error(data.message || '触发失败');
            }
        }
        catch (error) {
            console.error('触发分析失败:', error);
            message.error('触发分析失败');
        }
    };
    // 清理错误日志
    const clearErrors = async () => {
        try {
            const response = await fetch('/api/tasks/automation/clear-errors', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                message.success('错误日志已清理');
                await fetchStatus();
            }
            else {
                message.error(data.message || '清理失败');
            }
        }
        catch (error) {
            console.error('清理错误失败:', error);
            message.error('清理错误失败');
        }
    };
    // 保存配置
    const saveConfig = async (values) => {
        try {
            const response = await fetch('/api/tasks/automation/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(values)
            });
            const data = await response.json();
            if (data.success) {
                message.success('配置保存成功');
                setConfig({ ...config, ...values });
                setConfigModalVisible(false);
            }
            else {
                message.error(data.message || '保存失败');
            }
        }
        catch (error) {
            console.error('保存配置失败:', error);
            message.error('保存配置失败');
        }
    };
    useEffect(() => {
        fetchConfig();
        fetchStatus();
        fetchStatistics();
        // 定时刷新状态
        const interval = setInterval(() => {
            fetchStatus();
            fetchStatistics();
        }, 5000);
        return () => clearInterval(interval);
    }, []);
    const getStatusColor = (isRunning) => {
        return isRunning ? '#52c41a' : '#d9d9d9';
    };
    const getTaskTypeLabel = (type) => {
        const labels = {
            main: '主线任务',
            side: '支线任务',
            daily: '日常任务',
            event: '活动任务',
            all: '所有任务'
        };
        return labels[type] || type;
    };
    return (_jsxs("div", { className: "p-6", children: [_jsxs("div", { className: "mb-6", children: [_jsx("h1", { className: "text-2xl font-bold mb-2", children: "\u81EA\u52A8\u5316\u7BA1\u7406" }), _jsx("p", { className: "text-gray-600", children: "\u914D\u7F6E\u548C\u63A7\u5236\u4EFB\u52A1\u81EA\u52A8\u5316\u6267\u884C\uFF0C\u51CF\u5C11\u624B\u52A8\u64CD\u4F5C" })] }), _jsxs(Row, { gutter: [16, 16], className: "mb-6", children: [_jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u8FD0\u884C\u72B6\u6001", value: status?.isRunning ? '运行中' : '已停止', valueStyle: { color: getStatusColor(status?.isRunning || false) }, prefix: _jsx(RobotOutlined, {}) }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u5DF2\u5B8C\u6210\u4EFB\u52A1", value: statistics?.totalTasksCompleted || 0, prefix: _jsx(TrophyOutlined, {}) }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u6210\u529F\u7387", value: ((statistics?.successRate || 0) * 100).toFixed(1), suffix: "%", valueStyle: {
                                    color: (statistics?.successRate || 0) > 0.8 ? '#3f8600' : '#cf1322'
                                } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u9519\u8BEF\u6570\u91CF", value: statistics?.errorCount || 0, valueStyle: { color: (statistics?.errorCount || 0) > 0 ? '#cf1322' : '#3f8600' } }) }) })] }), _jsx(Card, { title: "\u63A7\u5236\u9762\u677F", className: "mb-6", children: _jsxs(Space, { size: "large", children: [_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), onClick: handleStartAutomationClick, loading: loading || gameStatusLoading, disabled: status?.isRunning, children: "\u542F\u52A8\u81EA\u52A8\u5316" }), _jsx(Button, { icon: _jsx(PauseCircleOutlined, {}), onClick: stopAutomation, loading: loading, disabled: !status?.isRunning, children: "\u505C\u6B62\u81EA\u52A8\u5316" }), _jsx(Button, { icon: _jsx(SettingOutlined, {}), onClick: () => setConfigModalVisible(true), children: "\u914D\u7F6E\u8BBE\u7F6E" }), _jsx(Button, { icon: _jsx(InfoCircleOutlined, {}), onClick: triggerCollect, disabled: status?.currentTasks.includes('任务信息收集'), children: "\u6536\u96C6\u4EFB\u52A1\u4FE1\u606F" }), _jsx(Button, { icon: _jsx(TrophyOutlined, {}), onClick: triggerAnalyze, disabled: status?.currentTasks.includes('攻略分析'), children: "\u5206\u6790\u653B\u7565" }), _jsx(Button, { icon: _jsx(ClearOutlined, {}), onClick: clearErrors, disabled: !status?.errors.length, children: "\u6E05\u7406\u9519\u8BEF" })] }) }), _jsxs(Row, { gutter: [16, 16], className: "mb-6", children: [_jsx(Col, { xs: 24, md: 12, children: _jsx(Card, { title: "\u5F53\u524D\u4EFB\u52A1", size: "small", children: status?.currentTasks.length ? (_jsx(List, { size: "small", dataSource: status.currentTasks, renderItem: (task) => (_jsx(List.Item, { children: _jsx(Tag, { color: "processing", children: task }) })) })) : (_jsx("div", { className: "text-gray-500 text-center py-4", children: "\u6682\u65E0\u8FD0\u884C\u4E2D\u7684\u4EFB\u52A1" })) }) }), _jsx(Col, { xs: 24, md: 12, children: _jsx(Card, { title: "\u9519\u8BEF\u65E5\u5FD7", size: "small", children: status?.errors.length ? (_jsx(List, { size: "small", dataSource: status.errors.slice(-5), renderItem: (error) => (_jsx(List.Item, { children: _jsx(Alert, { message: error, type: "error", showIcon: true, className: "w-full" }) })) })) : (_jsx("div", { className: "text-gray-500 text-center py-4", children: "\u6682\u65E0\u9519\u8BEF" })) }) })] }), config && (_jsx(Card, { title: "\u5F53\u524D\u914D\u7F6E", size: "small", children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u4EFB\u52A1\u7C7B\u578B\uFF1A" }), _jsx(Tag, { color: "blue", children: getTaskTypeLabel(config.taskType) })] }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u6267\u884C\u95F4\u9694\uFF1A" }), _jsxs("span", { children: [config.intervalMinutes, " \u5206\u949F"] })] }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u6700\u4F4E\u6210\u529F\u7387\uFF1A" }), _jsxs("span", { children: [(config.minSuccessRate * 100).toFixed(0), "%"] })] }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u81EA\u52A8\u6536\u96C6\u4FE1\u606F\uFF1A" }), _jsx(Tag, { color: config.autoCollectInfo ? 'green' : 'red', children: config.autoCollectInfo ? '开启' : '关闭' })] }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u81EA\u52A8\u5206\u6790\u653B\u7565\uFF1A" }), _jsx(Tag, { color: config.autoAnalyzeStrategy ? 'green' : 'red', children: config.autoAnalyzeStrategy ? '开启' : '关闭' })] }) }), _jsx(Col, { xs: 24, sm: 12, md: 8, children: _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "font-medium", children: "\u81EA\u52A8\u6267\u884C\u4EFB\u52A1\uFF1A" }), _jsx(Tag, { color: config.autoExecuteTasks ? 'green' : 'red', children: config.autoExecuteTasks ? '开启' : '关闭' })] }) })] }) })), _jsx(Modal, { title: "\u81EA\u52A8\u5316\u914D\u7F6E", open: configModalVisible, onCancel: () => setConfigModalVisible(false), onOk: () => form.submit(), width: 800, okText: "\u4FDD\u5B58", cancelText: "\u53D6\u6D88", children: _jsxs(Form, { form: form, layout: "vertical", onFinish: saveConfig, initialValues: config, children: [_jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u4EFB\u52A1\u7C7B\u578B", name: "taskType", rules: [{ required: true, message: '请选择任务类型' }], children: _jsxs(Select, { children: [_jsx(Option, { value: "all", children: "\u6240\u6709\u4EFB\u52A1" }), _jsx(Option, { value: "main", children: "\u4E3B\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "side", children: "\u652F\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "daily", children: "\u65E5\u5E38\u4EFB\u52A1" }), _jsx(Option, { value: "event", children: "\u6D3B\u52A8\u4EFB\u52A1" })] }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u6267\u884C\u95F4\u9694\uFF08\u5206\u949F\uFF09", name: "intervalMinutes", rules: [{ required: true, message: '请输入执行间隔' }], children: _jsx(InputNumber, { min: 5, max: 1440, className: "w-full" }) }) })] }), _jsx(Divider, { children: "\u81EA\u52A8\u5316\u529F\u80FD" }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u81EA\u52A8\u6536\u96C6\u4EFB\u52A1\u4FE1\u606F", name: "autoCollectInfo", valuePropName: "checked", children: _jsx(Switch, {}) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u81EA\u52A8\u5206\u6790\u653B\u7565", name: "autoAnalyzeStrategy", valuePropName: "checked", children: _jsx(Switch, {}) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u81EA\u52A8\u9009\u62E9\u6700\u4F18\u653B\u7565", name: "autoSelectBestStrategy", valuePropName: "checked", children: _jsx(Switch, {}) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u81EA\u52A8\u6267\u884C\u4EFB\u52A1", name: "autoExecuteTasks", valuePropName: "checked", children: _jsx(Switch, {}) }) })] }), _jsx(Divider, { children: "\u6267\u884C\u53C2\u6570" }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u6700\u4F4E\u6210\u529F\u7387", name: "minSuccessRate", children: _jsx(Slider, { min: 0.5, max: 1, step: 0.05, marks: {
                                                0.5: '50%',
                                                0.8: '80%',
                                                1: '100%'
                                            }, tipFormatter: (value) => `${(value * 100).toFixed(0)}%` }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { label: "\u6700\u5927\u91CD\u8BD5\u6B21\u6570", name: "maxRetryCount", children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) })] }), _jsx(Divider, { children: "\u8D44\u6E90\u7BA1\u7406" }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u6700\u5927\u5E76\u53D1\u4EFB\u52A1\u6570", name: ['resourceManagement', 'maxConcurrentTasks'], children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) }), _jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u4F53\u529B\u9608\u503C", name: ['resourceManagement', 'energyThreshold'], children: _jsx(InputNumber, { min: 0, max: 100, className: "w-full" }) }) }), _jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u81EA\u52A8\u6062\u590D\u4F53\u529B", name: ['resourceManagement', 'autoRestoreEnergy'], valuePropName: "checked", children: _jsx(Switch, {}) }) })] }), _jsx(Divider, { children: "\u4EFB\u52A1\u4F18\u5148\u7EA7" }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 6, children: _jsx(Form.Item, { label: "\u4E3B\u7EBF\u4EFB\u52A1", name: ['prioritySettings', 'main'], children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) }), _jsx(Col, { span: 6, children: _jsx(Form.Item, { label: "\u652F\u7EBF\u4EFB\u52A1", name: ['prioritySettings', 'side'], children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) }), _jsx(Col, { span: 6, children: _jsx(Form.Item, { label: "\u65E5\u5E38\u4EFB\u52A1", name: ['prioritySettings', 'daily'], children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) }), _jsx(Col, { span: 6, children: _jsx(Form.Item, { label: "\u6D3B\u52A8\u4EFB\u52A1", name: ['prioritySettings', 'event'], children: _jsx(InputNumber, { min: 1, max: 10, className: "w-full" }) }) })] }), _jsx(Divider, { children: "\u901A\u77E5\u8BBE\u7F6E" }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u4EFB\u52A1\u5B8C\u6210\u901A\u77E5", name: ['notificationSettings', 'onTaskComplete'], valuePropName: "checked", children: _jsx(Switch, {}) }) }), _jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u9519\u8BEF\u901A\u77E5", name: ['notificationSettings', 'onError'], valuePropName: "checked", children: _jsx(Switch, {}) }) }), _jsx(Col, { span: 8, children: _jsx(Form.Item, { label: "\u6700\u4F18\u653B\u7565\u53D1\u73B0\u901A\u77E5", name: ['notificationSettings', 'onOptimalStrategyFound'], valuePropName: "checked", children: _jsx(Switch, {}) }) })] })] }) }), _jsx(GameStatusDialog, { visible: showGameDialog, onClose: () => setShowGameDialog(false), onLaunch: launchGame, onCancel: () => setShowGameDialog(false), title: "\u6E38\u620F\u672A\u542F\u52A8", message: "\u68C0\u6D4B\u5230\u6E38\u620F\u672A\u542F\u52A8\uFF0C\u542F\u52A8\u81EA\u52A8\u5316\u7BA1\u7406\u9700\u8981\u6E38\u620F\u5904\u4E8E\u8FD0\u884C\u72B6\u6001\u3002\u662F\u5426\u73B0\u5728\u542F\u52A8\u6E38\u620F\uFF1F" })] }));
};
export default Automation;
