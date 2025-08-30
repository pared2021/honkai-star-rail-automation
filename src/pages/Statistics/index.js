import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 数据统计页面
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Select, DatePicker, Table, Space, Button, Empty } from 'antd';
import { TrophyOutlined, ClockCircleOutlined, CheckCircleOutlined, ExclamationCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
const { Option } = Select;
const { RangePicker } = DatePicker;
const Statistics = () => {
    const [accounts, setAccounts] = useState([]);
    const [selectedAccountId, setSelectedAccountId] = useState('all');
    const [dateRange, setDateRange] = useState(null);
    const [taskHistory, setTaskHistory] = useState([]);
    const [statistics, setStatistics] = useState({
        totalTasks: 0,
        completedTasks: 0,
        failedTasks: 0,
        totalTime: 0,
        averageTime: 0,
        successRate: 0
    });
    const [loading, setLoading] = useState(false);
    // 获取账号列表
    const fetchAccounts = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/accounts');
            const data = await response.json();
            if (data.success) {
                setAccounts(data.data);
            }
        }
        catch (error) {
            console.error('获取账号列表失败:', error);
        }
    };
    // 获取任务历史
    const fetchTaskHistory = async () => {
        try {
            setLoading(true);
            const accountId = selectedAccountId === 'all' ? undefined : selectedAccountId;
            const response = await fetch('http://localhost:3001/api/task/history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ accountId })
            });
            const data = await response.json();
            if (data.success) {
                let tasks = data.data;
                // 根据日期范围过滤
                if (dateRange && dateRange[0] && dateRange[1]) {
                    const startDate = dateRange[0].startOf('day');
                    const endDate = dateRange[1].endOf('day');
                    tasks = tasks.filter((task) => {
                        const taskDate = new Date(task.createdAt);
                        return taskDate >= startDate.toDate() && taskDate <= endDate.toDate();
                    });
                }
                setTaskHistory(tasks);
                calculateStatistics(tasks);
            }
        }
        catch (error) {
            console.error('获取任务历史失败:', error);
        }
        finally {
            setLoading(false);
        }
    };
    // 计算统计数据
    const calculateStatistics = (tasks) => {
        const totalTasks = tasks.length;
        const completedTasks = tasks.filter(task => task.status === 'completed').length;
        const failedTasks = tasks.filter(task => task.status === 'failed').length;
        let totalTime = 0;
        tasks.forEach(task => {
            if (task.startTime && task.endTime) {
                totalTime += new Date(task.endTime).getTime() - new Date(task.startTime).getTime();
            }
        });
        const averageTime = totalTasks > 0 ? totalTime / totalTasks : 0;
        const successRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
        setStatistics({
            totalTasks,
            completedTasks,
            failedTasks,
            totalTime,
            averageTime,
            successRate
        });
    };
    // 刷新数据
    const refreshData = () => {
        fetchTaskHistory();
    };
    // 导出数据
    const exportData = () => {
        // TODO: 实现数据导出功能
        console.log('导出数据功能待实现');
    };
    // 组件挂载时获取数据
    useEffect(() => {
        fetchAccounts();
    }, []);
    // 当筛选条件变化时重新获取数据
    useEffect(() => {
        fetchTaskHistory();
    }, [selectedAccountId, dateRange]);
    // 格式化时间
    const formatTime = (milliseconds) => {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) {
            return `${hours}小时${minutes % 60}分钟`;
        }
        else if (minutes > 0) {
            return `${minutes}分钟${seconds % 60}秒`;
        }
        else {
            return `${seconds}秒`;
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
    // 任务历史表格列
    const taskColumns = [
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
            render: (status) => {
                const statusMap = {
                    completed: { color: '#52c41a', text: '已完成' },
                    failed: { color: '#ff4d4f', text: '失败' },
                    cancelled: { color: '#d9d9d9', text: '已取消' }
                };
                const config = statusMap[status] || { color: '#1890ff', text: status };
                return _jsx("span", { style: { color: config.color }, children: config.text });
            }
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
                    return formatTime(duration);
                }
                return '-';
            }
        }
    ];
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: [_jsx("h1", { style: { margin: 0 }, children: "\u6570\u636E\u7EDF\u8BA1" }), _jsxs(Space, { children: [_jsx(Button, { icon: _jsx(DownloadOutlined, {}), onClick: exportData, children: "\u5BFC\u51FA\u6570\u636E" }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: refreshData, loading: loading, children: "\u5237\u65B0" })] })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: [16, 16], align: "middle", children: [_jsxs(Col, { span: 6, children: [_jsx("span", { style: { marginRight: '8px' }, children: "\u8D26\u53F7:" }), _jsxs(Select, { value: selectedAccountId, onChange: setSelectedAccountId, style: { width: '100%' }, children: [_jsx(Option, { value: "all", children: "\u5168\u90E8\u8D26\u53F7" }), accounts.map(account => (_jsx(Option, { value: account.id, children: account.name }, account.id)))] })] }), _jsxs(Col, { span: 8, children: [_jsx("span", { style: { marginRight: '8px' }, children: "\u65F6\u95F4\u8303\u56F4:" }), _jsx(RangePicker, { value: dateRange, onChange: setDateRange, style: { width: '100%' }, placeholder: ['开始日期', '结束日期'] })] })] }) }), _jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u603B\u4EFB\u52A1\u6570", value: statistics.totalTasks, prefix: _jsx(TrophyOutlined, {}), valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u5B8C\u6210\u4EFB\u52A1", value: statistics.completedTasks, prefix: _jsx(CheckCircleOutlined, {}), valueStyle: { color: '#52c41a' } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u5931\u8D25\u4EFB\u52A1", value: statistics.failedTasks, prefix: _jsx(ExclamationCircleOutlined, {}), valueStyle: { color: '#ff4d4f' } }) }) }), _jsx(Col, { xs: 24, sm: 12, md: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u6210\u529F\u7387", value: statistics.successRate, precision: 1, suffix: "%", prefix: _jsx(CheckCircleOutlined, {}), valueStyle: {
                                    color: statistics.successRate >= 80 ? '#52c41a' :
                                        statistics.successRate >= 60 ? '#faad14' : '#ff4d4f'
                                } }) }) })] }), _jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u603B\u8017\u65F6", value: formatTime(statistics.totalTime), prefix: _jsx(ClockCircleOutlined, {}), valueStyle: { color: '#722ed1' } }) }) }), _jsx(Col, { xs: 24, sm: 12, children: _jsx(Card, { children: _jsx(Statistic, { title: "\u5E73\u5747\u8017\u65F6", value: formatTime(statistics.averageTime), prefix: _jsx(ClockCircleOutlined, {}), valueStyle: { color: '#13c2c2' } }) }) })] }), _jsx(Card, { title: "\u4EFB\u52A1\u5386\u53F2", children: taskHistory.length > 0 ? (_jsx(Table, { columns: taskColumns, dataSource: taskHistory, rowKey: "id", loading: loading, pagination: {
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 条记录`
                    } })) : (_jsx(Empty, { description: "\u6682\u65E0\u4EFB\u52A1\u6570\u636E", style: { padding: '40px' } })) })] }));
};
export default Statistics;
