import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { Activity, Clock, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';
import PerformanceDataCollector from '../services/PerformanceDataCollector';
import ExecutionTracker from '../services/ExecutionTracker';
import IntelligentEvaluator from '../services/IntelligentEvaluator';
import { DatabaseService } from '../services/DatabaseService';
import type { RealTimePerformanceData, StrategyExecutionSession } from '../services/PerformanceDataCollector';
import type { ExecutionProgress } from '../services/ExecutionTracker';
import type { IntelligentEvaluationResult } from '../services/IntelligentEvaluator';

interface PerformanceDashboardProps {
  strategyId: string;
  isExecuting?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ strategyId, isExecuting = false }) => {
  const [performanceData, setPerformanceData] = useState<RealTimePerformanceData[]>([]);
  const [executionProgress, setExecutionProgress] = useState<ExecutionProgress | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<IntelligentEvaluationResult | null>(null);
  const [activeSession, setActiveSession] = useState<StrategyExecutionSession | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const dbService = new DatabaseService();
  const performanceCollector = new PerformanceDataCollector(dbService);
  const intelligentEvaluator = new IntelligentEvaluator(performanceCollector, dbService);
  const executionTracker = new ExecutionTracker(performanceCollector, intelligentEvaluator, dbService);

  useEffect(() => {
    if (isExecuting) {
      startRealTimeMonitoring();
    } else {
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
    } catch (error) {
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
    } catch (error) {
      console.error('加载历史数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'running': return 'text-blue-500';
      case 'paused': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <XCircle className="w-4 h-4" />;
      case 'running': return <Activity className="w-4 h-4 animate-pulse" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const renderRealTimeTab = () => (
    <div className="space-y-6">
      {/* 实时状态卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">CPU使用率</p>
                <p className="text-lg font-semibold">
                  {performanceData[performanceData.length - 1]?.cpuUsage?.toFixed(1) || 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">内存使用</p>
                <p className="text-lg font-semibold">
                  {performanceData[performanceData.length - 1]?.memoryUsage?.toFixed(1) || 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600">FPS</p>
                <p className="text-lg font-semibold">
                  {performanceData[performanceData.length - 1]?.fps || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Wifi className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm text-gray-600">网络延迟</p>
                <p className="text-lg font-semibold">
                  {performanceData[performanceData.length - 1]?.networkLatency || 0}ms
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 执行进度 */}
      {executionProgress && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {getStatusIcon(executionProgress.status)}
              <span>执行进度</span>
              <Badge className={getStatusColor(executionProgress.status)}>
                {executionProgress.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>总体进度</span>
                  <span>{executionProgress.completedSteps}/{executionProgress.totalSteps}</span>
                </div>
                <Progress value={(executionProgress.completedSteps / executionProgress.totalSteps) * 100} />
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">已用时间:</span>
                  <span className="ml-2 font-medium">{formatTime(executionProgress.elapsedTime)}</span>
                </div>
                <div>
                  <span className="text-gray-600">预计剩余:</span>
                  <span className="ml-2 font-medium">{formatTime(executionProgress.estimatedTimeRemaining)}</span>
                </div>
              </div>
              
              {executionProgress.currentActivity && (
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm font-medium">当前活动:</p>
                  <p className="text-sm text-gray-600">{executionProgress.currentActivity}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 实时性能图表 */}
      <Card>
        <CardHeader>
          <CardTitle>实时性能监控</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
              <YAxis />
              <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} />
              <Legend />
              <Line type="monotone" dataKey="cpuUsage" stroke="#8884d8" name="CPU使用率(%)" />
              <Line type="monotone" dataKey="memoryUsage" stroke="#82ca9d" name="内存使用率(%)" />
              <Line type="monotone" dataKey="fps" stroke="#ffc658" name="FPS" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );

  const renderAnalysisTab = () => (
    <div className="space-y-6">
      {evaluationResult && (
        <>
          {/* 综合评分 */}
          <Card>
            <CardHeader>
              <CardTitle>智能评估结果</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{evaluationResult.overallScore}</div>
                  <div className="text-sm text-gray-600">综合评分</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{evaluationResult.reliability}%</div>
                  <div className="text-sm text-gray-600">可靠性</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">{evaluationResult.efficiency}%</div>
                  <div className="text-sm text-gray-600">效率</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">{evaluationResult.stability}%</div>
                  <div className="text-sm text-gray-600">稳定性</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-cyan-600">{evaluationResult.userFriendliness}%</div>
                  <div className="text-sm text-gray-600">用户友好度</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">{evaluationResult.resourceConsumption}%</div>
                  <div className="text-sm text-gray-600">资源消耗</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 优化建议 */}
          {evaluationResult.optimizationSuggestions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  <span>优化建议</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {evaluationResult.optimizationSuggestions.slice(0, 3).map((suggestion, index) => (
                    <div key={index} className="border-l-4 border-yellow-500 pl-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{suggestion.title}</h4>
                        <Badge variant="outline">{suggestion.priority}</Badge>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                      <p className="text-xs text-gray-500 mt-1">影响: {suggestion.impact}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 性能指标图表 */}
          <Card>
            <CardHeader>
              <CardTitle>性能指标分布</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: '可靠性', value: evaluationResult.reliability },
                      { name: '效率', value: evaluationResult.efficiency },
                      { name: '稳定性', value: evaluationResult.stability },
                      { name: '用户友好度', value: evaluationResult.userFriendliness },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const renderHistoryTab = () => (
    <div className="space-y-6">
      {/* 历史执行统计 */}
      <Card>
        <CardHeader>
          <CardTitle>历史执行统计</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="successRate" fill="#82ca9d" name="成功率(%)" />
              <Bar dataKey="avgDuration" fill="#8884d8" name="平均耗时(分钟)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 趋势分析 */}
      <Card>
        <CardHeader>
          <CardTitle>性能趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="avgCpuUsage" stroke="#8884d8" name="平均CPU使用率" />
              <Line type="monotone" dataKey="avgMemoryUsage" stroke="#82ca9d" name="平均内存使用率" />
              <Line type="monotone" dataKey="avgFps" stroke="#ffc658" name="平均FPS" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">加载性能数据中...</span>
      </div>
    );
  }

  return (
    <div className="w-full">
      <Tabs defaultValue={isExecuting ? "realtime" : "analysis"} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="realtime">实时监控</TabsTrigger>
          <TabsTrigger value="analysis">智能分析</TabsTrigger>
          <TabsTrigger value="history">历史数据</TabsTrigger>
        </TabsList>
        
        <TabsContent value="realtime" className="mt-6">
          {renderRealTimeTab()}
        </TabsContent>
        
        <TabsContent value="analysis" className="mt-6">
          {renderAnalysisTab()}
        </TabsContent>
        
        <TabsContent value="history" className="mt-6">
          {renderHistoryTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PerformanceDashboard;