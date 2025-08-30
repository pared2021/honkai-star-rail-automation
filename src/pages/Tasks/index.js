import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
// 任务管理页面
import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Select, Switch, Space, message, Tag, Tabs, Row, Col, InputNumber } from 'antd';
import { PlusOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';
import { useGameStatus } from '../../hooks/useGameStatus';
import GameStatusDialog from '../../components/GameStatusDialog';
const { TabPane } = Tabs;
const { Option } = Select;
const Tasks = () => {
    const [runningTasks, setRunningTasks] = useState([]);
    const [taskHistory, setTaskHistory] = useState([]);
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [startTaskModalVisible, setStartTaskModalVisible] = useState(false);
    const [selectedTaskType, setSelectedTaskType] = useState('daily');
    const [form] = Form.useForm();
    // 游戏状态管理
    const { gameStatus, loading: gameStatusLoading, checkGameStatus, launchGame, showGameDialog, setShowGameDialog, checkAndPromptIfNeeded } = useGameStatus();
    // 获取运行中的任务
    const fetchRunningTasks = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/tasks/running');
            const data = await response.json();
            if (data.success) {
                setRunningTasks(data.data);
            }
        }
        catch (error) {
            console.error('获取运行任务失败:', error);
        }
    };
    // 获取任务历史
    const fetchTaskHistory = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/tasks/history');
            const data = await response.json();
            if (data.success) {
                setTaskHistory(data.data);
            }
        }
        catch (error) {
            console.error('获取任务历史失败:', error);
        }
    };
    // 获取账号列表
    const fetchAccounts = async () => {
        try {
            const response = { success: true, data: [] }; // await window.electronAPI.account.list();
            if (response.success) {
                setAccounts(response.data);
            }
        }
        catch (error) {
            console.error('获取账号列表失败:', error);
        }
    };
    // 处理启动任务按钮点击
    const handleStartTaskClick = async () => {
        // 检查游戏状态，如果游戏未启动则显示提示对话框
        const canProceed = await checkAndPromptIfNeeded('启动任务');
        if (canProceed) {
            setStartTaskModalVisible(true);
        }
    };
    // 启动任务
    const startTask = async (values) => {
        try {
            setLoading(true);
            // 再次检查游戏状态，确保游戏正在运行
            const status = await checkGameStatus();
            if (!status.isRunning) {
                message.error('游戏未启动，无法执行任务');
                return;
            }
            const response = { success: true, data: { taskId: 'mock-task-id' } }; // await window.electronAPI.task.start({
            // taskType: selectedTaskType,
            // accountId: values.accountId,
            // config: values
            // });
            if (response.success) {
                message.success('任务启动成功');
                setStartTaskModalVisible(false);
                form.resetFields();
                await fetchRunningTasks();
            }
            else {
                message.error('任务启动失败');
            }
        }
        catch (error) {
            message.error('任务启动失败');
            console.error('启动任务失败:', error);
        }
        finally {
            setLoading(false);
        }
    };
    // 控制任务
    const controlTask = async (taskId, action) => {
        try {
            const response = { success: true }; // await window.electronAPI.task.control({ taskId, action });
            if (response.success) {
                message.success(`任务${action === 'stop' ? '停止' : action === 'pause' ? '暂停' : '恢复'}成功`);
                await fetchRunningTasks();
            }
            else {
                message.error('操作失败');
            }
        }
        catch (error) {
            message.error('操作失败');
            console.error('控制任务失败:', error);
        }
    };
    // 组件挂载时获取数据
    useEffect(() => {
        fetchRunningTasks();
        fetchTaskHistory();
        fetchAccounts();
        // 定时刷新运行中的任务
        const interval = setInterval(fetchRunningTasks, 3000);
        return () => clearInterval(interval);
    }, []);
    // 获取任务状态颜色
    const getTaskStatusColor = (status) => {
        switch (status) {
            case 'running': return 'processing';
            case 'completed': return 'success';
            case 'failed': return 'error';
            case 'cancelled': return 'default';
            case 'pending': return 'warning';
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
    // 运行中任务表格列
    const runningTaskColumns = [
        {
            title: '任务类型',
            dataIndex: 'taskType',
            key: 'taskType',
            render: (taskType) => getTaskTypeName(taskType)
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status) => (_jsx(Tag, { color: getTaskStatusColor(status), children: status }))
        },
        {
            title: '开始时间',
            dataIndex: 'startTime',
            key: 'startTime',
            render: (time) => time ? new Date(time).toLocaleString() : '-'
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (_jsxs(Space, { children: [_jsx(Button, { size: "small", icon: _jsx(PauseCircleOutlined, {}), onClick: () => controlTask(record.id, 'pause'), children: "\u6682\u505C" }), _jsx(Button, { size: "small", icon: _jsx(StopOutlined, {}), danger: true, onClick: () => controlTask(record.id, 'stop'), children: "\u505C\u6B62" })] }))
        }
    ];
    // 历史任务表格列
    const historyTaskColumns = [
        {
            title: '任务类型',
            dataIndex: 'taskType',
            key: 'taskType',
            render: (taskType) => getTaskTypeName(taskType)
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status) => (_jsx(Tag, { color: getTaskStatusColor(status), children: status }))
        },
        {
            title: '开始时间',
            dataIndex: 'startTime',
            key: 'startTime',
            render: (time) => time ? new Date(time).toLocaleString() : '-'
        },
        {
            title: '结束时间',
            dataIndex: 'endTime',
            key: 'endTime',
            render: (time) => time ? new Date(time).toLocaleString() : '-'
        },
        {
            title: '耗时',
            key: 'duration',
            render: (_, record) => {
                if (record.startTime && record.endTime) {
                    const duration = new Date(record.endTime).getTime() - new Date(record.startTime).getTime();
                    return `${Math.round(duration / 1000)}秒`;
                }
                return '-';
            }
        }
    ];
    // 渲染任务配置表单
    const renderTaskConfigForm = () => {
        switch (selectedTaskType) {
            case 'daily':
                return (_jsxs(_Fragment, { children: [_jsx(Form.Item, { name: "enableStamina", label: "\u542F\u7528\u4F53\u529B\u6D88\u8017", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "enableCommission", label: "\u542F\u7528\u59D4\u6258\u4EFB\u52A1", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "staminaTarget", label: "\u4F53\u529B\u76EE\u6807\u503C", children: _jsx(InputNumber, { min: 0, max: 240 }) }), _jsx(Form.Item, { name: "autoCollectRewards", label: "\u81EA\u52A8\u6536\u96C6\u5956\u52B1", valuePropName: "checked", children: _jsx(Switch, {}) })] }));
            case 'main':
                return (_jsxs(_Fragment, { children: [_jsx(Form.Item, { name: "autoDialog", label: "\u81EA\u52A8\u5BF9\u8BDD", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "autoBattle", label: "\u81EA\u52A8\u6218\u6597", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "skipCutscene", label: "\u8DF3\u8FC7\u8FC7\u573A\u52A8\u753B", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "battleStrategy", label: "\u6218\u6597\u7B56\u7565", children: _jsxs(Select, { children: [_jsx(Option, { value: "auto", children: "\u81EA\u52A8" }), _jsx(Option, { value: "conservative", children: "\u4FDD\u5B88" }), _jsx(Option, { value: "aggressive", children: "\u6FC0\u8FDB" })] }) })] }));
            default:
                return null;
        }
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: [_jsx("h1", { style: { margin: 0 }, children: "\u4EFB\u52A1\u7BA1\u7406" }), _jsx(Button, { type: "primary", icon: _jsx(PlusOutlined, {}), onClick: handleStartTaskClick, loading: gameStatusLoading, children: "\u542F\u52A8\u4EFB\u52A1" })] }), _jsxs(Tabs, { defaultActiveKey: "running", children: [_jsx(TabPane, { tab: "\u8FD0\u884C\u4E2D\u4EFB\u52A1", children: _jsx(Card, { children: _jsx(Table, { columns: runningTaskColumns, dataSource: runningTasks, rowKey: "id", pagination: false, locale: { emptyText: '暂无运行中的任务' } }) }) }, "running"), _jsx(TabPane, { tab: "\u4EFB\u52A1\u5386\u53F2", children: _jsx(Card, { children: _jsx(Table, { columns: historyTaskColumns, dataSource: taskHistory, rowKey: "id", pagination: { pageSize: 10 }, locale: { emptyText: '暂无历史任务' } }) }) }, "history")] }), _jsx(Modal, { title: "\u542F\u52A8\u4EFB\u52A1", open: startTaskModalVisible, onOk: () => form.submit(), onCancel: () => {
                    setStartTaskModalVisible(false);
                    form.resetFields();
                }, confirmLoading: loading, width: 600, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: startTask, initialValues: {
                        taskType: 'daily',
                        enableStamina: true,
                        enableCommission: true,
                        staminaTarget: 240,
                        autoCollectRewards: true,
                        autoDialog: true,
                        autoBattle: true,
                        skipCutscene: false,
                        battleStrategy: 'auto'
                    }, children: [_jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "taskType", label: "\u4EFB\u52A1\u7C7B\u578B", required: true, children: _jsxs(Select, { onChange: setSelectedTaskType, children: [_jsx(Option, { value: "daily", children: "\u65E5\u5E38\u4EFB\u52A1" }), _jsx(Option, { value: "main", children: "\u4E3B\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "side", children: "\u652F\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "custom", children: "\u81EA\u5B9A\u4E49\u4EFB\u52A1" })] }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "accountId", label: "\u9009\u62E9\u8D26\u53F7", children: _jsx(Select, { placeholder: "\u9009\u62E9\u8D26\u53F7\uFF08\u53EF\u9009\uFF09", children: accounts.map(account => (_jsxs(Option, { value: account.id, children: [account.name, " (", account.gameAccount, ")"] }, account.id))) }) }) })] }), renderTaskConfigForm()] }) }), _jsx(GameStatusDialog, { visible: showGameDialog, onClose: () => setShowGameDialog(false), onLaunch: launchGame, onCancel: () => setShowGameDialog(false), title: "\u6E38\u620F\u672A\u542F\u52A8", message: "\u68C0\u6D4B\u5230\u6E38\u620F\u672A\u542F\u52A8\uFF0C\u542F\u52A8\u4EFB\u52A1\u9700\u8981\u6E38\u620F\u5904\u4E8E\u8FD0\u884C\u72B6\u6001\u3002\u662F\u5426\u73B0\u5728\u542F\u52A8\u6E38\u620F\uFF1F" })] }));
};
export default Tasks;
