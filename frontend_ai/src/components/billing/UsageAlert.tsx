import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription } from '../ui/alert';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import { 
  AlertTriangle, 
  Zap, 
  X, 
  TrendingUp,
  CreditCard 
} from 'lucide-react';
import { apiService } from '../../services/api';

interface UsageAlertProps {
  onUpgradeClick?: () => void;
  className?: string;
  showDismiss?: boolean;
}

interface UsageStats {
  usage_percentage: number;
  tokens_remaining: number | string;
  total_tokens_used: number;
  current_plan: {
    name: string;
    plan_type: string;
  };
}

export const UsageAlert: React.FC<UsageAlertProps> = ({ 
  onUpgradeClick, 
  className = "",
  showDismiss = true 
}) => {
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [isDismissed, setIsDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsageStats();
    
    // Check for dismissal in localStorage
    const dismissed = localStorage.getItem('usage_alert_dismissed');
    if (dismissed) {
      const dismissedDate = new Date(dismissed);
      const now = new Date();
      const timeDiff = now.getTime() - dismissedDate.getTime();
      const hoursDiff = timeDiff / (1000 * 3600);
      
      // Show alert again after 24 hours
      if (hoursDiff < 24) {
        setIsDismissed(true);
      }
    }
  }, []);

  const fetchUsageStats = async () => {
    try {
      const data = await apiService.getUsageAnalyticsDashboard();
      setUsageStats(data);
    } catch (error) {
      console.error('Failed to fetch usage stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem('usage_alert_dismissed', new Date().toISOString());
  };

  if (loading || isDismissed || !usageStats) {
    return null;
  }

  const { usage_percentage, tokens_remaining, current_plan } = usageStats;

  // Only show alert for high usage scenarios
  const shouldShowAlert = usage_percentage >= 75;
  
  if (!shouldShowAlert) {
    return null;
  }

  const getAlertConfig = () => {
    if (usage_percentage >= 100) {
      return {
        variant: 'destructive' as const,
        icon: AlertTriangle,
        title: 'Token Limit Reached',
        message: 'You have reached your monthly token limit. Upgrade your plan to continue using AI features.',
        badgeText: 'Limit Exceeded',
        badgeColor: 'destructive' as const,
        showUpgrade: true
      };
    } else if (usage_percentage >= 90) {
      return {
        variant: 'destructive' as const,
        icon: AlertTriangle,
        title: 'Approaching Token Limit',
        message: `You're using ${usage_percentage.toFixed(1)}% of your tokens. Consider upgrading to avoid interruptions.`,
        badgeText: 'High Usage',
        badgeColor: 'destructive' as const,
        showUpgrade: true
      };
    } else if (usage_percentage >= 75) {
      return {
        variant: 'default' as const,
        icon: TrendingUp,
        title: 'High Token Usage',
        message: `You've used ${usage_percentage.toFixed(1)}% of your monthly tokens on the ${current_plan.name} plan.`,
        badgeText: 'Monitor Usage',
        badgeColor: 'secondary' as const,
        showUpgrade: current_plan.plan_type === 'free'
      };
    }

    return null;
  };

  const alertConfig = getAlertConfig();
  if (!alertConfig) return null;

  const { variant, icon: Icon, title, message, badgeText, badgeColor, showUpgrade } = alertConfig;

  return (
    <Alert variant={variant} className={`${className} relative`}>
      <Icon className="h-4 w-4" />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium">{title}</span>
          <Badge variant={badgeColor} className="text-xs">
            {badgeText}
          </Badge>
        </div>
        <AlertDescription className="text-sm">
          {message}
          {typeof tokens_remaining === 'number' && tokens_remaining > 0 && (
            <span className="block mt-1 text-xs opacity-80">
              {new Intl.NumberFormat().format(tokens_remaining)} tokens remaining
            </span>
          )}
        </AlertDescription>
      </div>
      
      <div className="flex items-center gap-2 ml-4">
        {showUpgrade && onUpgradeClick && (
          <Button
            onClick={onUpgradeClick}
            size="sm"
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1"
          >
            <CreditCard className="h-3 w-3 mr-1" />
            Upgrade
          </Button>
        )}
        
        {showDismiss && (
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-black/10 rounded transition-colors"
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </Alert>
  );
};

export default UsageAlert;