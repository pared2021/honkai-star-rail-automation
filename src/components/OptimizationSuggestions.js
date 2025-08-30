import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { Lightbulb, TrendingUp, Clock, Zap, Shield, Target, AlertTriangle, CheckCircle, ArrowRight, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import IntelligentEvaluator from '../services/IntelligentEvaluator';
import PerformanceDataCollector from '../services/PerformanceDataCollector';
import { DatabaseService } from '../services/DatabaseService';
const OptimizationSuggestions = ({ strategyId, evaluationResult, onApplySuggestion, onFeedback }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [appliedSuggestions, setAppliedSuggestions] = useState(new Set());
    const dbService = new DatabaseService();
    const performanceCollector = new PerformanceDataCollector(dbService);
    const intelligentEvaluator = new IntelligentEvaluator(performanceCollector, dbService);
    useEffect(() => {
        if (evaluationResult?.optimizationSuggestions) {
            setSuggestions(evaluationResult.optimizationSuggestions.map(s => ({
                ...s,
                userFeedback: undefined
            })));
        }
        else {
            loadSuggestions();
        }
    }, [strategyId, evaluationResult]);
    const loadSuggestions = async () => {
        setIsLoading(true);
        try {
            const result = await intelligentEvaluator.evaluateStrategy(strategyId);
            setSuggestions(result.optimizationSuggestions.map(s => ({
                ...s,
                userFeedback: undefined
            })));
        }
        catch (error) {
            console.error('加载优化建议失败:', error);
        }
        finally {
            setIsLoading(false);
        }
    };
    const handleApplySuggestion = async (suggestionId) => {
        try {
            setAppliedSuggestions(prev => new Set([...prev, suggestionId]));
            // 更新建议状态
            setSuggestions(prev => prev.map(s => s.id === suggestionId
                ? { ...s, userFeedback: { ...s.userFeedback, applied: true, timestamp: Date.now() } }
                : s));
            onApplySuggestion?.(suggestionId);
        }
        catch (error) {
            console.error('应用建议失败:', error);
            setAppliedSuggestions(prev => {
                const newSet = new Set(prev);
                newSet.delete(suggestionId);
                return newSet;
            });
        }
    };
    const handleFeedback = (suggestionId, helpful) => {
        setSuggestions(prev => prev.map(s => s.id === suggestionId
            ? {
                ...s,
                userFeedback: {
                    ...s.userFeedback,
                    helpful,
                    timestamp: Date.now()
                }
            }
            : s));
        onFeedback?.(suggestionId, helpful);
    };
    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800 border-red-200';
            case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'low': return 'bg-green-100 text-green-800 border-green-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };
    const getCategoryIcon = (category) => {
        switch (category) {
            case 'performance': return _jsx(Zap, { className: "w-4 h-4" });
            case 'reliability': return _jsx(Shield, { className: "w-4 h-4" });
            case 'efficiency': return _jsx(TrendingUp, { className: "w-4 h-4" });
            case 'timing': return _jsx(Clock, { className: "w-4 h-4" });
            case 'accuracy': return _jsx(Target, { className: "w-4 h-4" });
            default: return _jsx(Lightbulb, { className: "w-4 h-4" });
        }
    };
    const getImpactLevel = (impact) => {
        switch (impact) {
            case 'high': return { value: 80, color: 'text-red-600' };
            case 'medium': return { value: 50, color: 'text-yellow-600' };
            case 'low': return { value: 20, color: 'text-green-600' };
            default: return { value: 0, color: 'text-gray-600' };
        }
    };
    const filteredSuggestions = selectedCategory === 'all'
        ? suggestions
        : suggestions.filter(s => s.category === selectedCategory);
    const categories = ['all', ...Array.from(new Set(suggestions.map(s => s.category)))];
    const categoryLabels = {
        all: '全部',
        performance: '性能优化',
        reliability: '可靠性',
        efficiency: '效率提升',
        timing: '时机优化',
        accuracy: '准确性'
    };
    const renderSuggestionCard = (suggestion) => {
        const impactLevel = getImpactLevel(suggestion.impact);
        const isApplied = appliedSuggestions.has(suggestion.id) || suggestion.userFeedback?.applied;
        return (_jsxs(Card, { className: `transition-all duration-200 hover:shadow-md ${isApplied ? 'bg-green-50 border-green-200' : ''}`, children: [_jsx(CardHeader, { className: "pb-3", children: _jsxs("div", { className: "flex items-start justify-between", children: [_jsxs("div", { className: "flex items-center space-x-2", children: [getCategoryIcon(suggestion.category), _jsx(CardTitle, { className: "text-lg", children: suggestion.title }), isApplied && _jsx(CheckCircle, { className: "w-5 h-5 text-green-500" })] }), _jsx("div", { className: "flex items-center space-x-2", children: _jsx(Badge, { className: getPriorityColor(suggestion.priority), children: suggestion.priority === 'high' ? '高优先级' :
                                        suggestion.priority === 'medium' ? '中优先级' : '低优先级' }) })] }) }), _jsxs(CardContent, { className: "space-y-4", children: [_jsx("p", { className: "text-gray-700", children: suggestion.description }), _jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { children: "\u9884\u671F\u6539\u5584\u7A0B\u5EA6" }), _jsx("span", { className: impactLevel.color, children: suggestion.impact })] }), _jsx(Progress, { value: impactLevel.value, className: "h-2" })] }), suggestion.steps && suggestion.steps.length > 0 && (_jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium text-sm", children: "\u5B9E\u65BD\u6B65\u9AA4:" }), _jsx("ol", { className: "list-decimal list-inside space-y-1 text-sm text-gray-600", children: suggestion.steps.map((step, index) => (_jsx("li", { children: step }, index))) })] })), suggestion.expectedImprovement && (_jsxs(Alert, { children: [_jsx(TrendingUp, { className: "h-4 w-4" }), _jsxs(AlertDescription, { children: [_jsx("strong", { children: "\u9884\u671F\u6548\u679C:" }), " ", suggestion.expectedImprovement] })] })), _jsxs("div", { className: "flex items-center justify-between pt-2", children: [_jsx("div", { className: "flex items-center space-x-2", children: !isApplied ? (_jsxs(Button, { onClick: () => handleApplySuggestion(suggestion.id), size: "sm", className: "flex items-center space-x-1", children: [_jsx("span", { children: "\u5E94\u7528\u5EFA\u8BAE" }), _jsx(ArrowRight, { className: "w-3 h-3" })] })) : (_jsxs(Badge, { variant: "outline", className: "text-green-600 border-green-600", children: [_jsx(CheckCircle, { className: "w-3 h-3 mr-1" }), "\u5DF2\u5E94\u7528"] })) }), _jsxs("div", { className: "flex items-center space-x-1", children: [_jsx("span", { className: "text-xs text-gray-500", children: "\u6709\u5E2E\u52A9\u5417?" }), _jsx(Button, { variant: "ghost", size: "sm", onClick: () => handleFeedback(suggestion.id, true), className: `p-1 h-6 w-6 ${suggestion.userFeedback?.helpful === true ? 'text-green-600' : 'text-gray-400'}`, children: _jsx(ThumbsUp, { className: "w-3 h-3" }) }), _jsx(Button, { variant: "ghost", size: "sm", onClick: () => handleFeedback(suggestion.id, false), className: `p-1 h-6 w-6 ${suggestion.userFeedback?.helpful === false ? 'text-red-600' : 'text-gray-400'}`, children: _jsx(ThumbsDown, { className: "w-3 h-3" }) })] })] })] })] }, suggestion.id));
    };
    const renderSummaryTab = () => {
        const highPrioritySuggestions = suggestions.filter(s => s.priority === 'high');
        const appliedCount = suggestions.filter(s => appliedSuggestions.has(s.id) || s.userFeedback?.applied).length;
        const helpfulCount = suggestions.filter(s => s.userFeedback?.helpful === true).length;
        return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-blue-600", children: suggestions.length }), _jsx("div", { className: "text-sm text-gray-600", children: "\u603B\u5EFA\u8BAE\u6570" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-red-600", children: highPrioritySuggestions.length }), _jsx("div", { className: "text-sm text-gray-600", children: "\u9AD8\u4F18\u5148\u7EA7" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-green-600", children: appliedCount }), _jsx("div", { className: "text-sm text-gray-600", children: "\u5DF2\u5E94\u7528" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-purple-600", children: helpfulCount }), _jsx("div", { className: "text-sm text-gray-600", children: "\u6709\u5E2E\u52A9" })] }) })] }), highPrioritySuggestions.length > 0 && (_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsxs(CardTitle, { className: "flex items-center space-x-2", children: [_jsx(AlertTriangle, { className: "w-5 h-5 text-red-500" }), _jsx("span", { children: "\u9AD8\u4F18\u5148\u7EA7\u5EFA\u8BAE" })] }) }), _jsx(CardContent, { children: _jsx("div", { className: "space-y-3", children: highPrioritySuggestions.slice(0, 3).map(suggestion => (_jsxs("div", { className: "flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200", children: [_jsxs("div", { className: "flex-1", children: [_jsx("h4", { className: "font-medium", children: suggestion.title }), _jsx("p", { className: "text-sm text-gray-600 mt-1", children: suggestion.description })] }), _jsx(Button, { size: "sm", onClick: () => handleApplySuggestion(suggestion.id), disabled: appliedSuggestions.has(suggestion.id), children: appliedSuggestions.has(suggestion.id) ? '已应用' : '立即应用' })] }, suggestion.id))) }) })] })), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u5206\u7C7B\u7EDF\u8BA1" }) }), _jsx(CardContent, { children: _jsx("div", { className: "grid grid-cols-2 md:grid-cols-3 gap-4", children: Object.entries(suggestions.reduce((acc, s) => {
                                    acc[s.category] = (acc[s.category] || 0) + 1;
                                    return acc;
                                }, {})).map(([category, count]) => (_jsxs("div", { className: "flex items-center space-x-2 p-3 bg-gray-50 rounded", children: [getCategoryIcon(category), _jsxs("div", { children: [_jsx("div", { className: "font-medium", children: categoryLabels[category] || category }), _jsxs("div", { className: "text-sm text-gray-600", children: [count, " \u4E2A\u5EFA\u8BAE"] })] })] }, category))) }) })] })] }));
    };
    if (isLoading) {
        return (_jsxs("div", { className: "flex items-center justify-center h-64", children: [_jsx("div", { className: "animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" }), _jsx("span", { className: "ml-2", children: "\u751F\u6210\u4F18\u5316\u5EFA\u8BAE\u4E2D..." })] }));
    }
    return (_jsx("div", { className: "w-full", children: _jsxs(Tabs, { defaultValue: "summary", className: "w-full", children: [_jsxs(TabsList, { className: "grid w-full grid-cols-2", children: [_jsx(TabsTrigger, { value: "summary", children: "\u6982\u89C8" }), _jsx(TabsTrigger, { value: "detailed", children: "\u8BE6\u7EC6\u5EFA\u8BAE" })] }), _jsx(TabsContent, { value: "summary", className: "mt-6", children: renderSummaryTab() }), _jsx(TabsContent, { value: "detailed", className: "mt-6", children: _jsxs("div", { className: "space-y-6", children: [_jsx("div", { className: "flex flex-wrap gap-2", children: categories.map(category => (_jsxs(Button, { variant: selectedCategory === category ? "default" : "outline", size: "sm", onClick: () => setSelectedCategory(category), className: "flex items-center space-x-1", children: [category !== 'all' && getCategoryIcon(category), _jsx("span", { children: categoryLabels[category] || category })] }, category))) }), _jsx("div", { className: "space-y-4", children: filteredSuggestions.length > 0 ? (filteredSuggestions.map(renderSuggestionCard)) : (_jsx(Card, { children: _jsxs(CardContent, { className: "p-8 text-center", children: [_jsx(Star, { className: "w-12 h-12 text-gray-400 mx-auto mb-4" }), _jsx("h3", { className: "text-lg font-medium text-gray-600 mb-2", children: "\u6682\u65E0\u4F18\u5316\u5EFA\u8BAE" }), _jsx("p", { className: "text-gray-500", children: "\u5F53\u524D\u653B\u7565\u8868\u73B0\u826F\u597D\uFF0C\u6682\u65F6\u6CA1\u6709\u9700\u8981\u4F18\u5316\u7684\u5730\u65B9\u3002" })] }) })) })] }) })] }) }));
};
export default OptimizationSuggestions;
