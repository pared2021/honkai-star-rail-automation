import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 攻略管理页面
import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, Space, message, Tag, Progress, Descriptions, Tabs, Row, Col, Statistic, Alert, Tooltip, Rate, Timeline, List, Avatar, Popconfirm } from 'antd';
import { ReloadOutlined, PlayCircleOutlined, EyeOutlined, SearchOutlined, TrophyOutlined, ClockCircleOutlined, StarOutlined, SafetyOutlined, DollarOutlined, CheckCircleOutlined, ExclamationCircleOutlined, DatabaseOutlined, EditOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons';
import PerformanceDashboard from '../../components/PerformanceDashboard';
import OptimizationSuggestions from '../../components/OptimizationSuggestions';
import FeedbackSystem from '../../components/FeedbackSystem';
const { TabPane } = Tabs;
const { Option } = Select;
const StrategyPage = () => {
    const [strategies, setStrategies] = useState([]);
    const [evaluations, setEvaluations] = useState({});
    const [loading, setLoading] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [selectedStrategy, setSelectedStrategy] = useState(null);
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [filterTaskType, setFilterTaskType] = useState('all');
    const [searchText, setSearchText] = useState('');
    const [selectedTaskId, setSelectedTaskId] = useState('');
    // 预置攻略管理相关状态
    const [presetStrategies, setPresetStrategies] = useState([]);
    const [presetLoading, setPresetLoading] = useState(false);
    const [presetStats, setPresetStats] = useState(null);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editingStrategy, setEditingStrategy] = useState(null);
    const [form] = Form.useForm();
    // 获取攻略列表
    const fetchStrategies = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/tasks/strategies');
            if (response.ok) {
                const data = await response.json();
                setStrategies(data.data || []);
            }
            else {
                message.error('获取攻略列表失败');
            }
        }
        catch (error) {
            console.error('获取攻略列表失败:', error);
            message.error('获取攻略列表失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 获取攻略评估
    const fetchEvaluations = async (strategyId) => {
        try {
            const response = await fetch(`/api/tasks/strategies/${strategyId}/evaluations`);
            if (response.ok) {
                const data = await response.json();
                setEvaluations(prev => ({
                    ...prev,
                    [strategyId]: data.data || []
                }));
            }
        }
        catch (error) {
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
                    }
                    catch (error) {
                        console.error('获取分析状态失败:', error);
                    }
                }, 3000);
                // 10分钟后停止刷新
                setTimeout(() => {
                    clearInterval(interval);
                }, 600000);
            }
            else {
                message.error('启动攻略分析失败');
            }
        }
        catch (error) {
            console.error('启动攻略分析失败:', error);
            message.error('启动攻略分析失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 获取最优攻略
    const getBestStrategy = async (taskId) => {
        try {
            const response = await fetch(`/api/tasks/strategies/${taskId}/best`);
            if (response.ok) {
                const data = await response.json();
                if (data.data) {
                    setSelectedStrategy(data.data);
                    setDetailModalVisible(true);
                    await fetchEvaluations(data.data.id);
                }
                else {
                    message.info('该任务暂无攻略数据');
                }
            }
            else {
                message.error('获取最优攻略失败');
            }
        }
        catch (error) {
            console.error('获取最优攻略失败:', error);
            message.error('获取最优攻略失败');
        }
    };
    // 显示攻略详情
    const showStrategyDetail = async (strategy) => {
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
    const getScoreColor = (score) => {
        if (score >= 0.8)
            return '#52c41a';
        if (score >= 0.6)
            return '#1890ff';
        if (score >= 0.4)
            return '#faad14';
        return '#f5222d';
    };
    // 任务类型标签颜色
    const getTaskTypeColor = (type) => {
        switch (type) {
            case 'main': return 'red';
            case 'side': return 'blue';
            case 'daily': return 'green';
            case 'event': return 'orange';
            default: return 'default';
        }
    };
    // 任务类型名称
    const getTaskTypeName = (type) => {
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
            render: (text, record) => (_jsxs(Space, { children: [_jsx("span", { children: text }), record.isVerified && _jsxs(Tag, { color: "gold", children: [_jsx(StarOutlined, {}), " \u5DF2\u9A8C\u8BC1"] })] }))
        },
        {
            title: '难度等级',
            dataIndex: 'difficulty',
            key: 'difficulty',
            width: 100,
            render: (difficulty) => (_jsx(Tag, { color: difficulty === 'easy' ? 'green' : difficulty === 'medium' ? 'orange' : 'red', children: difficulty === 'easy' ? '简单' : difficulty === 'medium' ? '中等' : '困难' }))
        },
        {
            title: '成功率',
            dataIndex: 'successRate',
            key: 'successRate',
            width: 120,
            render: (score) => (_jsxs("div", { children: [_jsx(Rate, { disabled: true, value: score * 5, allowHalf: true, style: { fontSize: '12px' } }), _jsxs("div", { style: { color: getScoreColor(score), fontWeight: 'bold' }, children: [(score * 100).toFixed(1), "%"] })] }))
        },
        {
            title: '预计时间',
            dataIndex: 'estimatedTime',
            key: 'estimatedTime',
            width: 100,
            render: (time) => (_jsxs("div", { children: [_jsx(ClockCircleOutlined, {}), " ", time, "\u5206\u949F"] }))
        },
        {
            title: '验证状态',
            dataIndex: 'isVerified',
            key: 'isVerified',
            width: 100,
            render: (isVerified) => (_jsxs("div", { children: [_jsx(CheckCircleOutlined, { style: { color: isVerified ? '#52c41a' : '#d9d9d9' } }), isVerified ? '已验证' : '未验证'] }))
        },
        {
            title: '创建时间',
            dataIndex: 'createdAt',
            key: 'createdAt',
            width: 150,
            render: (date) => new Date(date).toLocaleString()
        },
        {
            title: '更新时间',
            dataIndex: 'updatedAt',
            key: 'updatedAt',
            width: 150,
            render: (date) => new Date(date).toLocaleString()
        },
        {
            title: '操作',
            key: 'action',
            width: 120,
            render: (_, record) => (_jsx(Space, { children: _jsx(Tooltip, { title: "\u67E5\u770B\u8BE6\u60C5", children: _jsx(Button, { type: "link", icon: _jsx(EyeOutlined, {}), onClick: () => showStrategyDetail(record) }) }) }))
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
            }
            else {
                message.error('获取预置攻略失败');
            }
        }
        catch (error) {
            console.error('获取预置攻略失败:', error);
            message.error('获取预置攻略失败');
        }
        finally {
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
        }
        catch (error) {
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
            }
            else {
                message.error('重新初始化失败');
            }
        }
        catch (error) {
            console.error('重新初始化失败:', error);
            message.error('重新初始化失败');
        }
        finally {
            setPresetLoading(false);
        }
    };
    // 删除预置攻略
    const deletePresetStrategy = async (strategyId) => {
        try {
            const response = await fetch(`/api/tasks/strategies/${strategyId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                message.success('删除成功');
                await fetchPresetStrategies();
                await fetchPresetStats();
            }
            else {
                message.error('删除失败');
            }
        }
        catch (error) {
            console.error('删除失败:', error);
            message.error('删除失败');
        }
    };
    // 编辑预置攻略
    const editPresetStrategy = (strategy) => {
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
    const saveEditedStrategy = async (values) => {
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
            }
            else {
                message.error('保存失败');
            }
        }
        catch (error) {
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
            render: (difficulty) => (_jsx(Tag, { color: difficulty === 'easy' ? 'green' : difficulty === 'medium' ? 'orange' : 'red', children: difficulty === 'easy' ? '简单' : difficulty === 'medium' ? '中等' : '困难' }))
        },
        {
            title: '步骤数量',
            dataIndex: 'steps',
            key: 'stepsCount',
            width: 100,
            render: (steps) => steps?.length || 0
        },
        {
            title: '来源',
            dataIndex: 'source',
            key: 'source',
            width: 100,
            render: (source) => (_jsx(Tag, { color: "blue", children: source === 'preset' ? '内置' : '用户' }))
        },
        {
            title: '更新时间',
            dataIndex: 'updatedAt',
            key: 'updatedAt',
            width: 150,
            render: (date) => new Date(date).toLocaleString()
        },
        {
            title: '操作',
            key: 'action',
            width: 150,
            render: (_, record) => (_jsxs(Space, { children: [_jsx(Tooltip, { title: "\u67E5\u770B\u8BE6\u60C5", children: _jsx(Button, { type: "link", icon: _jsx(EyeOutlined, {}), onClick: () => showStrategyDetail(record) }) }), _jsx(Tooltip, { title: "\u7F16\u8F91", children: _jsx(Button, { type: "link", icon: _jsx(EditOutlined, {}), onClick: () => editPresetStrategy(record) }) }), _jsx(Popconfirm, { title: "\u786E\u5B9A\u8981\u5220\u9664\u8FD9\u4E2A\u653B\u7565\u5417\uFF1F", onConfirm: () => deletePresetStrategy(record.id), okText: "\u786E\u5B9A", cancelText: "\u53D6\u6D88", children: _jsx(Tooltip, { title: "\u5220\u9664", children: _jsx(Button, { type: "link", danger: true, icon: _jsx(DeleteOutlined, {}) }) }) })] }))
        }
    ];
    useEffect(() => {
        fetchStrategies();
        fetchPresetStrategies();
        fetchPresetStats();
    }, []);
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { span: 12, children: _jsx("h2", { children: "\u653B\u7565\u7BA1\u7406" }) }), _jsx(Col, { span: 12, style: { textAlign: 'right' }, children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), onClick: startAnalysis, loading: loading, children: "\u542F\u52A8\u653B\u7565\u5206\u6790" }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: fetchStrategies, loading: loading, children: "\u5237\u65B0" })] }) })] }), analysisResult && (_jsx(Alert, { message: `分析状态: 已完成`, description: _jsxs("div", { children: [_jsx(Progress, { percent: 100, status: 'success', style: { marginBottom: '8px' } }), _jsxs("div", { children: ["\u5206\u6790\u65F6\u95F4: ", new Date(analysisResult.analysisTime).toLocaleString()] }), _jsxs("div", { children: ["\u7F6E\u4FE1\u5EA6: ", (analysisResult.confidenceLevel * 100).toFixed(1), "%"] }), _jsxs("div", { children: ["\u5206\u6790\u8BC4\u5206: ", analysisResult.analysisScore.toFixed(1)] })] }), type: 'success', style: { marginBottom: '16px' } })), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u603B\u653B\u7565\u6570", value: strategies.length, prefix: _jsx(TrophyOutlined, {}) }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u6700\u4F18\u653B\u7565", value: strategies.filter(s => s.isVerified).length, valueStyle: { color: '#faad14' }, prefix: _jsx(StarOutlined, {}) }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u5E73\u5747\u8BC4\u5206", value: (strategies.reduce((sum, s) => sum + s.successRate, 0) / strategies.length * 100).toFixed(1), suffix: "%", valueStyle: { color: '#52c41a' } }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u9AD8\u5206\u653B\u7565", value: strategies.filter(s => s.successRate >= 0.8).length, valueStyle: { color: '#1890ff' } }) }) })] }), _jsx(Card, { style: { marginBottom: '16px' }, children: _jsxs(Row, { gutter: 16, align: "middle", children: [_jsx(Col, { span: 8, children: _jsx(Input, { placeholder: "\u8F93\u5165\u4EFB\u52A1ID\u67E5\u627E\u6700\u4F18\u653B\u7565", value: selectedTaskId, onChange: (e) => setSelectedTaskId(e.target.value) }) }), _jsx(Col, { span: 4, children: _jsx(Button, { type: "primary", icon: _jsx(SearchOutlined, {}), onClick: () => selectedTaskId && getBestStrategy(selectedTaskId), disabled: !selectedTaskId, children: "\u67E5\u627E\u6700\u4F18\u653B\u7565" }) })] }) }), _jsx(Card, { style: { marginBottom: '16px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 8, children: _jsx(Input, { placeholder: "\u641C\u7D22\u653B\u7565\u540D\u79F0\u6216\u63CF\u8FF0", prefix: _jsx(SearchOutlined, {}), value: searchText, onChange: (e) => setSearchText(e.target.value) }) }), _jsx(Col, { span: 8, children: _jsxs(Select, { style: { width: '100%' }, placeholder: "\u9009\u62E9\u4EFB\u52A1\u7C7B\u578B", value: filterTaskType, onChange: setFilterTaskType, children: [_jsx(Option, { value: "all", children: "\u5168\u90E8\u7C7B\u578B" }), _jsx(Option, { value: "main", children: "\u4E3B\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "side", children: "\u652F\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "daily", children: "\u65E5\u5E38\u4EFB\u52A1" }), _jsx(Option, { value: "event", children: "\u6D3B\u52A8\u4EFB\u52A1" })] }) })] }) }), _jsxs(Tabs, { defaultActiveKey: "strategies", children: [_jsx(Tabs.TabPane, { tab: "\u653B\u7565\u5217\u8868", children: _jsx(Card, { children: _jsx(Table, { columns: columns, dataSource: filteredStrategies, rowKey: "id", loading: loading, pagination: {
                                    pageSize: 10,
                                    showSizeChanger: true,
                                    showQuickJumper: true,
                                    showTotal: (total) => `共 ${total} 条记录`
                                } }) }) }, "strategies"), _jsxs(Tabs.TabPane, { tab: _jsxs("span", { children: [_jsx(DatabaseOutlined, {}), "\u9884\u7F6E\u653B\u7565\u7BA1\u7406"] }), children: [presetStats && (_jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u9884\u7F6E\u653B\u7565\u603B\u6570", value: presetStats.totalStrategies, prefix: _jsx(DatabaseOutlined, {}) }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u4E3B\u7EBF\u4EFB\u52A1\u653B\u7565", value: presetStats.mainTaskStrategies, valueStyle: { color: '#f5222d' } }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u652F\u7EBF\u4EFB\u52A1\u653B\u7565", value: presetStats.sideTaskStrategies, valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u65E5\u5E38\u4EFB\u52A1\u653B\u7565", value: presetStats.dailyTaskStrategies, valueStyle: { color: '#52c41a' } }) }) })] })), _jsx(Card, { style: { marginBottom: '16px' }, children: _jsx(Row, { gutter: 16, align: "middle", children: _jsx(Col, { span: 12, children: _jsxs(Space, { children: [_jsx(Popconfirm, { title: "\u786E\u5B9A\u8981\u91CD\u65B0\u521D\u59CB\u5316\u9884\u7F6E\u653B\u7565\u6570\u636E\u5417\uFF1F\u8FD9\u5C06\u8986\u76D6\u73B0\u6709\u7684\u9884\u7F6E\u653B\u7565\u3002", onConfirm: reinitializePresetData, okText: "\u786E\u5B9A", cancelText: "\u53D6\u6D88", children: _jsx(Button, { type: "primary", icon: _jsx(SyncOutlined, {}), loading: presetLoading, children: "\u91CD\u65B0\u521D\u59CB\u5316\u9884\u7F6E\u6570\u636E" }) }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                                        fetchPresetStrategies();
                                                        fetchPresetStats();
                                                    }, loading: presetLoading, children: "\u5237\u65B0" })] }) }) }) }), _jsx(Card, { children: _jsx(Table, { columns: presetColumns, dataSource: presetStrategies, rowKey: "id", loading: presetLoading, pagination: {
                                        pageSize: 10,
                                        showSizeChanger: true,
                                        showQuickJumper: true,
                                        showTotal: (total) => `共 ${total} 条预置攻略`
                                    } }) })] }, "preset")] }), _jsx(Modal, { title: "\u7F16\u8F91\u9884\u7F6E\u653B\u7565", open: editModalVisible, onCancel: () => {
                    setEditModalVisible(false);
                    setEditingStrategy(null);
                    form.resetFields();
                }, onOk: () => form.submit(), width: 800, okText: "\u4FDD\u5B58", cancelText: "\u53D6\u6D88", children: _jsxs(Form, { form: form, layout: "vertical", onFinish: saveEditedStrategy, children: [_jsx(Form.Item, { name: "name", label: "\u653B\u7565\u540D\u79F0", rules: [{ required: true, message: '请输入攻略名称' }], children: _jsx(Input, { placeholder: "\u8BF7\u8F93\u5165\u653B\u7565\u540D\u79F0" }) }), _jsx(Form.Item, { name: "taskType", label: "\u4EFB\u52A1\u7C7B\u578B", rules: [{ required: true, message: '请选择任务类型' }], children: _jsxs(Select, { placeholder: "\u8BF7\u9009\u62E9\u4EFB\u52A1\u7C7B\u578B", children: [_jsx(Option, { value: "main", children: "\u4E3B\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "side", children: "\u652F\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "daily", children: "\u65E5\u5E38\u4EFB\u52A1" }), _jsx(Option, { value: "event", children: "\u6D3B\u52A8\u4EFB\u52A1" })] }) }), _jsx(Form.Item, { name: "description", label: "\u653B\u7565\u63CF\u8FF0", rules: [{ required: true, message: '请输入攻略描述' }], children: _jsx(Input.TextArea, { rows: 3, placeholder: "\u8BF7\u8F93\u5165\u653B\u7565\u63CF\u8FF0" }) }), _jsx(Form.Item, { name: "steps", label: "\u653B\u7565\u6B65\u9AA4 (JSON\u683C\u5F0F)", rules: [
                                { required: true, message: '请输入攻略步骤' },
                                {
                                    validator: (_, value) => {
                                        try {
                                            JSON.parse(value);
                                            return Promise.resolve();
                                        }
                                        catch {
                                            return Promise.reject(new Error('请输入有效的JSON格式'));
                                        }
                                    }
                                }
                            ], children: _jsx(Input.TextArea, { rows: 10, placeholder: "\u8BF7\u8F93\u5165JSON\u683C\u5F0F\u7684\u653B\u7565\u6B65\u9AA4", style: { fontFamily: 'monospace' } }) })] }) }), _jsx(Modal, { title: "\u653B\u7565\u8BE6\u60C5", open: detailModalVisible, onCancel: () => setDetailModalVisible(false), footer: null, width: 1000, children: selectedStrategy && (_jsxs(Tabs, { defaultActiveKey: "basic", children: [_jsx(TabPane, { tab: "\u57FA\u672C\u4FE1\u606F", children: _jsxs(Descriptions, { column: 2, bordered: true, children: [_jsx(Descriptions.Item, { label: "\u653B\u7565\u540D\u79F0", span: 2, children: _jsxs(Space, { children: [selectedStrategy.strategyName, selectedStrategy.isVerified && _jsxs(Tag, { color: "gold", children: [_jsx(StarOutlined, {}), " \u5DF2\u9A8C\u8BC1\u653B\u7565"] })] }) }), _jsx(Descriptions.Item, { label: "\u4EFB\u52A1\u7C7B\u578B", children: _jsx(Tag, { color: selectedStrategy.difficulty === 'easy' ? 'green' : selectedStrategy.difficulty === 'medium' ? 'blue' : 'red', children: selectedStrategy.difficulty === 'easy' ? '简单' : selectedStrategy.difficulty === 'medium' ? '中等' : '困难' }) }), _jsx(Descriptions.Item, { label: "\u603B\u8BC4\u5206", children: _jsxs(Space, { children: [_jsx(Rate, { disabled: true, value: selectedStrategy.successRate * 5, allowHalf: true }), _jsxs("span", { style: { color: getScoreColor(selectedStrategy.successRate), fontWeight: 'bold' }, children: [(selectedStrategy.successRate * 100).toFixed(1), "%"] })] }) }), _jsx(Descriptions.Item, { label: "\u65F6\u95F4\u6548\u7387", children: _jsxs("div", { style: { color: getScoreColor(selectedStrategy.successRate) }, children: [_jsx(ClockCircleOutlined, {}), " ", selectedStrategy.estimatedTime, "\u5206\u949F"] }) }), _jsx(Descriptions.Item, { label: "\u6210\u529F\u7387", children: _jsxs("div", { style: { color: getScoreColor(selectedStrategy.successRate) }, children: [_jsx(CheckCircleOutlined, {}), " ", (selectedStrategy.successRate * 100).toFixed(1), "%"] }) }), _jsx(Descriptions.Item, { label: "\u53EF\u9760\u6027", children: _jsxs("div", { style: { color: getScoreColor(selectedStrategy.successRate) }, children: [_jsx(SafetyOutlined, {}), " ", (selectedStrategy.successRate * 100).toFixed(1), "%"] }) }), _jsx(Descriptions.Item, { label: "\u8D44\u6E90\u6D88\u8017", children: _jsxs("div", { style: { color: getScoreColor(selectedStrategy.successRate) }, children: [_jsx(DollarOutlined, {}), " ", selectedStrategy.estimatedTime, "\u5206\u949F"] }) }), _jsx(Descriptions.Item, { label: "\u63CF\u8FF0", span: 2, children: selectedStrategy.description })] }) }, "basic"), _jsx(TabPane, { tab: "\u653B\u7565\u6B65\u9AA4", children: _jsx(Timeline, { children: selectedStrategy.steps.map((step, index) => (_jsx(Timeline.Item, { color: step.stepType === 'battle' ? 'red' : step.stepType === 'dialog' ? 'blue' : 'green', children: _jsxs(Card, { size: "small", children: [_jsxs("div", { children: [_jsxs("strong", { children: ["\u6B65\u9AA4 ", index + 1, ":"] }), " ", step.description] }), _jsxs("div", { children: [_jsx("strong", { children: "\u52A8\u4F5C:" }), " ", step.action.type] }), step.action.parameters && Object.keys(step.action.parameters).length > 0 && (_jsxs("div", { children: [_jsx("strong", { children: "\u53C2\u6570:" }), " ", JSON.stringify(step.action.parameters)] })), step.conditions && step.conditions.length > 0 && (_jsxs("div", { children: [_jsx("strong", { children: "\u6761\u4EF6:" }), _jsx(Space, { wrap: true, style: { marginLeft: '8px' }, children: step.conditions.map((condition, condIndex) => (_jsxs(Tag, { children: [condition.type, ": ", condition.value] }, condIndex))) })] })), _jsxs("div", { children: [_jsx("strong", { children: "\u8D85\u65F6\u65F6\u95F4:" }), " ", step.timeout, "\u79D2"] })] }) }, index))) }) }, "steps"), _jsx(TabPane, { tab: "\u6027\u80FD\u5206\u6790", children: _jsx(PerformanceDashboard, { strategyId: selectedStrategy.id }) }, "performance"), _jsx(TabPane, { tab: "\u4F18\u5316\u5EFA\u8BAE", children: _jsx(OptimizationSuggestions, { strategyId: selectedStrategy.id }) }, "optimization"), _jsx(TabPane, { tab: "\u7528\u6237\u53CD\u9988", children: _jsx(FeedbackSystem, { strategyId: selectedStrategy.id }) }, "feedback"), _jsx(TabPane, { tab: "\u8BC4\u4F30\u8BB0\u5F55", children: evaluations[selectedStrategy.id] && evaluations[selectedStrategy.id].length > 0 ? (_jsx(List, { dataSource: evaluations[selectedStrategy.id], renderItem: (evaluation) => (_jsx(List.Item, { children: _jsx(List.Item.Meta, { avatar: _jsx(Avatar, { style: {
                                                backgroundColor: evaluation.success ? '#52c41a' : '#f5222d'
                                            }, icon: evaluation.success ? _jsx(CheckCircleOutlined, {}) : _jsx(ExclamationCircleOutlined, {}) }), title: _jsxs(Space, { children: [_jsxs("span", { children: ["\u8BC4\u4F30 #", evaluation.id.slice(-6)] }), _jsx(Tag, { color: evaluation.success ? 'success' : 'error', children: evaluation.success ? '成功' : '失败' }), _jsxs("span", { children: ["\u8017\u65F6: ", evaluation.executionTime, "\u79D2"] })] }), description: _jsxs("div", { children: [_jsxs("div", { children: ["\u8BC4\u4F30\u65F6\u95F4: ", new Date(evaluation.executedAt).toLocaleString()] }), evaluation.feedback && _jsxs("div", { children: ["\u53CD\u9988: ", evaluation.feedback] }), evaluation.feedback && (_jsxs("div", { children: [_jsx("strong", { children: "\u53CD\u9988:" }), _jsx("p", { children: evaluation.feedback })] }))] }) }) })) })) : (_jsxs("div", { style: { textAlign: 'center', padding: '40px' }, children: [_jsx(ExclamationCircleOutlined, { style: { fontSize: '48px', color: '#d9d9d9' } }), _jsx("div", { style: { marginTop: '16px', color: '#999' }, children: "\u6682\u65E0\u8BC4\u4F30\u8BB0\u5F55" })] })) }, "evaluations")] })) })] }));
};
export default StrategyPage;
