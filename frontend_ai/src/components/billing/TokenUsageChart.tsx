import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { apiService } from '../../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

interface DailyUsage {
  day: string;
  tokens: number;
  cost_cents: number;
}

interface UsageByType {
  usage_type: string;
  tokens: number;
  cost_cents: number;
}

interface ChartData {
  daily_usage: DailyUsage[];
  usage_by_type: UsageByType[];
}

const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', 
  '#ff00ff', '#00ffff', '#ff0000', '#0000ff', '#ffff00'
];

export const TokenUsageChart: React.FC = () => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const [viewType, setViewType] = useState<'daily' | 'usage_type'>('daily');

  useEffect(() => {
    fetchChartData();
  }, [timeRange]);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getTokenUsageChart(timeRange);
      setChartData(response);
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatUsageType = (type: string) => {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  if (!chartData) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">No usage data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Token Usage Analytics</h3>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Button
              onClick={() => setViewType('daily')}
              className={`px-3 py-1 text-sm ${
                viewType === 'daily' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Daily Trend
            </Button>
            <Button
              onClick={() => setViewType('usage_type')}
              className={`px-3 py-1 text-sm ${
                viewType === 'usage_type' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              By Type
            </Button>
          </div>
          <div className="flex items-center gap-1">
            <Button
              onClick={() => setTimeRange(7)}
              className={`px-3 py-1 text-sm ${
                timeRange === 7 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              7d
            </Button>
            <Button
              onClick={() => setTimeRange(30)}
              className={`px-3 py-1 text-sm ${
                timeRange === 30 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              30d
            </Button>
            <Button
              onClick={() => setTimeRange(90)}
              className={`px-3 py-1 text-sm ${
                timeRange === 90 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              90d
            </Button>
          </div>
        </div>
      </div>
      <div>
        {viewType === 'daily' ? (
          <div className="space-y-4">
            {chartData.daily_usage.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData.daily_usage}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="day" 
                      tickFormatter={formatDate}
                      fontSize={12}
                    />
                    <YAxis fontSize={12} />
                    <Tooltip
                      labelFormatter={(value) => formatDate(value as string)}
                      formatter={(value, name) => [
                        new Intl.NumberFormat().format(value as number),
                        name === 'tokens' ? 'Tokens Used' : 'Cost (cents)'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="tokens" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      dot={{ fill: '#8884d8', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-muted-foreground">No daily usage data available</p>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <div>
              <h4 className="text-sm font-medium mb-4">Distribution by Type</h4>
              {chartData.usage_by_type.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={chartData.usage_by_type}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="tokens"
                        nameKey="usage_type"
                        label={({ usage_type, percent }) => 
                          `${formatUsageType(usage_type)} ${(percent * 100).toFixed(0)}%`
                        }
                      >
                        {chartData.usage_by_type.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value, name) => [
                          new Intl.NumberFormat().format(value as number),
                          'Tokens Used'
                        ]}
                        labelFormatter={(value) => formatUsageType(value as string)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <p className="text-muted-foreground">No usage type data available</p>
                </div>
              )}
            </div>

            {/* Bar Chart */}
            <div>
              <h4 className="text-sm font-medium mb-4">Tokens by Category</h4>
              {chartData.usage_by_type.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData.usage_by_type}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="usage_type" 
                        tickFormatter={formatUsageType}
                        fontSize={10}
                        angle={-45}
                        textAnchor="end"
                      />
                      <YAxis fontSize={12} />
                      <Tooltip
                        formatter={(value) => [
                          new Intl.NumberFormat().format(value as number),
                          'Tokens Used'
                        ]}
                        labelFormatter={formatUsageType}
                      />
                      <Bar dataKey="tokens" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <p className="text-muted-foreground">No usage type data available</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Summary Stats */}
        {chartData.usage_by_type.length > 0 && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {chartData.usage_by_type.slice(0, 4).map((item, index) => (
              <div key={item.usage_type} className="text-center p-3 border rounded-lg">
                <div 
                  className="w-3 h-3 rounded-full mx-auto mb-2"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <p className="text-xs text-muted-foreground">
                  {formatUsageType(item.usage_type)}
                </p>
                <p className="font-semibold">
                  {new Intl.NumberFormat().format(item.tokens)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};