import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { Star, MessageSquare, ThumbsUp, Send, BarChart3, Filter } from 'lucide-react';
import { toast } from 'sonner';
const FeedbackSystem = ({ strategyId, onFeedbackSubmit }) => {
    const [feedbacks, setFeedbacks] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [sortBy, setSortBy] = useState('newest');
    // 新反馈表单状态
    const [newFeedback, setNewFeedback] = useState({
        rating: 0,
        category: 'execution',
        title: '',
        description: '',
        tags: [],
        userId: 'current-user' // 实际应用中从认证系统获取
    });
    useEffect(() => {
        loadFeedbacks();
    }, [strategyId]);
    const loadFeedbacks = async () => {
        try {
            // 模拟加载反馈数据
            const mockFeedbacks = [
                {
                    id: '1',
                    strategyId,
                    userId: 'user1',
                    rating: 4,
                    category: 'execution',
                    title: '执行效果不错，但有改进空间',
                    description: '整体执行流程比较顺畅，但在某些步骤上还可以优化时机。建议在战斗前增加状态检查。',
                    tags: ['执行流程', '时机优化'],
                    timestamp: Date.now() - 86400000,
                    status: 'reviewed',
                    helpful: 5,
                    responses: [
                        {
                            id: 'r1',
                            content: '感谢反馈！我们会在下个版本中优化战斗前的状态检查逻辑。',
                            timestamp: Date.now() - 43200000,
                            author: '开发团队'
                        }
                    ]
                },
                {
                    id: '2',
                    strategyId,
                    userId: 'user2',
                    rating: 5,
                    category: 'efficiency',
                    title: '效率很高，节省了大量时间',
                    description: '使用这个攻略后，完成任务的时间缩短了30%，非常满意！',
                    tags: ['高效率', '时间节省'],
                    timestamp: Date.now() - 172800000,
                    status: 'implemented',
                    helpful: 12
                },
                {
                    id: '3',
                    strategyId,
                    userId: 'user3',
                    rating: 3,
                    category: 'accuracy',
                    title: '准确性有待提升',
                    description: '在复杂场景下偶尔会出现识别错误，希望能提高准确性。',
                    tags: ['准确性', '复杂场景'],
                    timestamp: Date.now() - 259200000,
                    status: 'pending',
                    helpful: 3
                }
            ];
            setFeedbacks(mockFeedbacks);
        }
        catch (error) {
            console.error('加载反馈失败:', error);
        }
    };
    const handleSubmitFeedback = async () => {
        if (!newFeedback.title.trim() || !newFeedback.description.trim() || newFeedback.rating === 0) {
            toast.error('请填写完整的反馈信息');
            return;
        }
        setIsSubmitting(true);
        try {
            const feedbackData = {
                ...newFeedback,
                strategyId
            };
            // 调用回调函数
            onFeedbackSubmit?.({ ...feedbackData, status: 'pending' });
            // 添加到本地列表
            const newFeedbackItem = {
                ...feedbackData,
                id: Date.now().toString(),
                timestamp: Date.now(),
                helpful: 0,
                status: 'pending'
            };
            setFeedbacks(prev => [newFeedbackItem, ...prev]);
            // 重置表单
            setNewFeedback({
                rating: 0,
                category: 'execution',
                title: '',
                description: '',
                tags: [],
                userId: 'current-user'
            });
            toast.success('反馈提交成功！');
        }
        catch (error) {
            console.error('提交反馈失败:', error);
            toast.error('提交失败，请重试');
        }
        finally {
            setIsSubmitting(false);
        }
    };
    const handleRating = (rating) => {
        setNewFeedback(prev => ({ ...prev, rating }));
    };
    const handleTagInput = (e) => {
        if (e.key === 'Enter' && e.currentTarget.value.trim()) {
            const newTag = e.currentTarget.value.trim();
            if (!newFeedback.tags.includes(newTag)) {
                setNewFeedback(prev => ({
                    ...prev,
                    tags: [...prev.tags, newTag]
                }));
            }
            e.currentTarget.value = '';
        }
    };
    const removeTag = (tagToRemove) => {
        setNewFeedback(prev => ({
            ...prev,
            tags: prev.tags.filter(tag => tag !== tagToRemove)
        }));
    };
    const handleHelpful = (feedbackId) => {
        setFeedbacks(prev => prev.map(f => f.id === feedbackId
            ? { ...f, helpful: f.helpful + 1 }
            : f));
        toast.success('感谢您的反馈！');
    };
    const getCategoryLabel = (category) => {
        const labels = {
            execution: '执行效果',
            accuracy: '准确性',
            efficiency: '效率',
            usability: '易用性',
            other: '其他'
        };
        return labels[category] || category;
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'reviewed': return 'bg-blue-100 text-blue-800';
            case 'implemented': return 'bg-green-100 text-green-800';
            case 'rejected': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };
    const getStatusLabel = (status) => {
        const labels = {
            pending: '待处理',
            reviewed: '已查看',
            implemented: '已实现',
            rejected: '已拒绝'
        };
        return labels[status] || status;
    };
    const filteredAndSortedFeedbacks = feedbacks
        .filter(f => selectedCategory === 'all' || f.category === selectedCategory)
        .sort((a, b) => {
        switch (sortBy) {
            case 'newest': return b.timestamp - a.timestamp;
            case 'oldest': return a.timestamp - b.timestamp;
            case 'rating': return b.rating - a.rating;
            case 'helpful': return b.helpful - a.helpful;
            default: return 0;
        }
    });
    const averageRating = feedbacks.length > 0
        ? feedbacks.reduce((sum, f) => sum + f.rating, 0) / feedbacks.length
        : 0;
    const ratingDistribution = [1, 2, 3, 4, 5].map(rating => ({
        rating,
        count: feedbacks.filter(f => f.rating === rating).length,
        percentage: feedbacks.length > 0
            ? (feedbacks.filter(f => f.rating === rating).length / feedbacks.length) * 100
            : 0
    }));
    const renderStars = (rating, interactive = false, onRate) => {
        return (_jsxs("div", { className: "flex items-center space-x-1", children: [[1, 2, 3, 4, 5].map(star => (_jsx(Star, { className: `w-5 h-5 ${star <= rating
                        ? 'text-yellow-400 fill-yellow-400'
                        : 'text-gray-300'} ${interactive ? 'cursor-pointer hover:text-yellow-400' : ''}`, onClick: () => interactive && onRate?.(star) }, star))), !interactive && (_jsxs("span", { className: "ml-2 text-sm text-gray-600", children: ["(", rating, "/5)"] }))] }));
    };
    const renderSubmitTab = () => (_jsx("div", { className: "space-y-6", children: _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsxs(CardTitle, { className: "flex items-center space-x-2", children: [_jsx(MessageSquare, { className: "w-5 h-5" }), _jsx("span", { children: "\u63D0\u4EA4\u53CD\u9988" })] }) }), _jsxs(CardContent, { className: "space-y-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { children: "\u6574\u4F53\u8BC4\u5206" }), renderStars(newFeedback.rating, true, handleRating)] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { children: "\u53CD\u9988\u5206\u7C7B" }), _jsx("div", { className: "flex flex-wrap gap-2", children: ['execution', 'accuracy', 'efficiency', 'usability', 'other'].map(category => (_jsx(Button, { variant: newFeedback.category === category ? "default" : "outline", size: "sm", onClick: () => setNewFeedback(prev => ({ ...prev, category: category })), children: getCategoryLabel(category) }, category))) })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "title", children: "\u53CD\u9988\u6807\u9898" }), _jsx(Input, { id: "title", placeholder: "\u7B80\u8981\u63CF\u8FF0\u60A8\u7684\u53CD\u9988...", value: newFeedback.title, onChange: (e) => setNewFeedback(prev => ({ ...prev, title: e.target.value })) })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "description", children: "\u8BE6\u7EC6\u63CF\u8FF0" }), _jsx(Textarea, { id: "description", placeholder: "\u8BF7\u8BE6\u7EC6\u63CF\u8FF0\u60A8\u7684\u4F7F\u7528\u4F53\u9A8C\u3001\u9047\u5230\u7684\u95EE\u9898\u6216\u6539\u8FDB\u5EFA\u8BAE...", rows: 4, value: newFeedback.description, onChange: (e) => setNewFeedback(prev => ({ ...prev, description: e.target.value })) })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "tags", children: "\u6807\u7B7E (\u6309\u56DE\u8F66\u6DFB\u52A0)" }), _jsx(Input, { id: "tags", placeholder: "\u6DFB\u52A0\u76F8\u5173\u6807\u7B7E...", onKeyDown: handleTagInput }), newFeedback.tags.length > 0 && (_jsx("div", { className: "flex flex-wrap gap-2 mt-2", children: newFeedback.tags.map(tag => (_jsxs(Badge, { variant: "secondary", className: "cursor-pointer", onClick: () => removeTag(tag), children: [tag, " \u00D7"] }, tag))) }))] }), _jsxs(Button, { onClick: handleSubmitFeedback, disabled: isSubmitting, className: "w-full flex items-center space-x-2", children: [_jsx(Send, { className: "w-4 h-4" }), _jsx("span", { children: isSubmitting ? '提交中...' : '提交反馈' })] })] })] }) }));
    const renderFeedbacksTab = () => (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex flex-wrap items-center gap-4", children: [_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Filter, { className: "w-4 h-4" }), _jsx("span", { className: "text-sm font-medium", children: "\u5206\u7C7B:" }), _jsx("div", { className: "flex gap-1", children: ['all', 'execution', 'accuracy', 'efficiency', 'usability', 'other'].map(category => (_jsx(Button, { variant: selectedCategory === category ? "default" : "outline", size: "sm", onClick: () => setSelectedCategory(category), children: category === 'all' ? '全部' : getCategoryLabel(category) }, category))) })] }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("span", { className: "text-sm font-medium", children: "\u6392\u5E8F:" }), _jsx("div", { className: "flex gap-1", children: [
                                    { key: 'newest', label: '最新' },
                                    { key: 'helpful', label: '最有帮助' },
                                    { key: 'rating', label: '评分' }
                                ].map(({ key, label }) => (_jsx(Button, { variant: sortBy === key ? "default" : "outline", size: "sm", onClick: () => setSortBy(key), children: label }, key))) })] })] }), _jsxs("div", { className: "space-y-4", children: [filteredAndSortedFeedbacks.map(feedback => (_jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx("div", { className: "flex items-start justify-between", children: _jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("h3", { className: "font-medium", children: feedback.title }), _jsx(Badge, { className: getStatusColor(feedback.status), children: getStatusLabel(feedback.status) })] }), _jsxs("div", { className: "flex items-center space-x-4", children: [renderStars(feedback.rating), _jsx(Badge, { variant: "outline", children: getCategoryLabel(feedback.category) }), _jsx("span", { className: "text-sm text-gray-500", children: new Date(feedback.timestamp).toLocaleDateString() })] })] }) }) }), _jsxs(CardContent, { className: "space-y-4", children: [_jsx("p", { className: "text-gray-700", children: feedback.description }), feedback.tags.length > 0 && (_jsx("div", { className: "flex flex-wrap gap-2", children: feedback.tags.map(tag => (_jsx(Badge, { variant: "secondary", children: tag }, tag))) })), feedback.responses && feedback.responses.length > 0 && (_jsxs("div", { className: "space-y-2 border-t pt-4", children: [_jsx("h4", { className: "font-medium text-sm", children: "\u5B98\u65B9\u56DE\u590D:" }), feedback.responses.map(response => (_jsxs("div", { className: "bg-blue-50 p-3 rounded border-l-4 border-blue-500", children: [_jsx("p", { className: "text-sm", children: response.content }), _jsxs("div", { className: "flex items-center justify-between mt-2 text-xs text-gray-500", children: [_jsx("span", { children: response.author }), _jsx("span", { children: new Date(response.timestamp).toLocaleDateString() })] })] }, response.id)))] })), _jsx("div", { className: "flex items-center justify-between pt-2", children: _jsxs(Button, { variant: "ghost", size: "sm", onClick: () => handleHelpful(feedback.id), className: "flex items-center space-x-1", children: [_jsx(ThumbsUp, { className: "w-4 h-4" }), _jsxs("span", { children: ["\u6709\u5E2E\u52A9 (", feedback.helpful, ")"] })] }) })] })] }, feedback.id))), filteredAndSortedFeedbacks.length === 0 && (_jsx(Card, { children: _jsxs(CardContent, { className: "p-8 text-center", children: [_jsx(MessageSquare, { className: "w-12 h-12 text-gray-400 mx-auto mb-4" }), _jsx("h3", { className: "text-lg font-medium text-gray-600 mb-2", children: "\u6682\u65E0\u53CD\u9988" }), _jsx("p", { className: "text-gray-500", children: "\u8FD8\u6CA1\u6709\u7528\u6237\u53CD\u9988\uFF0C\u6210\u4E3A\u7B2C\u4E00\u4E2A\u5206\u4EAB\u4F53\u9A8C\u7684\u4EBA\u5427\uFF01" })] }) }))] })] }));
    const renderStatsTab = () => (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-blue-600", children: feedbacks.length }), _jsx("div", { className: "text-sm text-gray-600", children: "\u603B\u53CD\u9988\u6570" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-yellow-600", children: averageRating.toFixed(1) }), _jsx("div", { className: "text-sm text-gray-600", children: "\u5E73\u5747\u8BC4\u5206" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-green-600", children: feedbacks.filter(f => f.status === 'implemented').length }), _jsx("div", { className: "text-sm text-gray-600", children: "\u5DF2\u5B9E\u73B0" })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4 text-center", children: [_jsx("div", { className: "text-2xl font-bold text-purple-600", children: feedbacks.reduce((sum, f) => sum + f.helpful, 0) }), _jsx("div", { className: "text-sm text-gray-600", children: "\u603B\u70B9\u8D5E\u6570" })] }) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsxs(CardTitle, { className: "flex items-center space-x-2", children: [_jsx(BarChart3, { className: "w-5 h-5" }), _jsx("span", { children: "\u8BC4\u5206\u5206\u5E03" })] }) }), _jsx(CardContent, { children: _jsx("div", { className: "space-y-3", children: ratingDistribution.reverse().map(({ rating, count, percentage }) => (_jsxs("div", { className: "flex items-center space-x-4", children: [_jsxs("div", { className: "flex items-center space-x-1 w-16", children: [_jsx("span", { className: "text-sm", children: rating }), _jsx(Star, { className: "w-4 h-4 text-yellow-400 fill-yellow-400" })] }), _jsx("div", { className: "flex-1", children: _jsx(Progress, { value: percentage, className: "h-2" }) }), _jsx("div", { className: "text-sm text-gray-600 w-12", children: count })] }, rating))) }) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "\u5206\u7C7B\u7EDF\u8BA1" }) }), _jsx(CardContent, { children: _jsx("div", { className: "grid grid-cols-2 md:grid-cols-3 gap-4", children: Object.entries(feedbacks.reduce((acc, f) => {
                                acc[f.category] = (acc[f.category] || 0) + 1;
                                return acc;
                            }, {})).map(([category, count]) => (_jsxs("div", { className: "text-center p-4 bg-gray-50 rounded", children: [_jsx("div", { className: "text-xl font-bold", children: count }), _jsx("div", { className: "text-sm text-gray-600", children: getCategoryLabel(category) })] }, category))) }) })] })] }));
    return (_jsx("div", { className: "w-full", children: _jsxs(Tabs, { defaultValue: "submit", className: "w-full", children: [_jsxs(TabsList, { className: "grid w-full grid-cols-3", children: [_jsx(TabsTrigger, { value: "submit", children: "\u63D0\u4EA4\u53CD\u9988" }), _jsx(TabsTrigger, { value: "feedbacks", children: "\u67E5\u770B\u53CD\u9988" }), _jsx(TabsTrigger, { value: "stats", children: "\u7EDF\u8BA1\u5206\u6790" })] }), _jsx(TabsContent, { value: "submit", className: "mt-6", children: renderSubmitTab() }), _jsx(TabsContent, { value: "feedbacks", className: "mt-6", children: renderFeedbacksTab() }), _jsx(TabsContent, { value: "stats", className: "mt-6", children: renderStatsTab() })] }) }));
};
export default FeedbackSystem;
