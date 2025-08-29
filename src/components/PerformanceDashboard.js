import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Clock, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import PerformanceDataCollector from '../services/PerformanceDataCollector';
import ExecutionTracker from '../services/ExecutionTracker';
import IntelligentEvaluator from '../services/IntelligentEvaluator';
import { DatabaseService } from '../services/DatabaseService';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
const PerformanceDashboard = ({ strategyId, isExecuting = false }) => {
    const [performanceData, setPerformanceData] = useState([]);
    const [executionProgress, setExecutionProgress] = useState(null);
    const [evaluationResult, setEvaluationResult] = useState(null);
    const [activeSession, setActiveSession] = useState(null);
    const [historicalData, setHistoricalData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const dbService = new DatabaseService();
    const performanceCollector = new PerformanceDataCollector(dbService);
    const intelligentEvaluator = new IntelligentEvaluator(performanceCollector, dbService);
    const executionTracker = new ExecutionTracker(performanceCollector, intelligentEvaluator, dbService);
    useEffect(() => {
        if (isExecuting) {
            startRealTimeMonitoring();
        }
        else {
            loadHistoricalData();
        }
        return () => {
            if (isExecuting) {
                performanceCollector.stopCollection();
            }
        };
    }, [strategyId, isExecuting]);
    const startRealTimeMonitoring = async () => {
        try {
            await performanceCollector.startCollection();
            // 开始实时数据收集
            const interval = setInterval(async () => {
                const data = performanceCollector.getLatestData();
                if (data) {
                    setPerformanceData(prev => [...prev.slice(-50), data]); // 保留最近50个数据点
                }
                const progress = await executionTracker.getExecutionProgress(strategyId);
                setExecutionProgress(progress);
                const sessions = await performanceCollector.getActiveSessions();
                const session = sessions.find(s => s.strategyId === strategyId);
                setActiveSession(session);
            }, 1000);
            return () => clearInterval(interval);
        }
        catch (error) {
            console.error('启动实时监控失败:', error);
        }
    };
    const loadHistoricalData = async () => {
        setIsLoading(true);
        try {
            const history = await performanceCollector.getPerformanceHistory();
            setHistoricalData(history);
            const evaluation = await intelligentEvaluator.evaluateStrategy(strategyId);
            setEvaluationResult(evaluation);
        }
        catch (error) {
            console.error('加载历史数据失败:', error);
        }
        finally {
            setIsLoading(false);
        }
    };
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'success': return 'text-green-500';
            case 'failed': return 'text-red-500';
            case 'running': return 'text-blue-500';
            case 'paused': return 'text-yellow-500';
            default: return 'text-gray-500';
        }
    };
    const getStatusIcon = (status) => {
        switch (status) {
            case 'success': return _jsx(CheckCircle, { className: "w-4 h-4" });
            case 'failed': return _jsx(XCircle, { className: "w-4 h-4" });
            case 'running': return _jsx(Activity, { className: "w-4 h-4 animate-pulse" });
            default: return _jsx(Clock, { className: "w-4 h-4" });
        }
    };
    const renderRealTimeTab = () => (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsx(Card, { children: _jsx(CardContent, { className: "p-4", children: _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Cpu, { className: "w-5 h-5 text-blue-500" }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600", children: "CPU\u4F7F\u7528\u7387" }), _jsxs("p", { className: "text-lg font-semibold", children: [performanceData[performanceData.length - 1]?.cpuUsage?.toFixed(1) || 0, "%"] })] })] }) }) }), _jsx(Card, { children: _jsx(CardContent, { className: "p-4", children: _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(HardDrive, { className: "w-5 h-5 text-green-500" }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600", children: "\u5185\u5B58\u4F7F\u7528" }), _jsxs("p", { className: "text-lg font-semibold", children: [performanceData[performanceData.length - 1]?.memoryUsage?.toFixed(1) || 0, "%"] })] })] }) }) }), _jsx(Card, { children: _jsx(CardContent, { className: "p-4", children: _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Activity, { className: "w-5 h-5 text-purple-500" }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600", children: "FPS" }), _jsx("p", { className: "text-lg font-semibold", children: performanceData[performanceData.length - 1]?.fps || 0 })] })] }) }) }), _jsx(Card, { children: _jsx(CardContent, { className: "p-4", children: _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Wifi, { className: "w-5 h-5 text-orange-500" }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600", children: "\u7F51\u7EDC\u5EF6\u8FDF" }), _jsxs("p", { className: "text-lg font-semibold", children: [performanceData[performanceData.length - 1]?.networkLatency || 0, "ms"] })] })] }) }) })] }), executionProgress && (_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsxs(CardTitle, { className: "flex items-center space-x-2", children: [getStatusIcon(executionProgress.status), _jsx("span", { children: "\u6267\u884C\u8FDB\u5EA6" }), _jsx(Badge, { className: getStatusColor(executionProgress.status), children: executionProgress.status })] }) }), _jsx(CardContent, { children: _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between text-sm mb-2", children: [_jsx("span", { children: "\u603B\u4F53\u8FDB\u5EA6" }), _jsxs("span", { children: [executionProgress.completedSteps, "/", executionProgress.totalSteps] })] }), _jsx(Progress, { value: (executionProgress.completedSteps / executionProgress.totalSteps) * 100 })] }), _jsxs("div", { className: "grid grid-cols-2 gap-4 text-sm", children: [_jsxs("div", { children: [_jsx("span", { className: "text-gray-600", children: "\u5DF2\u7528\u65F6\u95F4:" }), _jsx("span", { className: "ml-2 font-medium", children: formatTime(executionProgress.elapsedTime) })] }), _jsxs("div", { children: [_jsx("span", { className: "text-gray-600", children: "\u9884\u8BA1\u5269\u4F59:" }), _jsx("span", { className: "ml-2 font-medium", children: formatTime(executionProgress.estimatedTimeRemaining) })] })] }), executionProgress.currentActivity && (_jsxs("div", { className: "bg-gray-50 p-3 rounded", children: [_jsx("p", { className: "text-sm font-medium", children: "\u5F53\u524D\u6D3B\u52A8:" }), _jsx("p", { className: "text-sm text-gray-600", children: executionProgress.currentActivity })] }))] }) })] })), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u5B9E\u65F6\u6027\u80FD\u76D1\u63A7" }) }), _jsx(CardContent, { children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(LineChart, { data: performanceData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "timestamp", tickFormatter: (value) => new Date(value).toLocaleTimeString() }), _jsx(YAxis, {}), _jsx(Tooltip, { labelFormatter: (value) => new Date(value).toLocaleString() }), _jsx(Legend, {}), _jsx(Line, { type: "monotone", dataKey: "cpuUsage", stroke: "#8884d8", name: "CPU\u4F7F\u7528\u7387(%)" }), _jsx(Line, { type: "monotone", dataKey: "memoryUsage", stroke: "#82ca9d", name: "\u5185\u5B58\u4F7F\u7528\u7387(%)" }), _jsx(Line, { type: "monotone", dataKey: "fps", stroke: "#ffc658", name: "FPS" })] }) }) })] })] }));
    const renderAnalysisTab = () => (_jsx("div", { className: "space-y-6", children: evaluationResult && (_jsxs(_Fragment, { children: [_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u667A\u80FD\u8BC4\u4F30\u7ED3\u679C" }) }), _jsx(CardContent, { children: _jsxs("div", { className: "grid grid-cols-2 md:grid-cols-3 gap-4", children: [_jsxs("div", { className: "text-center", children: [_jsx("div", { className: "text-3xl font-bold text-blue-600", children: evaluationResult.overallScore }), _jsx("div", { className: "text-sm text-gray-600", children: "\u7EFC\u5408\u8BC4\u5206" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-3xl font-bold text-green-600", children: [evaluationResult.reliability, "%"] }), _jsx("div", { className: "text-sm text-gray-600", children: "\u53EF\u9760\u6027" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-3xl font-bold text-purple-600", children: [evaluationResult.efficiency, "%"] }), _jsx("div", { className: "text-sm text-gray-600", children: "\u6548\u7387" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-3xl font-bold text-orange-600", children: [evaluationResult.stability, "%"] }), _jsx("div", { className: "text-sm text-gray-600", children: "\u7A33\u5B9A\u6027" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-3xl font-bold text-cyan-600", children: [evaluationResult.userFriendliness, "%"] }), _jsx("div", { className: "text-sm text-gray-600", children: "\u7528\u6237\u53CB\u597D\u5EA6" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-3xl font-bold text-red-600", children: [evaluationResult.resourceConsumption, "%"] }), _jsx("div", { className: "text-sm text-gray-600", children: "\u8D44\u6E90\u6D88\u8017" })] })] }) })] }), evaluationResult.optimizationSuggestions.length > 0 && (_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsxs(CardTitle, { className: "flex items-center space-x-2", children: [_jsx(AlertTriangle, { className: "w-5 h-5 text-yellow-500" }), _jsx("span", { children: "\u4F18\u5316\u5EFA\u8BAE" })] }) }), _jsx(CardContent, { children: _jsx("div", { className: "space-y-3", children: evaluationResult.optimizationSuggestions.slice(0, 3).map((suggestion, index) => (_jsxs("div", { className: "border-l-4 border-yellow-500 pl-4", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h4", { className: "font-medium", children: suggestion.title }), _jsx(Badge, { variant: "outline", children: suggestion.priority })] }), _jsx("p", { className: "text-sm text-gray-600 mt-1", children: suggestion.description }), _jsxs("p", { className: "text-xs text-gray-500 mt-1", children: ["\u5F71\u54CD: ", suggestion.impact] })] }, index))) }) })] })), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u6027\u80FD\u6307\u6807\u5206\u5E03" }) }), _jsx(CardContent, { children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(PieChart, { children: [_jsx(Pie, { data: [
                                                { name: '可靠性', value: evaluationResult.reliability },
                                                { name: '效率', value: evaluationResult.efficiency },
                                                { name: '稳定性', value: evaluationResult.stability },
                                                { name: '用户友好度', value: evaluationResult.userFriendliness },
                                            ], cx: "50%", cy: "50%", labelLine: false, label: ({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`, outerRadius: 80, fill: "#8884d8", dataKey: "value", children: COLORS.map((color, index) => (_jsx(Cell, { fill: color }, `cell-${index}`))) }), _jsx(Tooltip, {})] }) }) })] })] })) }));
    const renderHistoryTab = () => (_jsxs("div", { className: "space-y-6", children: [_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u5386\u53F2\u6267\u884C\u7EDF\u8BA1" }) }), _jsx(CardContent, { children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(BarChart, { data: historicalData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "date" }), _jsx(YAxis, {}), _jsx(Tooltip, {}), _jsx(Legend, {}), _jsx(Bar, { dataKey: "successRate", fill: "#82ca9d", name: "\u6210\u529F\u7387(%)" }), _jsx(Bar, { dataKey: "avgDuration", fill: "#8884d8", name: "\u5E73\u5747\u8017\u65F6(\u5206\u949F)" })] }) }) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u6027\u80FD\u8D8B\u52BF" }) }), _jsx(CardContent, { children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(LineChart, { data: historicalData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "date" }), _jsx(YAxis, {}), _jsx(Tooltip, {}), _jsx(Legend, {}), _jsx(Line, { type: "monotone", dataKey: "avgCpuUsage", stroke: "#8884d8", name: "\u5E73\u5747CPU\u4F7F\u7528\u7387" }), _jsx(Line, { type: "monotone", dataKey: "avgMemoryUsage", stroke: "#82ca9d", name: "\u5E73\u5747\u5185\u5B58\u4F7F\u7528\u7387" }), _jsx(Line, { type: "monotone", dataKey: "avgFps", stroke: "#ffc658", name: "\u5E73\u5747FPS" })] }) }) })] })] }));
    if (isLoading) {
        return (_jsxs("div", { className: "flex items-center justify-center h-64", children: [_jsx("div", { className: "animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" }), _jsx("span", { className: "ml-2", children: "\u52A0\u8F7D\u6027\u80FD\u6570\u636E\u4E2D..." })] }));
    }
    return (_jsx("div", { className: "w-full", children: _jsxs(Tabs, { defaultValue: isExecuting ? "realtime" : "analysis", className: "w-full", children: [_jsxs(TabsList, { className: "grid w-full grid-cols-3", children: [_jsx(TabsTrigger, { value: "realtime", children: "\u5B9E\u65F6\u76D1\u63A7" }), _jsx(TabsTrigger, { value: "analysis", children: "\u667A\u80FD\u5206\u6790" }), _jsx(TabsTrigger, { value: "history", children: "\u5386\u53F2\u6570\u636E" })] }), _jsx(TabsContent, { value: "realtime", className: "mt-6", children: renderRealTimeTab() }), _jsx(TabsContent, { value: "analysis", className: "mt-6", children: renderAnalysisTab() }), _jsx(TabsContent, { value: "history", className: "mt-6", children: renderHistoryTab() })] }) }));
};
export default PerformanceDashboard;
