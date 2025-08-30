import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 任务信息管理页面
import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Input, Select, Space, message, Tag, Progress, Descriptions, Tabs, Row, Col, Statistic, Alert, Tooltip } from 'antd';
import { ReloadOutlined, PlayCircleOutlined, EyeOutlined, SearchOutlined, InfoCircleOutlined, TrophyOutlined, ClockCircleOutlined } from '@ant-design/icons';
const { TabPane } = Tabs;
const { Option } = Select;
const TaskInfoPage = () => {
    const [taskInfos, setTaskInfos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [collectStatus, setCollectStatus] = useState(null);
    const [selectedTaskInfo, setSelectedTaskInfo] = useState(null);
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [filterType, setFilterType] = useState('all');
    const [searchText, setSearchText] = useState('');
    // 获取任务信息列表
    const fetchTaskInfos = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/tasks/info');
            if (response.ok) {
                const data = await response.json();
                setTaskInfos(data.data || []);
            }
            else {
                message.error('获取任务信息失败');
            }
        }
        catch (error) {
            console.error('获取任务信息失败:', error);
            message.error('获取任务信息失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 获取收集状态
    const fetchCollectStatus = async () => {
        try {
            const response = await fetch('/api/tasks/info/collect/status');
            if (response.ok) {
                const data = await response.json();
                setCollectStatus(data.data);
            }
        }
        catch (error) {
            console.error('获取收集状态失败:', error);
        }
    };
    // 启动任务信息收集
    const startCollection = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/tasks/info/collect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (response.ok) {
                message.success('任务信息收集已启动');
                fetchCollectStatus();
                // 定期刷新状态
                const interval = setInterval(() => {
                    fetchCollectStatus();
                }, 2000);
                // 5分钟后停止刷新
                setTimeout(() => {
                    clearInterval(interval);
                    fetchTaskInfos();
                }, 300000);
            }
            else {
                message.error('启动任务信息收集失败');
            }
        }
        catch (error) {
            console.error('启动任务信息收集失败:', error);
            message.error('启动任务信息收集失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 显示任务详情
    const showTaskDetail = (taskInfo) => {
        setSelectedTaskInfo(taskInfo);
        setDetailModalVisible(true);
    };
    // 过滤任务信息
    const filteredTaskInfos = taskInfos.filter(taskInfo => {
        const matchesType = filterType === 'all' || taskInfo.type === filterType;
        const matchesSearch = !searchText ||
            taskInfo.name.toLowerCase().includes(searchText.toLowerCase()) ||
            taskInfo.description.toLowerCase().includes(searchText.toLowerCase());
        return matchesType && matchesSearch;
    });
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
    // 难度标签颜色
    const getDifficultyColor = (difficulty) => {
        switch (difficulty) {
            case 'easy': return 'green';
            case 'normal': return 'blue';
            case 'hard': return 'orange';
            case 'extreme': return 'red';
            default: return 'default';
        }
    };
    // 难度名称
    const getDifficultyName = (difficulty) => {
        switch (difficulty) {
            case 'easy': return '简单';
            case 'normal': return '普通';
            case 'hard': return '困难';
            case 'extreme': return '极难';
            default: return '未知';
        }
    };
    // 表格列定义
    const columns = [
        {
            title: '任务名称',
            dataIndex: 'name',
            key: 'name',
            width: 200,
            render: (text, record) => (_jsxs(Space, { children: [_jsx("span", { children: text }), record.isRepeatable && _jsx(Tag, { color: "cyan", children: "\u53EF\u91CD\u590D" })] }))
        },
        {
            title: '类型',
            dataIndex: 'type',
            key: 'type',
            width: 100,
            render: (type) => (_jsx(Tag, { color: getTaskTypeColor(type), children: getTaskTypeName(type) }))
        },
        {
            title: '难度',
            dataIndex: 'difficulty',
            key: 'difficulty',
            width: 80,
            render: (difficulty) => (_jsx(Tag, { color: getDifficultyColor(difficulty), children: getDifficultyName(difficulty) }))
        },
        {
            title: '预计时间',
            dataIndex: 'estimatedTime',
            key: 'estimatedTime',
            width: 100,
            render: (time) => (_jsxs("span", { children: [_jsx(ClockCircleOutlined, {}), " ", Math.round(time / 60), "\u5206\u949F"] }))
        },
        {
            title: '奖励',
            dataIndex: 'rewards',
            key: 'rewards',
            width: 150,
            render: (rewards) => (_jsxs(Space, { wrap: true, children: [rewards.slice(0, 2).map((reward, index) => (_jsxs(Tag, { color: "gold", children: [_jsx(TrophyOutlined, {}), " ", reward.name, " x", reward.amount] }, index))), rewards.length > 2 && (_jsxs(Tag, { children: ["+", rewards.length - 2, "\u9879"] }))] }))
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
            render: (_, record) => (_jsx(Space, { children: _jsx(Tooltip, { title: "\u67E5\u770B\u8BE6\u60C5", children: _jsx(Button, { type: "link", icon: _jsx(EyeOutlined, {}), onClick: () => showTaskDetail(record) }) }) }))
        }
    ];
    useEffect(() => {
        fetchTaskInfos();
        fetchCollectStatus();
    }, []);
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { span: 12, children: _jsx("h2", { children: "\u4EFB\u52A1\u4FE1\u606F\u7BA1\u7406" }) }), _jsx(Col, { span: 12, style: { textAlign: 'right' }, children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), onClick: startCollection, loading: loading, children: "\u542F\u52A8\u4FE1\u606F\u6536\u96C6" }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: fetchTaskInfos, loading: loading, children: "\u5237\u65B0" })] }) })] }), collectStatus && (_jsx(Alert, { message: `收集状态: ${collectStatus.status === 'collecting' ? '进行中' : '已完成'}`, description: _jsxs("div", { children: [_jsx(Progress, { percent: Math.round(collectStatus.collectionProgress * 100), status: collectStatus.status === 'collecting' ? 'active' : 'success', style: { marginBottom: '8px' } }), _jsxs("div", { children: ["\u5DF2\u6536\u96C6: ", collectStatus.collectedTasks, " / ", collectStatus.totalTasks, " \u4E2A\u4EFB\u52A1"] }), _jsxs("div", { children: ["\u6700\u540E\u6536\u96C6\u65F6\u95F4: ", new Date(collectStatus.lastCollectionTime).toLocaleString()] })] }), type: collectStatus.status === 'collecting' ? 'info' : 'success', style: { marginBottom: '16px' } })), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u603B\u4EFB\u52A1\u6570", value: taskInfos.length, prefix: _jsx(InfoCircleOutlined, {}) }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u4E3B\u7EBF\u4EFB\u52A1", value: taskInfos.filter(t => t.type === 'main').length, valueStyle: { color: '#cf1322' } }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u652F\u7EBF\u4EFB\u52A1", value: taskInfos.filter(t => t.type === 'side').length, valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { span: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u65E5\u5E38\u4EFB\u52A1", value: taskInfos.filter(t => t.type === 'daily').length, valueStyle: { color: '#52c41a' } }) }) })] }), _jsx(Card, { style: { marginBottom: '16px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 8, children: _jsx(Input, { placeholder: "\u641C\u7D22\u4EFB\u52A1\u540D\u79F0\u6216\u63CF\u8FF0", prefix: _jsx(SearchOutlined, {}), value: searchText, onChange: (e) => setSearchText(e.target.value) }) }), _jsx(Col, { span: 8, children: _jsxs(Select, { style: { width: '100%' }, placeholder: "\u9009\u62E9\u4EFB\u52A1\u7C7B\u578B", value: filterType, onChange: setFilterType, children: [_jsx(Option, { value: "all", children: "\u5168\u90E8\u7C7B\u578B" }), _jsx(Option, { value: "main", children: "\u4E3B\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "side", children: "\u652F\u7EBF\u4EFB\u52A1" }), _jsx(Option, { value: "daily", children: "\u65E5\u5E38\u4EFB\u52A1" }), _jsx(Option, { value: "event", children: "\u6D3B\u52A8\u4EFB\u52A1" })] }) })] }) }), _jsx(Card, { children: _jsx(Table, { columns: columns, dataSource: filteredTaskInfos, rowKey: "id", loading: loading, pagination: {
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 条记录`
                    } }) }), _jsx(Modal, { title: "\u4EFB\u52A1\u8BE6\u60C5", open: detailModalVisible, onCancel: () => setDetailModalVisible(false), footer: null, width: 800, children: selectedTaskInfo && (_jsxs(Tabs, { defaultActiveKey: "basic", children: [_jsx(TabPane, { tab: "\u57FA\u672C\u4FE1\u606F", children: _jsxs(Descriptions, { column: 2, bordered: true, children: [_jsx(Descriptions.Item, { label: "\u4EFB\u52A1\u540D\u79F0", span: 2, children: selectedTaskInfo.name }), _jsx(Descriptions.Item, { label: "\u4EFB\u52A1\u7C7B\u578B", children: _jsx(Tag, { color: getTaskTypeColor(selectedTaskInfo.type), children: getTaskTypeName(selectedTaskInfo.type) }) }), _jsx(Descriptions.Item, { label: "\u96BE\u5EA6", children: _jsx(Tag, { color: getDifficultyColor(selectedTaskInfo.difficulty), children: getDifficultyName(selectedTaskInfo.difficulty) }) }), _jsxs(Descriptions.Item, { label: "\u9884\u8BA1\u65F6\u95F4", children: [Math.round(selectedTaskInfo.estimatedTime / 60), "\u5206\u949F"] }), _jsx(Descriptions.Item, { label: "\u53EF\u91CD\u590D", children: selectedTaskInfo.isRepeatable ? '是' : '否' }), _jsx(Descriptions.Item, { label: "\u63CF\u8FF0", span: 2, children: selectedTaskInfo.description }), selectedTaskInfo.prerequisites.length > 0 && (_jsx(Descriptions.Item, { label: "\u524D\u7F6E\u6761\u4EF6", span: 2, children: _jsx(Space, { wrap: true, children: selectedTaskInfo.prerequisites.map((prereq, index) => (_jsx(Tag, { children: prereq }, index))) }) }))] }) }, "basic"), _jsx(TabPane, { tab: "\u5956\u52B1\u4FE1\u606F", children: _jsx(Table, { dataSource: selectedTaskInfo.rewards, columns: [
                                    {
                                        title: '奖励名称',
                                        dataIndex: 'name',
                                        key: 'name'
                                    },
                                    {
                                        title: '类型',
                                        dataIndex: 'type',
                                        key: 'type',
                                        render: (type) => (_jsx(Tag, { color: type === 'currency' ? 'gold' : type === 'item' ? 'blue' : 'green', children: type === 'currency' ? '货币' : type === 'item' ? '物品' : '经验' }))
                                    },
                                    {
                                        title: '数量',
                                        dataIndex: 'amount',
                                        key: 'amount'
                                    },
                                    {
                                        title: '描述',
                                        dataIndex: 'description',
                                        key: 'description'
                                    }
                                ], pagination: false, size: "small" }) }, "rewards"), selectedTaskInfo.steps && selectedTaskInfo.steps.length > 0 && (_jsx(TabPane, { tab: "\u4EFB\u52A1\u6B65\u9AA4", children: _jsx("div", { children: selectedTaskInfo.steps.map((step, index) => (_jsxs(Card, { size: "small", style: { marginBottom: '8px' }, children: [_jsxs("div", { children: [_jsxs("strong", { children: ["\u6B65\u9AA4 ", index + 1, ":"] }), " ", step.description] }), _jsxs("div", { children: [_jsx("strong", { children: "\u7C7B\u578B:" }), " ", step.stepType] }), step.expectedResult && _jsxs("div", { children: [_jsx("strong", { children: "\u9884\u671F\u7ED3\u679C:" }), " ", step.expectedResult] }), step.conditions && step.conditions.length > 0 && (_jsxs("div", { children: [_jsx("strong", { children: "\u6267\u884C\u6761\u4EF6:" }), _jsx(Space, { wrap: true, style: { marginLeft: '8px' }, children: step.conditions.map((condition, condIndex) => (_jsxs(Tag, { children: [condition.type, ": ", condition.value] }, condIndex))) })] }))] }, index))) }) }, "steps"))] })) })] }));
};
export default TaskInfoPage;
