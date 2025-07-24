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
import { api } from '../../services/api';
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

  const handleUpgrade = async () => {
    if (!selectedPlan) return;

    try {
      setLoading(true);
      setError(null);

      await api.post(`/api/billing/subscriptions/${currentSubscription.id}/upgrade/`, {
        plan_id: selectedPlan.id
      });

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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {availablePlans.map((plan) => {
            const features = getPlanFeatures(plan);
            const isCurrent = isCurrentPlan(plan);
            const isUpgradeOption = isUpgrade(plan);
            
            return (
              <Card 
                key={plan.id}
                className={`cursor-pointer transition-all ${
                  selectedPlan?.id === plan.id 
                    ? 'border-blue-500 ring-2 ring-blue-200' 
                    : isCurrent
                    ? 'border-green-500 bg-green-50'
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
                    {isCurrent && (
                      <Badge variant="secondary">Current</Badge>
                    )}
                    {plan.plan_type === 'enterprise' && (
                      <Badge variant="default">Popular</Badge>
                    )}
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