import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import { Progress } from '../ui/progress';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import { 
  CreditCard, 
  Activity, 
  TrendingUp, 
  Calendar,
  AlertTriangle,
  Crown,
  Zap
} from 'lucide-react';
import { api } from '../../services/api';

interface BillingPlan {
  id: number;
  name: string;
  description: string;
  plan_type: 'free' | 'paid' | 'enterprise';
  token_limit: number;
  price: string;
  billing_interval: 'monthly' | 'yearly' | 'one_time';
  max_projects: number;
  is_free: boolean;
}

interface UserSubscription {
  id: number;
  plan: BillingPlan;
  status: 'active' | 'canceled' | 'expired' | 'suspended';
  tokens_used_this_period: number;
  tokens_remaining: number;
  usage_percentage: number;
  current_period_start: string;
  current_period_end: string;
  bonus_tokens_remaining: number;
}

interface UsageStats {
  total_tokens_used: number;
  tokens_remaining: number;
  usage_percentage: number;
  current_plan: BillingPlan;
  usage_by_type: Record<string, number>;
  daily_usage: Array<{ day: string; tokens: number }>;
  monthly_cost: string;
}

interface TokenUsage {
  id: number;
  usage_type: string;
  tokens_used: number;
  operation_description: string;
  created_at: string;
  project_name?: string;
  success: boolean;
}

interface DashboardData {
  subscription: UserSubscription;
  usage_stats: UsageStats;
  recent_usage: TokenUsage[];
  available_plans: BillingPlan[];
}

export const BillingDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/billing/dashboard/');
      setDashboardData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getPlanIcon = (planType: string) => {
    switch (planType) {
      case 'enterprise':
        return <Crown className="h-5 w-5 text-yellow-500" />;
      case 'paid':
        return <Zap className="h-5 w-5 text-blue-500" />;
      default:
        return <Activity className="h-5 w-5 text-green-500" />;
    }
  };

  const getUsageTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'ai_generation': 'bg-purple-100 text-purple-800',
      'chat_message': 'bg-blue-100 text-blue-800',
      'error_fix': 'bg-red-100 text-red-800',
      'file_analysis': 'bg-green-100 text-green-800',
      'project_planning': 'bg-orange-100 text-orange-800',
      'code_review': 'bg-yellow-100 text-yellow-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchDashboardData} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!dashboardData) return null;

  const { subscription, usage_stats, recent_usage, available_plans } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Current Plan Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Current Plan</h3>
            {getPlanIcon(subscription.plan.plan_type)}
          </div>
          <div className="text-2xl font-bold">{subscription.plan.name}</div>
          <p className="text-xs text-gray-500">
            {subscription.plan.is_free ? 'Free Plan' : `$${subscription.plan.price}/${subscription.plan.billing_interval}`}
          </p>
        </Card>

        <Card className="p-6">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Tokens Remaining</h3>
            <Activity className="h-4 w-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold">
            {subscription.plan.token_limit === 0 
              ? '∞' 
              : formatNumber(subscription.tokens_remaining)
            }
          </div>
          <p className="text-xs text-gray-500">
            of {subscription.plan.token_limit === 0 
              ? 'unlimited' 
              : formatNumber(subscription.plan.token_limit)
            } tokens
          </p>
        </Card>

        <Card className="p-6">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Monthly Cost</h3>
            <CreditCard className="h-4 w-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold">${usage_stats.monthly_cost}</div>
          <p className="text-xs text-gray-500">
            Current billing period
          </p>
        </Card>
      </div>

      {/* Usage Progress */}
      {subscription.plan.token_limit > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Token Usage
              <Badge variant={subscription.usage_percentage > 80 ? 'destructive' : 'secondary'}>
                {subscription.usage_percentage.toFixed(1)}%
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={subscription.usage_percentage} className="w-full" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{formatNumber(subscription.tokens_used_this_period)} used</span>
              <span>{formatNumber(subscription.tokens_remaining)} remaining</span>
            </div>
            {subscription.usage_percentage > 90 && (
              <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm text-yellow-800">
                  You're approaching your token limit. Consider upgrading your plan.
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Billing Period Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Billing Period
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Period Start</p>
              <p className="font-semibold">{formatDate(subscription.current_period_start)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Period End</p>
              <p className="font-semibold">{formatDate(subscription.current_period_end)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Usage by Type</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(usage_stats.usage_by_type).map(([type, tokens]) => (
              <div key={type} className="text-center p-3 border rounded-lg">
                <p className="text-sm text-muted-foreground capitalize">
                  {type.replace('_', ' ')}
                </p>
                <p className="text-lg font-semibold">{formatNumber(tokens)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Usage */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recent_usage.slice(0, 10).map((usage) => (
              <div key={usage.id} className="flex items-center justify-between py-2 border-b">
                <div className="flex items-center gap-3">
                  <Badge 
                    variant="outline" 
                    className={getUsageTypeColor(usage.usage_type)}
                  >
                    {usage.usage_type.replace('_', ' ')}
                  </Badge>
                  <div>
                    <p className="text-sm font-medium">
                      {usage.operation_description || 'AI Operation'}
                    </p>
                    {usage.project_name && (
                      <p className="text-xs text-muted-foreground">
                        Project: {usage.project_name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">
                    {formatNumber(usage.tokens_used)} tokens
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(usage.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Available Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Available Plans</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {available_plans.map((plan) => (
              <div 
                key={plan.id} 
                className={`border rounded-lg p-4 ${
                  plan.id === subscription.plan.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{plan.name}</h3>
                  {getPlanIcon(plan.plan_type)}
                </div>
                <p className="text-2xl font-bold mb-2">
                  {plan.is_free ? 'Free' : `$${plan.price}`}
                  {!plan.is_free && (
                    <span className="text-sm text-muted-foreground">
                      /{plan.billing_interval}
                    </span>
                  )}
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  {plan.token_limit === 0 
                    ? 'Unlimited tokens' 
                    : `${formatNumber(plan.token_limit)} tokens`
                  }
                </p>
                <p className="text-sm mb-4">{plan.description}</p>
                {plan.id !== subscription.plan.id && (
                  <Button 
                    className="w-full" 
                    variant={plan.plan_type === 'enterprise' ? 'default' : 'outline'}
                    onClick={() => {
                      // TODO: Implement plan upgrade
                      console.log('Upgrade to plan:', plan.id);
                    }}
                  >
                    {plan.is_free ? 'Downgrade' : 'Upgrade'}
                  </Button>
                )}
                {plan.id === subscription.plan.id && (
                  <Badge variant="secondary" className="w-full justify-center">
                    Current Plan
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};