import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { 
  Crown, 
  Zap, 
  Activity, 
  Check, 
  AlertTriangle,
  CreditCard 
} from 'lucide-react';
import { apiService } from '../../services/api';
import { BillingPlan, UserSubscription } from '../../types/api';

interface PlanUpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentSubscription: UserSubscription;
  availablePlans: BillingPlan[];
  onUpgradeComplete: () => void;
}

export const PlanUpgradeModal: React.FC<PlanUpgradeModalProps> = ({
  isOpen,
  onClose,
  currentSubscription,
  availablePlans,
  onUpgradeComplete
}) => {
  const [selectedPlan, setSelectedPlan] = useState<BillingPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usageData, setUsageData] = useState<any>(null);

  // Fetch usage data for recommendations
  React.useEffect(() => {
    if (isOpen) {
      fetchUsageData();
    }
  }, [isOpen]);

  const fetchUsageData = async () => {
    try {
      const data = await apiService.getUsageAnalyticsDashboard();
      setUsageData(data);
    } catch (err) {
      console.error('Failed to fetch usage data:', err);
    }
  };

  const getRecommendedPlan = () => {
    if (!usageData) return null;
    
    // If user is using more than 90% of their current tokens, recommend an upgrade
    if (usageData.usage_percentage > 90) {
      // Find the next tier up
      const currentPlanPrice = parseFloat(currentSubscription.plan.price);
      const higherPlans = availablePlans
        .filter(plan => parseFloat(plan.price) > currentPlanPrice)
        .sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
      
      return higherPlans[0];
    }
    
    return null;
  };

  const getUsagePrediction = (plan: BillingPlan) => {
    if (!usageData || plan.token_limit === 0) return null;
    
    const currentUsage = usageData.total_tokens_used;
    const currentPeriodDays = 30; // Assuming monthly billing
    const averageDailyUsage = currentUsage / currentPeriodDays;
    const projectedMonthlyUsage = averageDailyUsage * 30;
    
    if (projectedMonthlyUsage > plan.token_limit) {
      return {
        willExceed: true,
        projectedUsage: Math.round(projectedMonthlyUsage),
        overage: Math.round(projectedMonthlyUsage - plan.token_limit)
      };
    }
    
    return {
      willExceed: false,
      projectedUsage: Math.round(projectedMonthlyUsage),
      utilization: Math.round((projectedMonthlyUsage / plan.token_limit) * 100)
    };
  };

  const handleUpgrade = async () => {
    if (!selectedPlan) return;

    try {
      setLoading(true);
      setError(null);

      await apiService.upgradePlan(selectedPlan.id);

      onUpgradeComplete();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to upgrade plan');
    } finally {
      setLoading(false);
    }
  };

  const getPlanIcon = (planType: string) => {
    switch (planType) {
      case 'enterprise':
        return <Crown className="h-6 w-6 text-yellow-500" />;
      case 'paid':
        return <Zap className="h-6 w-6 text-blue-500" />;
      default:
        return <Activity className="h-6 w-6 text-green-500" />;
    }
  };

  const getPlanFeatures = (plan: BillingPlan) => {
    const features = [
      plan.token_limit === 0 
        ? 'Unlimited tokens' 
        : `${new Intl.NumberFormat().format(plan.token_limit)} tokens/month`,
      plan.max_projects === 0 
        ? 'Unlimited projects' 
        : `Up to ${plan.max_projects} projects`,
      `${plan.max_concurrent_containers} concurrent container${plan.max_concurrent_containers > 1 ? 's' : ''}`,
    ];

    // Add boolean feature flags
    if (plan.enable_ai_chat) {
      features.push('AI Chat');
    }
    if (plan.enable_auto_error_fix) {
      features.push('Auto Error Fix');
    }
    if (plan.enable_advanced_templates) {
      features.push('Advanced Templates');
    }
    if (plan.enable_custom_containers) {
      features.push('Custom Containers');
    }
    if (plan.enable_code_export) {
      features.push('Code Export');
    }
    if (plan.enable_version_control) {
      features.push('Version Control');
    }
    if (plan.enable_collaboration) {
      features.push('Team Collaboration');
    }
    if (plan.enable_analytics) {
      features.push('Advanced Analytics');
    }
    if (plan.enable_priority_support) {
      features.push('Priority Support');
    }
    if (plan.enable_custom_models) {
      features.push('Custom AI Models');
    }
    if (plan.enable_api_access) {
      features.push('API Access');
    }
    if (plan.enable_white_labeling) {
      features.push('White Labeling');
    }

    return features;
  };

  const isUpgrade = (plan: BillingPlan) => {
    if (currentSubscription.plan.plan_type === 'free' && plan.plan_type !== 'free') {
      return true;
    }
    return parseFloat(plan.price.replace('$', '')) > parseFloat(currentSubscription.plan.price.replace('$', ''));
  };

  const isCurrentPlan = (plan: BillingPlan) => {
    return plan.id === currentSubscription.plan.id;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Choose Your Plan
          </DialogTitle>
          <DialogDescription>
            Upgrade your plan to access more tokens and advanced features.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-800">{error}</span>
          </div>
        )}

        {/* Usage Recommendation Banner */}
        {usageData && getRecommendedPlan() && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <span className="font-medium text-yellow-800">Upgrade Recommended</span>
            </div>
            <p className="text-sm text-yellow-700">
              You're using {usageData.usage_percentage?.toFixed(1)}% of your current token limit. 
              Consider upgrading to the <strong>{getRecommendedPlan()?.name}</strong> plan to avoid hitting limits.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {availablePlans.map((plan) => {
            const features = getPlanFeatures(plan);
            const isCurrent = isCurrentPlan(plan);
            const isUpgradeOption = isUpgrade(plan);
            const usagePrediction = getUsagePrediction(plan);
            const isRecommended = getRecommendedPlan()?.id === plan.id;
            
            return (
              <Card 
                key={plan.id}
                className={`cursor-pointer transition-all ${
                  selectedPlan?.id === plan.id 
                    ? 'border-blue-500 ring-2 ring-blue-200' 
                    : isCurrent
                    ? 'border-green-500 bg-green-50'
                    : isRecommended
                    ? 'border-yellow-500 bg-yellow-50'
                    : 'hover:border-gray-300'
                } ${isCurrent ? '' : 'hover:shadow-md'}`}
                onClick={() => !isCurrent && setSelectedPlan(plan)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      {getPlanIcon(plan.plan_type)}
                      <h3 className="text-lg font-semibold">{plan.name}</h3>
                    </div>
                    <div className="flex flex-col gap-1">
                      {isCurrent && (
                        <Badge variant="secondary">Current</Badge>
                      )}
                      {isRecommended && (
                        <Badge className="bg-yellow-500 text-white">Recommended</Badge>
                      )}
                      {plan.plan_type === 'enterprise' && !isRecommended && (
                        <Badge variant="default">Popular</Badge>
                      )}
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="text-3xl font-bold">
                      {plan.price}
                    </div>
                    {plan.plan_type !== 'free' && (
                      <div className="text-sm text-muted-foreground">
                        per {plan.billing_interval}
                      </div>
                    )}
                  </div>

                  {/* Usage Prediction */}
                  {usagePrediction && (
                    <div className={`p-3 rounded-lg mb-4 ${
                      usagePrediction.willExceed 
                        ? 'bg-red-50 border border-red-200' 
                        : 'bg-green-50 border border-green-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        {usagePrediction.willExceed ? (
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                        ) : (
                          <Check className="h-4 w-4 text-green-600" />
                        )}
                        <span className={`text-sm font-medium ${
                          usagePrediction.willExceed ? 'text-red-800' : 'text-green-800'
                        }`}>
                          Usage Prediction
                        </span>
                      </div>
                      <p className={`text-xs ${
                        usagePrediction.willExceed ? 'text-red-700' : 'text-green-700'
                      }`}>
                        {usagePrediction.willExceed ? (
                          <>Would exceed by {new Intl.NumberFormat().format(usagePrediction.overage)} tokens</>
                        ) : (
                          <>~{usagePrediction.utilization}% utilization expected</>
                        )}
                      </p>
                    </div>
                  )}

                  <p className="text-sm text-muted-foreground mb-4">
                    {plan.description}
                  </p>

                  <div className="space-y-2">
                    {features.map((feature, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500" />
                        <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {isCurrent ? (
                    <Button disabled className="w-full mt-6">
                      Current Plan
                    </Button>
                  ) : isUpgradeOption ? (
                    <div className="mt-6">
                      <div className="text-center mb-2">
                        <Badge 
                          variant="outline" 
                          className="bg-blue-50 text-blue-700 border-blue-200"
                        >
                          Upgrade
                        </Badge>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-6">
                      <div className="text-center mb-2">
                        <Badge variant="outline" className="bg-gray-50 text-gray-600">
                          Downgrade
                        </Badge>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {selectedPlan && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold mb-2">Plan Change Summary</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Current Plan</p>
                <p className="font-medium">{currentSubscription.plan.name}</p>
                <p className="text-muted-foreground">
                  {currentSubscription.plan.is_free 
                    ? 'Free' 
                    : `$${currentSubscription.plan.price}/${currentSubscription.plan.billing_interval}`
                  }
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">New Plan</p>
                <p className="font-medium">{selectedPlan.name}</p>
                <p className="text-muted-foreground">
                  {selectedPlan.is_free 
                    ? 'Free' 
                    : `$${selectedPlan.price}/${selectedPlan.billing_interval}`
                  }
                </p>
              </div>
            </div>
            
            {!selectedPlan.is_free && (
              <div className="mt-3 text-sm text-muted-foreground">
                <p>
                  • Changes take effect immediately
                </p>
                <p>
                  • You'll be charged the new amount on your next billing cycle
                </p>
                <p>
                  • Token limits reset with the new plan
                </p>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpgrade} 
            disabled={!selectedPlan || loading || isCurrentPlan(selectedPlan)}
            className="min-w-24"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              selectedPlan && isUpgrade(selectedPlan) ? 'Upgrade Plan' : 'Change Plan'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};