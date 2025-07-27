import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import { Progress } from '../ui/progress';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import { 
  Activity, 
  TrendingUp, 
  Calendar,
  AlertTriangle,
  Zap,
  BarChart3,
  Download,
  Filter,
  Clock,
  DollarSign
} from 'lucide-react';
import { apiService } from '../../services/api';
import { TokenUsageChart } from './TokenUsageChart';

interface UsageStats {
  total_tokens_used: number;
  tokens_remaining: number | string;
  usage_percentage: number;
  current_plan: {
    id: number;
    name: string;
    token_limit: number;
    price: string;
    plan_type: string;
  };
  usage_by_type: Record<string, number>;
  daily_usage: Array<{ day: string; tokens: number; requests: number }>;
  weekly_usage: Array<{ day: string; tokens: number; requests: number }>;
  top_usage_types: Array<{ usage_type: string; tokens: number; count: number }>;
  monthly_cost: string;
  average_response_time_ms: number;
  period_start: string;
  period_end: string;
}

interface UsageHistoryItem {
  id: number;
  usage_type: string;
  tokens_used: number;
  prompt_tokens: number;
  completion_tokens: number;
  operation_description: string;
  response_time_ms: number | null;
  success: boolean;
  error_message: string;
  cost_dollars: number;
  created_at: string;
  project_name: string | null;
}

interface UsageAnalyticsDashboardProps {
  onUpgradeClick?: () => void;
}

