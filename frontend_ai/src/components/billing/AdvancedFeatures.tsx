import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import { BillingPlan } from '../../types/api';
import { 
  MessageSquare,
  Wrench,
  Star,
  Container,
  Download,
  GitBranch,
  Users,
  BarChart3,
  Shield,
  Cpu,
  Plug,
  Crown,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface AdvancedFeaturesProps {
  plan: BillingPlan;
}

interface FeatureItem {
  key: keyof BillingPlan;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const FEATURE_DEFINITIONS: FeatureItem[] = [
  {
    key: 'enable_ai_chat',
    label: 'AI Chat',
    description: 'Interactive AI chat functionality',
    icon: <MessageSquare className="w-5 h-5" />
  },
  {
    key: 'enable_auto_error_fix',
    label: 'Auto Error Fix',
    description: 'Automatic error detection and fixing',
    icon: <Wrench className="w-5 h-5" />
  },
  {
    key: 'enable_advanced_templates',
    label: 'Advanced Templates',
    description: 'Access to premium project templates',
    icon: <Star className="w-5 h-5" />
  },
  {
    key: 'enable_custom_containers',
    label: 'Custom Containers',
    description: 'Use custom Docker configurations',
    icon: <Container className="w-5 h-5" />
  },
  {
    key: 'enable_code_export',
    label: 'Code Export',
    description: 'Export generated code',
    icon: <Download className="w-5 h-5" />
  },
  {
    key: 'enable_version_control',
    label: 'Version Control',
    description: 'Git integration and version control',
    icon: <GitBranch className="w-5 h-5" />
  },
  {
    key: 'enable_collaboration',
    label: 'Team Collaboration',
    description: 'Team collaboration features',
    icon: <Users className="w-5 h-5" />
  },
  {
    key: 'enable_analytics',
    label: 'Advanced Analytics',
    description: 'Advanced usage analytics',
    icon: <BarChart3 className="w-5 h-5" />
  },
  {
    key: 'enable_priority_support',
    label: 'Priority Support',
    description: 'Priority customer support',
    icon: <Shield className="w-5 h-5" />
  },
  {
    key: 'enable_custom_models',
    label: 'Custom AI Models',
    description: 'Access to different AI models',
    icon: <Cpu className="w-5 h-5" />
  },
  {
    key: 'enable_api_access',
    label: 'API Access',
    description: 'API access for external integrations',
    icon: <Plug className="w-5 h-5" />
  },
  {
    key: 'enable_white_labeling',
    label: 'White Labeling',
    description: 'White-label customization',
    icon: <Crown className="w-5 h-5" />
  }
];

const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({ plan }) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Plan Features</h2>
        <p className="text-gray-400">
          Features included in your {plan.name}
        </p>
      </div>

      {/* Current Plan Summary */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {plan.plan_type === 'enterprise' && <Crown className="w-6 h-6 text-yellow-500" />}
            {plan.plan_type === 'paid' && <Star className="w-6 h-6 text-blue-500" />}
            {plan.plan_type === 'free' && <CheckCircle className="w-6 h-6 text-gray-500" />}
            <div>
              <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
              <p className="text-sm text-gray-400">
                {plan.description}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{plan.price}</div>
            <div className="text-sm text-gray-400">per {plan.billing_interval}</div>
          </div>
        </div>
      </Card>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURE_DEFINITIONS.map(feature => (
          <Card
            key={feature.key}
            className={`p-4 bg-gray-800 border-gray-700 ${
              plan[feature.key] ? 'border-l-4 border-l-green-500' : 'opacity-60'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`flex items-center gap-2 ${
                plan[feature.key] ? 'text-green-400' : 'text-gray-400'
              }`}>
                {feature.icon}
                <span className="font-semibold">{feature.label}</span>
              </div>
              {plan[feature.key] ? (
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-500 flex-shrink-0" />
              )}
            </div>
            <p className={`text-sm ${
              plan[feature.key] ? 'text-gray-300' : 'text-gray-500'
            }`}>
              {feature.description}
            </p>
            <div className="mt-2">
              <Badge 
                variant={plan[feature.key] ? 'default' : 'secondary'} 
                className="text-xs"
              >
                {plan[feature.key] ? 'Included' : 'Not Available'}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      {/* Plan Limits */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Plan Limits</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{plan.max_projects}</div>
            <div className="text-sm text-gray-400">Max Projects</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{plan.token_limit.toLocaleString()}</div>
            <div className="text-sm text-gray-400">Token Limit</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">{plan.max_concurrent_containers}</div>
            <div className="text-sm text-gray-400">Concurrent Containers</div>
          </div>
        </div>
        {plan.bonus_tokens > 0 && (
          <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-600 rounded-lg">
            <div className="flex items-center gap-2 text-yellow-400">
              <Star className="w-4 h-4" />
              <span className="text-sm font-medium">
                Bonus: {plan.bonus_tokens.toLocaleString()} additional tokens included
              </span>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default AdvancedFeatures;