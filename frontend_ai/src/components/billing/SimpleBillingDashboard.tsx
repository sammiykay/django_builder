import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import { Progress } from '../ui/progress';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import AdvancedFeatures from './AdvancedFeatures';
import PaymentGateway from './PaymentGateway';
import { 
  CreditCard, 
  Activity, 
  TrendingUp, 
  Calendar,
  AlertTriangle,
  Crown,
  Zap
} from 'lucide-react';
import { apiService } from '../../services/api';

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

export const SimpleBillingDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPaymentGateway, setShowPaymentGateway] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<BillingPlan | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getBillingDashboard();
      setDashboardData(response);
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
      'ai_generation': 'bg-purple-900 text-purple-300 border-purple-700',
      'chat_message': 'bg-blue-900 text-blue-300 border-blue-700',
      'error_fix': 'bg-red-900 text-red-300 border-red-700',
      'file_analysis': 'bg-green-900 text-green-300 border-green-700',
      'project_planning': 'bg-orange-900 text-orange-300 border-orange-700',
      'code_review': 'bg-yellow-900 text-yellow-300 border-yellow-700',
    };
    return colors[type] || 'bg-gray-800 text-gray-300 border-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-400">{error}</p>
          <Button onClick={fetchDashboardData} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!dashboardData) return null;

  const { subscription, usage_stats, recent_usage, available_plans } = dashboardData;

  const handlePlanUpgrade = (plan: BillingPlan) => {
    setSelectedPlan(plan);
    setShowPaymentGateway(true);
  };

  const handlePaymentSuccess = () => {
    setShowPaymentGateway(false);
    setSelectedPlan(null);
    // Refresh dashboard data after successful payment
    fetchDashboardData();
    // Trigger subscription update for other components
    localStorage.setItem('subscription_updated', Date.now().toString());
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'subscription_updated',
      newValue: Date.now().toString()
    }));
  };

  const handlePaymentClose = () => {
    setShowPaymentGateway(false);
    setSelectedPlan(null);
  };

  return (
    <div className="space-y-6">
      {/* Current Plan Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 bg-gray-800 border-gray-700">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-300">Current Plan</h3>
            {getPlanIcon(subscription.plan.plan_type)}
          </div>
          <div className="text-2xl font-bold text-white">{subscription.plan.name}</div>
          <p className="text-xs text-gray-400">
            {subscription.plan.is_free ? 'Free Plan' : `$${subscription.plan.price}/${subscription.plan.billing_interval}`}
          </p>
        </Card>

        <Card className="p-6 bg-gray-800 border-gray-700">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-300">Tokens Remaining</h3>
            <Activity className="h-4 w-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {subscription.plan.token_limit === 0 
              ? '∞' 
              : formatNumber(subscription.tokens_remaining)
            }
          </div>
          <p className="text-xs text-gray-400">
            of {subscription.plan.token_limit === 0 
              ? 'unlimited' 
              : formatNumber(subscription.plan.token_limit)
            } tokens
          </p>
        </Card>

        <Card className="p-6 bg-gray-800 border-gray-700">
          <div className="flex flex-row items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-300">Monthly Cost</h3>
            <CreditCard className="h-4 w-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-white">${usage_stats.monthly_cost}</div>
          <p className="text-xs text-gray-400">
            Current billing period
          </p>
        </Card>
      </div>

      {/* Usage Progress */}
      {subscription.plan.token_limit > 0 && (
        <Card className="p-6 bg-gray-800 border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Token Usage</h3>
            <Badge variant={subscription.usage_percentage > 80 ? 'destructive' : 'secondary'}>
              {subscription.usage_percentage.toFixed(1)}%
            </Badge>
          </div>
          <div className="space-y-4">
            <Progress value={subscription.usage_percentage} className="w-full" />
            <div className="flex justify-between text-sm text-gray-400">
              <span>{formatNumber(subscription.tokens_used_this_period)} used</span>
              <span>{formatNumber(subscription.tokens_remaining)} remaining</span>
            </div>
            {subscription.usage_percentage > 90 && (
              <div className="flex items-center gap-2 p-3 bg-yellow-900/20 border border-yellow-600 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
                <span className="text-sm text-yellow-300">
                  You're approaching your token limit. Consider upgrading your plan.
                </span>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Billing Period Info */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-5 w-5 text-gray-300" />
          <h3 className="text-lg font-semibold text-white">Billing Period</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">Period Start</p>
            <p className="font-semibold text-white">{formatDate(subscription.current_period_start)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Period End</p>
            <p className="font-semibold text-white">{formatDate(subscription.current_period_end)}</p>
          </div>
        </div>
      </Card>

      {/* Usage Breakdown */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Usage by Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(usage_stats.usage_by_type).map(([type, tokens]) => (
            <div key={type} className="text-center p-3 border border-gray-600 rounded-lg bg-gray-700">
              <p className="text-sm text-gray-400 capitalize">
                {type.replace('_', ' ')}
              </p>
              <p className="text-lg font-semibold text-white">{formatNumber(tokens)}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent Usage */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Recent Activity</h3>
        <div className="space-y-3">
          {recent_usage.slice(0, 10).map((usage) => (
            <div key={usage.id} className="flex items-center justify-between py-2 border-b border-gray-600">
              <div className="flex items-center gap-3">
                <Badge 
                  variant="outline" 
                  className={getUsageTypeColor(usage.usage_type)}
                >
                  {usage.usage_type.replace('_', ' ')}
                </Badge>
                <div>
                  <p className="text-sm font-medium text-white">
                    {usage.operation_description || 'AI Operation'}
                  </p>
                  {usage.project_name && (
                    <p className="text-xs text-gray-400">
                      Project: {usage.project_name}
                    </p>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-white">
                  {formatNumber(usage.tokens_used)} tokens
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(usage.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Available Plans */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {available_plans.map((plan) => (
            <div 
              key={plan.id} 
              className={`border rounded-lg p-4 ${
                plan.id === subscription.plan.id 
                  ? 'border-blue-500 bg-blue-900/20' 
                  : 'border-gray-600 bg-gray-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">{plan.name}</h4>
                {getPlanIcon(plan.plan_type)}
              </div>
              <p className="text-2xl font-bold mb-2 text-white">
                {plan.is_free ? 'Free' : `$${plan.price}`}
                {!plan.is_free && (
                  <span className="text-sm text-gray-400">
                    /{plan.billing_interval}
                  </span>
                )}
              </p>
              <p className="text-sm text-gray-400 mb-3">
                {plan.token_limit === 0 
                  ? 'Unlimited tokens' 
                  : `${formatNumber(plan.token_limit)} tokens`
                }
              </p>
              <p className="text-sm mb-4 text-gray-300">{plan.description}</p>
              {plan.id !== subscription.plan.id ? (
                <Button 
                  className="w-full" 
                  variant={plan.plan_type === 'enterprise' ? 'default' : 'outline'}
                  onClick={() => handlePlanUpgrade(plan)}
                >
                  {plan.is_free ? 'Downgrade' : 'Upgrade'}
                </Button>
              ) : (
                <Badge variant="secondary" className="w-full justify-center">
                  Current Plan
                </Badge>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Advanced Features Section */}
      <AdvancedFeatures 
        plan={subscription.plan}
      />

      {/* Payment Gateway Modal */}
      {showPaymentGateway && selectedPlan && (
        <PaymentGateway
          selectedPlan={selectedPlan}
          onPaymentSuccess={handlePaymentSuccess}
          onClose={handlePaymentClose}
        />
      )}
    </div>
  );
};