export const UsageAnalyticsDashboard: React.FC<UsageAnalyticsDashboardProps> = ({ onUpgradeClick }) => {
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [usageHistory, setUsageHistory] = useState<UsageHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [dateFilter, setDateFilter] = useState({
    start_date: '',
    end_date: '',
    usage_type: ''
  });

  useEffect(() => {
    fetchUsageStats();
    fetchUsageHistory();
  }, []);

  const fetchUsageStats = async () => {
    try {
      setLoading(true);
      const data = await apiService.getUsageAnalyticsDashboard();
      setUsageStats(data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load usage statistics');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsageHistory = async () => {
    try {
      const params: any = {};
      if (dateFilter.start_date) params.start_date = dateFilter.start_date;
      if (dateFilter.end_date) params.end_date = dateFilter.end_date;
      if (dateFilter.usage_type) params.usage_type = dateFilter.usage_type;

      const data = await apiService.getUsageHistory(params);
      setUsageHistory(data.results || []);
    } catch (err: any) {
      console.error('Failed to load usage history:', err);
    }
  };

  const exportUsageData = async () => {
    try {
      setExportLoading(true);
      const params: any = {};
      if (dateFilter.start_date) params.start_date = dateFilter.start_date;
      if (dateFilter.end_date) params.end_date = dateFilter.end_date;

      const response = await apiService.exportUsageData(params);

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `usage_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export usage data');
    } finally {
      setExportLoading(false);
    }
  };

  const formatTokenCount = (tokens: number | string): string => {
    if (typeof tokens === 'string') return tokens;
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
    return tokens.toString();
  };

  const formatCurrency = (amount: string | number): string => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  const getUsageTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      ai_generation: 'bg-blue-500',
      chat_message: 'bg-green-500',
      error_fix: 'bg-red-500',
      file_analysis: 'bg-purple-500',
      project_planning: 'bg-orange-500',
      code_review: 'bg-indigo-500'
    };
    return colors[type] || 'bg-gray-500';
  };

  const getUsageTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      ai_generation: 'AI Generation',
      chat_message: 'Chat Messages',
      error_fix: 'Error Fixes',
      file_analysis: 'File Analysis',
      project_planning: 'Project Planning',
      code_review: 'Code Review'
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-300 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-300 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-300 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-center space-x-2 text-red-700">
            <AlertTriangle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        </Card>
      </div>
    );
  }

  if (!usageStats) return null;

  const isNearLimit = usageStats.usage_percentage >= 80;
  const isAtLimit = usageStats.usage_percentage >= 100;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Usage Analytics</h1>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowDetails(!showDetails)}
            variant="outline"
            size="sm"
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            {showDetails ? 'Hide Details' : 'Show Details'}
          </Button>
          <Button
            onClick={exportUsageData}
            variant="outline"
            size="sm"
            disabled={exportLoading}
          >
            <Download className="h-4 w-4 mr-2" />
            {exportLoading ? 'Exporting...' : 'Export Data'}
          </Button>
        </div>
      </div>

      {/* Usage Alert */}
      {isNearLimit && (
        <Card className={`border-2 ${isAtLimit ? 'border-red-500 bg-red-50' : 'border-yellow-500 bg-yellow-50'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <AlertTriangle className={`h-6 w-6 ${isAtLimit ? 'text-red-600' : 'text-yellow-600'}`} />
              <div>
                <h3 className={`font-semibold ${isAtLimit ? 'text-red-800' : 'text-yellow-800'}`}>
                  {isAtLimit ? 'Token Limit Reached' : 'Approaching Token Limit'}
                </h3>
                <p className={`text-sm ${isAtLimit ? 'text-red-600' : 'text-yellow-600'}`}>
                  {isAtLimit
                    ? 'You have reached your monthly token limit. Upgrade your plan to continue using AI features.'
                    : `You've used ${usageStats.usage_percentage.toFixed(1)}% of your monthly tokens.`
                  }
                </p>
              </div>
            </div>
            {onUpgradeClick && (
              <Button onClick={onUpgradeClick} size="sm">
                Upgrade Plan
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Token Usage */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tokens Used</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatTokenCount(usageStats.total_tokens_used)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                of {typeof usageStats.tokens_remaining === 'number' 
                  ? formatTokenCount(usageStats.total_tokens_used + usageStats.tokens_remaining)
                  : usageStats.tokens_remaining
                }
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Zap className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4">
            <Progress 
              value={Math.min(usageStats.usage_percentage, 100)} 
              className="h-2"
              color={isAtLimit ? 'red' : isNearLimit ? 'yellow' : 'blue'}
            />
            <p className="text-xs text-gray-500 mt-1">
              {usageStats.usage_percentage.toFixed(1)}% used this period
            </p>
          </div>
        </Card>

        {/* Current Plan */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Current Plan</p>
              <p className="text-xl font-bold text-gray-900">
                {usageStats.current_plan.name}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatCurrency(usageStats.current_plan.price)}/month
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Activity className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        {/* Monthly Cost */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">This Period Cost</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(usageStats.monthly_cost)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Token usage cost
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        {/* Average Response Time */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {usageStats.average_response_time_ms?.toFixed(0) || 0}ms
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Last 7 days
              </p>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <Clock className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Usage Chart */}
      {usageStats.weekly_usage && usageStats.weekly_usage.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Usage Trend</h3>
            <TokenUsageChart 
              data={usageStats.weekly_usage} 
              height={300}
            />
          </div>
        </Card>
      )}

      {/* Usage by Type */}
      {usageStats.top_usage_types && usageStats.top_usage_types.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Usage Types</h3>
            <div className="space-y-4">
              {usageStats.top_usage_types.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getUsageTypeColor(item.usage_type)}`}></div>
                    <span className="text-sm font-medium text-gray-700">
                      {getUsageTypeLabel(item.usage_type)}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">
                      {formatTokenCount(item.tokens)} tokens
                    </p>
                    <p className="text-xs text-gray-500">
                      {item.count} requests
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Detailed Usage History */}
      {showDetails && (
        <Card>
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recent Usage History</h3>
              <div className="flex space-x-3">
                <input
                  type="date"
                  value={dateFilter.start_date}
                  onChange={(e) => setDateFilter(prev => ({ ...prev, start_date: e.target.value }))}
                  className="text-xs border rounded px-2 py-1"
                  placeholder="Start date"
                />
                <input
                  type="date"
                  value={dateFilter.end_date}
                  onChange={(e) => setDateFilter(prev => ({ ...prev, end_date: e.target.value }))}
                  className="text-xs border rounded px-2 py-1"
                  placeholder="End date"
                />
                <select
                  value={dateFilter.usage_type}
                  onChange={(e) => setDateFilter(prev => ({ ...prev, usage_type: e.target.value }))}
                  className="text-xs border rounded px-2 py-1"
                >
                  <option value="">All Types</option>
                  <option value="ai_generation">AI Generation</option>
                  <option value="chat_message">Chat Messages</option>
                  <option value="error_fix">Error Fixes</option>
                  <option value="file_analysis">File Analysis</option>
                </select>
                <Button onClick={fetchUsageHistory} size="sm" variant="outline">
                  <Filter className="h-4 w-4 mr-1" />
                  Filter
                </Button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date/Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Operation
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tokens
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cost
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {usageHistory.slice(0, 20).map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="secondary" className="text-xs">
                          {getUsageTypeLabel(item.usage_type)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {item.operation_description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatTokenCount(item.tokens_used)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.response_time_ms ? `${item.response_time_ms}ms` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={item.success ? "success" : "destructive"} className="text-xs">
                          {item.success ? 'Success' : 'Failed'}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(item.cost_dollars)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {usageHistory.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No usage history found for the selected filters.
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default UsageAnalyticsDashboard;