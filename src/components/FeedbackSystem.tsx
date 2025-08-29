import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

import { Progress } from './ui/progress';
import { 
  Star, 
  MessageSquare, 
  ThumbsUp, 
 
  Send, 

  BarChart3,
  Filter
} from 'lucide-react';
import { toast } from 'sonner';

interface FeedbackData {
  id: string;
  strategyId: string;
  userId: string;
  rating: number;
  category: 'execution' | 'accuracy' | 'efficiency' | 'usability' | 'other';
  title: string;
  description: string;
  tags: string[];
  timestamp: number;
  status: 'pending' | 'reviewed' | 'implemented' | 'rejected';
  helpful: number; // 其他用户认为有帮助的数量
  responses?: {
    id: string;
    content: string;
    timestamp: number;
    author: string;
  }[];
}

interface FeedbackSystemProps {
  strategyId: string;
  onFeedbackSubmit?: (feedback: Omit<FeedbackData, 'id' | 'timestamp' | 'helpful' | 'responses'>) => void;
}

const FeedbackSystem: React.FC<FeedbackSystemProps> = ({ strategyId, onFeedbackSubmit }) => {
  const [feedbacks, setFeedbacks] = useState<FeedbackData[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'rating' | 'helpful'>('newest');
  
  // 新反馈表单状态
  const [newFeedback, setNewFeedback] = useState({
    rating: 0,
    category: 'execution' as const,
    title: '',
    description: '',
    tags: [] as string[],
    userId: 'current-user' // 实际应用中从认证系统获取
  });

  useEffect(() => {
    loadFeedbacks();
  }, [strategyId]);

  const loadFeedbacks = async () => {
    try {
      // 模拟加载反馈数据
      const mockFeedbacks: FeedbackData[] = [
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
    } catch (error) {
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
      const newFeedbackItem: FeedbackData = {
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
    } catch (error) {
      console.error('提交反馈失败:', error);
      toast.error('提交失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRating = (rating: number) => {
    setNewFeedback(prev => ({ ...prev, rating }));
  };

  const handleTagInput = (e: React.KeyboardEvent<HTMLInputElement>) => {
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

  const removeTag = (tagToRemove: string) => {
    setNewFeedback(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleHelpful = (feedbackId: string) => {
    setFeedbacks(prev => prev.map(f => 
      f.id === feedbackId 
        ? { ...f, helpful: f.helpful + 1 }
        : f
    ));
    toast.success('感谢您的反馈！');
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      execution: '执行效果',
      accuracy: '准确性',
      efficiency: '效率',
      usability: '易用性',
      other: '其他'
    };
    return labels[category] || category;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'reviewed': return 'bg-blue-100 text-blue-800';
      case 'implemented': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
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

  const renderStars = (rating: number, interactive = false, onRate?: (rating: number) => void) => {
    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map(star => (
          <Star
            key={star}
            className={`w-5 h-5 ${
              star <= rating 
                ? 'text-yellow-400 fill-yellow-400' 
                : 'text-gray-300'
            } ${
              interactive ? 'cursor-pointer hover:text-yellow-400' : ''
            }`}
            onClick={() => interactive && onRate?.(star)}
          />
        ))}
        {!interactive && (
          <span className="ml-2 text-sm text-gray-600">({rating}/5)</span>
        )}
      </div>
    );
  };

  const renderSubmitTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="w-5 h-5" />
            <span>提交反馈</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 评分 */}
          <div className="space-y-2">
            <Label>整体评分</Label>
            {renderStars(newFeedback.rating, true, handleRating)}
          </div>
          
          {/* 分类 */}
          <div className="space-y-2">
            <Label>反馈分类</Label>
            <div className="flex flex-wrap gap-2">
              {['execution', 'accuracy', 'efficiency', 'usability', 'other'].map(category => (
                <Button
                  key={category}
                  variant={newFeedback.category === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setNewFeedback(prev => ({ ...prev, category: category as any }))}
                >
                  {getCategoryLabel(category)}
                </Button>
              ))}
            </div>
          </div>
          
          {/* 标题 */}
          <div className="space-y-2">
            <Label htmlFor="title">反馈标题</Label>
            <Input
              id="title"
              placeholder="简要描述您的反馈..."
              value={newFeedback.title}
              onChange={(e) => setNewFeedback(prev => ({ ...prev, title: e.target.value }))}
            />
          </div>
          
          {/* 详细描述 */}
          <div className="space-y-2">
            <Label htmlFor="description">详细描述</Label>
            <Textarea
              id="description"
              placeholder="请详细描述您的使用体验、遇到的问题或改进建议..."
              rows={4}
              value={newFeedback.description}
              onChange={(e) => setNewFeedback(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
          
          {/* 标签 */}
          <div className="space-y-2">
            <Label htmlFor="tags">标签 (按回车添加)</Label>
            <Input
              id="tags"
              placeholder="添加相关标签..."
              onKeyDown={handleTagInput}
            />
            {newFeedback.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {newFeedback.tags.map(tag => (
                  <Badge 
                    key={tag} 
                    variant="secondary" 
                    className="cursor-pointer"
                    onClick={() => removeTag(tag)}
                  >
                    {tag} ×
                  </Badge>
                ))}
              </div>
            )}
          </div>
          
          {/* 提交按钮 */}
          <Button 
            onClick={handleSubmitFeedback} 
            disabled={isSubmitting}
            className="w-full flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
            <span>{isSubmitting ? '提交中...' : '提交反馈'}</span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderFeedbacksTab = () => (
    <div className="space-y-6">
      {/* 筛选和排序 */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4" />
          <span className="text-sm font-medium">分类:</span>
          <div className="flex gap-1">
            {['all', 'execution', 'accuracy', 'efficiency', 'usability', 'other'].map(category => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category === 'all' ? '全部' : getCategoryLabel(category)}
              </Button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium">排序:</span>
          <div className="flex gap-1">
            {[
              { key: 'newest', label: '最新' },
              { key: 'helpful', label: '最有帮助' },
              { key: 'rating', label: '评分' }
            ].map(({ key, label }) => (
              <Button
                key={key}
                variant={sortBy === key ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy(key as any)}
              >
                {label}
              </Button>
            ))}
          </div>
        </div>
      </div>
      
      {/* 反馈列表 */}
      <div className="space-y-4">
        {filteredAndSortedFeedbacks.map(feedback => (
          <Card key={feedback.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-medium">{feedback.title}</h3>
                    <Badge className={getStatusColor(feedback.status)}>
                      {getStatusLabel(feedback.status)}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-4">
                    {renderStars(feedback.rating)}
                    <Badge variant="outline">{getCategoryLabel(feedback.category)}</Badge>
                    <span className="text-sm text-gray-500">
                      {new Date(feedback.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <p className="text-gray-700">{feedback.description}</p>
              
              {feedback.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {feedback.tags.map(tag => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
              )}
              
              {/* 响应 */}
              {feedback.responses && feedback.responses.length > 0 && (
                <div className="space-y-2 border-t pt-4">
                  <h4 className="font-medium text-sm">官方回复:</h4>
                  {feedback.responses.map(response => (
                    <div key={response.id} className="bg-blue-50 p-3 rounded border-l-4 border-blue-500">
                      <p className="text-sm">{response.content}</p>
                      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                        <span>{response.author}</span>
                        <span>{new Date(response.timestamp).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* 操作按钮 */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleHelpful(feedback.id)}
                  className="flex items-center space-x-1"
                >
                  <ThumbsUp className="w-4 h-4" />
                  <span>有帮助 ({feedback.helpful})</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {filteredAndSortedFeedbacks.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center">
              <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-600 mb-2">暂无反馈</h3>
              <p className="text-gray-500">还没有用户反馈，成为第一个分享体验的人吧！</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );

  const renderStatsTab = () => (
    <div className="space-y-6">
      {/* 总体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{feedbacks.length}</div>
            <div className="text-sm text-gray-600">总反馈数</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-yellow-600">{averageRating.toFixed(1)}</div>
            <div className="text-sm text-gray-600">平均评分</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {feedbacks.filter(f => f.status === 'implemented').length}
            </div>
            <div className="text-sm text-gray-600">已实现</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {feedbacks.reduce((sum, f) => sum + f.helpful, 0)}
            </div>
            <div className="text-sm text-gray-600">总点赞数</div>
          </CardContent>
        </Card>
      </div>
      
      {/* 评分分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5" />
            <span>评分分布</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {ratingDistribution.reverse().map(({ rating, count, percentage }) => (
              <div key={rating} className="flex items-center space-x-4">
                <div className="flex items-center space-x-1 w-16">
                  <span className="text-sm">{rating}</span>
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                </div>
                <div className="flex-1">
                  <Progress value={percentage} className="h-2" />
                </div>
                <div className="text-sm text-gray-600 w-12">{count}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* 分类统计 */}
      <Card>
        <CardHeader>
          <CardTitle>分类统计</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(
              feedbacks.reduce((acc, f) => {
                acc[f.category] = (acc[f.category] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).map(([category, count]) => (
              <div key={category} className="text-center p-4 bg-gray-50 rounded">
                <div className="text-xl font-bold">{count}</div>
                <div className="text-sm text-gray-600">{getCategoryLabel(category)}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="w-full">
      <Tabs defaultValue="submit" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="submit">提交反馈</TabsTrigger>
          <TabsTrigger value="feedbacks">查看反馈</TabsTrigger>
          <TabsTrigger value="stats">统计分析</TabsTrigger>
        </TabsList>
        
        <TabsContent value="submit" className="mt-6">
          {renderSubmitTab()}
        </TabsContent>
        
        <TabsContent value="feedbacks" className="mt-6">
          {renderFeedbacksTab()}
        </TabsContent>
        
        <TabsContent value="stats" className="mt-6">
          {renderStatsTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FeedbackSystem;