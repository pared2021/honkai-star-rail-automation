import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { 
  Lightbulb, 
  TrendingUp, 
  Clock, 
  Zap, 
  Shield, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  ArrowRight,
  ThumbsUp,
  ThumbsDown,
  Star
} from 'lucide-react';
import IntelligentEvaluator from '../services/IntelligentEvaluator';
import PerformanceDataCollector from '../services/PerformanceDataCollector';
import { DatabaseService } from '../services/DatabaseService';
import type { OptimizationSuggestion, IntelligentEvaluationResult } from '../services/IntelligentEvaluator';

interface OptimizationSuggestionsProps {
  strategyId: string;
  evaluationResult?: IntelligentEvaluationResult;
  onApplySuggestion?: (suggestionId: string) => void;
  onFeedback?: (suggestionId: string, helpful: boolean) => void;
}

interface SuggestionWithFeedback extends OptimizationSuggestion {
  userFeedback?: {
    helpful: boolean;
    applied: boolean;
    timestamp: number;
  };
}

const OptimizationSuggestions: React.FC<OptimizationSuggestionsProps> = ({
  strategyId,
  evaluationResult,
  onApplySuggestion,
  onFeedback
}) => {
  const [suggestions, setSuggestions] = useState<SuggestionWithFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [appliedSuggestions, setAppliedSuggestions] = useState<Set<string>>(new Set());

  const dbService = new DatabaseService();
  const performanceCollector = new PerformanceDataCollector(dbService);
  const intelligentEvaluator = new IntelligentEvaluator(performanceCollector, dbService);

  useEffect(() => {
    if (evaluationResult?.optimizationSuggestions) {
      setSuggestions(evaluationResult.optimizationSuggestions.map(s => ({
        ...s,
        userFeedback: undefined
      })));
    } else {
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
    } catch (error) {
      console.error('加载优化建议失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplySuggestion = async (suggestionId: string) => {
    try {
      setAppliedSuggestions(prev => new Set([...prev, suggestionId]));
      
      // 更新建议状态
      setSuggestions(prev => prev.map(s => 
        s.id === suggestionId 
          ? { ...s, userFeedback: { ...s.userFeedback, applied: true, timestamp: Date.now() } }
          : s
      ));
      
      onApplySuggestion?.(suggestionId);
    } catch (error) {
      console.error('应用建议失败:', error);
      setAppliedSuggestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestionId);
        return newSet;
      });
    }
  };

  const handleFeedback = (suggestionId: string, helpful: boolean) => {
    setSuggestions(prev => prev.map(s => 
      s.id === suggestionId 
        ? { 
            ...s, 
            userFeedback: { 
              ...s.userFeedback, 
              helpful, 
              timestamp: Date.now() 
            } 
          }
        : s
    ));
    
    onFeedback?.(suggestionId, helpful);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'performance': return <Zap className="w-4 h-4" />;
      case 'reliability': return <Shield className="w-4 h-4" />;
      case 'efficiency': return <TrendingUp className="w-4 h-4" />;
      case 'timing': return <Clock className="w-4 h-4" />;
      case 'accuracy': return <Target className="w-4 h-4" />;
      default: return <Lightbulb className="w-4 h-4" />;
    }
  };

  const getImpactLevel = (impact: string) => {
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
  const categoryLabels: Record<string, string> = {
    all: '全部',
    performance: '性能优化',
    reliability: '可靠性',
    efficiency: '效率提升',
    timing: '时机优化',
    accuracy: '准确性'
  };

  const renderSuggestionCard = (suggestion: SuggestionWithFeedback) => {
    const impactLevel = getImpactLevel(suggestion.impact);
    const isApplied = appliedSuggestions.has(suggestion.id) || suggestion.userFeedback?.applied;
    
    return (
      <Card key={suggestion.id} className={`transition-all duration-200 hover:shadow-md ${
        isApplied ? 'bg-green-50 border-green-200' : ''
      }`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              {getCategoryIcon(suggestion.category)}
              <CardTitle className="text-lg">{suggestion.title}</CardTitle>
              {isApplied && <CheckCircle className="w-5 h-5 text-green-500" />}
            </div>
            <div className="flex items-center space-x-2">
              <Badge className={getPriorityColor(suggestion.priority)}>
                {suggestion.priority === 'high' ? '高优先级' : 
                 suggestion.priority === 'medium' ? '中优先级' : '低优先级'}
              </Badge>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <p className="text-gray-700">{suggestion.description}</p>
          
          {/* 影响程度 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>预期改善程度</span>
              <span className={impactLevel.color}>{suggestion.impact}</span>
            </div>
            <Progress value={impactLevel.value} className="h-2" />
          </div>
          
          {/* 实施步骤 */}
          {suggestion.steps && suggestion.steps.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-sm">实施步骤:</h4>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                {suggestion.steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
          )}
          
          {/* 预期效果 */}
          {suggestion.expectedImprovement && (
            <Alert>
              <TrendingUp className="h-4 w-4" />
              <AlertDescription>
                <strong>预期效果:</strong> {suggestion.expectedImprovement}
              </AlertDescription>
            </Alert>
          )}
          
          {/* 操作按钮 */}
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center space-x-2">
              {!isApplied ? (
                <Button 
                  onClick={() => handleApplySuggestion(suggestion.id)}
                  size="sm"
                  className="flex items-center space-x-1"
                >
                  <span>应用建议</span>
                  <ArrowRight className="w-3 h-3" />
                </Button>
              ) : (
                <Badge variant="outline" className="text-green-600 border-green-600">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  已应用
                </Badge>
              )}
            </div>
            
            {/* 反馈按钮 */}
            <div className="flex items-center space-x-1">
              <span className="text-xs text-gray-500">有帮助吗?</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFeedback(suggestion.id, true)}
                className={`p-1 h-6 w-6 ${
                  suggestion.userFeedback?.helpful === true ? 'text-green-600' : 'text-gray-400'
                }`}
              >
                <ThumbsUp className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFeedback(suggestion.id, false)}
                className={`p-1 h-6 w-6 ${
                  suggestion.userFeedback?.helpful === false ? 'text-red-600' : 'text-gray-400'
                }`}
              >
                <ThumbsDown className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderSummaryTab = () => {
    const highPrioritySuggestions = suggestions.filter(s => s.priority === 'high');
    const appliedCount = suggestions.filter(s => appliedSuggestions.has(s.id) || s.userFeedback?.applied).length;
    const helpfulCount = suggestions.filter(s => s.userFeedback?.helpful === true).length;
    
    return (
      <div className="space-y-6">
        {/* 统计概览 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{suggestions.length}</div>
              <div className="text-sm text-gray-600">总建议数</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-red-600">{highPrioritySuggestions.length}</div>
              <div className="text-sm text-gray-600">高优先级</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{appliedCount}</div>
              <div className="text-sm text-gray-600">已应用</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">{helpfulCount}</div>
              <div className="text-sm text-gray-600">有帮助</div>
            </CardContent>
          </Card>
        </div>
        
        {/* 高优先级建议 */}
        {highPrioritySuggestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <span>高优先级建议</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {highPrioritySuggestions.slice(0, 3).map(suggestion => (
                  <div key={suggestion.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex-1">
                      <h4 className="font-medium">{suggestion.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                    </div>
                    <Button 
                      size="sm" 
                      onClick={() => handleApplySuggestion(suggestion.id)}
                      disabled={appliedSuggestions.has(suggestion.id)}
                    >
                      {appliedSuggestions.has(suggestion.id) ? '已应用' : '立即应用'}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* 分类统计 */}
        <Card>
          <CardHeader>
            <CardTitle>分类统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(
                suggestions.reduce((acc, s) => {
                  acc[s.category] = (acc[s.category] || 0) + 1;
                  return acc;
                }, {} as Record<string, number>)
              ).map(([category, count]) => (
                <div key={category} className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                  {getCategoryIcon(category)}
                  <div>
                    <div className="font-medium">{categoryLabels[category] || category}</div>
                    <div className="text-sm text-gray-600">{count} 个建议</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">生成优化建议中...</span>
      </div>
    );
  }

  return (
    <div className="w-full">
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="summary">概览</TabsTrigger>
          <TabsTrigger value="detailed">详细建议</TabsTrigger>
        </TabsList>
        
        <TabsContent value="summary" className="mt-6">
          {renderSummaryTab()}
        </TabsContent>
        
        <TabsContent value="detailed" className="mt-6">
          <div className="space-y-6">
            {/* 分类筛选 */}
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                  className="flex items-center space-x-1"
                >
                  {category !== 'all' && getCategoryIcon(category)}
                  <span>{categoryLabels[category] || category}</span>
                </Button>
              ))}
            </div>
            
            {/* 建议列表 */}
            <div className="space-y-4">
              {filteredSuggestions.length > 0 ? (
                filteredSuggestions.map(renderSuggestionCard)
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">暂无优化建议</h3>
                    <p className="text-gray-500">当前攻略表现良好，暂时没有需要优化的地方。</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OptimizationSuggestions;