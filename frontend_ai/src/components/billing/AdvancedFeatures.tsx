import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { Badge } from '../ui/badge-new';
import { 
  Crown, 
  Zap, 
  Users, 
  Globe, 
  BarChart3, 
  Shield, 
  Rocket,
  Star,
  Lock,
  CheckCircle,
  XCircle,
  ArrowUpCircle
} from 'lucide-react';

interface AdvancedFeaturesProps {
  userPlan: 'free' | 'paid' | 'enterprise';
  onUpgrade: (planType: string) => void;
}

interface Feature {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  requiredPlan: 'free' | 'paid' | 'enterprise';
  isEnabled?: boolean;
  usage?: string;
  comingSoon?: boolean;
}

const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({ userPlan, onUpgrade }) => {
  const features: Feature[] = [
    {
      id: 'priority_processing',
      name: 'Priority AI Processing',
      description: 'Get faster project generation with dedicated resources and skip the queue',
      icon: <Zap className="w-5 h-5" />,
      requiredPlan: 'paid',
      usage: '3x faster generation'
    },
    {
      id: 'custom_templates',
      name: 'Custom Templates',
      description: 'Create and save your own project templates for rapid deployment',
      icon: <Star className="w-5 h-5" />,
      requiredPlan: 'paid',
      usage: '5 templates saved'
    },
    {
      id: 'advanced_integrations',
      name: 'Advanced Integrations',
      description: 'Connect with external APIs, databases, and third-party services',
      icon: <Globe className="w-5 h-5" />,
      requiredPlan: 'paid',
      usage: 'Stripe, AWS, Google APIs'
    },
    {
      id: 'unlimited_projects',
      name: 'Unlimited Projects',
      description: 'Create as many Django projects as you need without restrictions',
      icon: <Rocket className="w-5 h-5" />,
      requiredPlan: 'paid',
      usage: '∞ projects'
    },
    {
      id: 'team_collaboration',
      name: 'Team Collaboration',
      description: 'Invite team members, share projects, and collaborate in real-time',
      icon: <Users className="w-5 h-5" />,
      requiredPlan: 'enterprise',
      usage: '12 team members'
    },
    {
      id: 'advanced_analytics',
      name: 'Advanced Analytics',
      description: 'Detailed performance metrics, usage insights, and optimization suggestions',
      icon: <BarChart3 className="w-5 h-5" />,
      requiredPlan: 'enterprise',
      usage: 'Full dashboard access'
    },
    {
      id: 'white_label',
      name: 'White-label Deployments',
      description: 'Deploy applications with your own branding and custom domain',
      icon: <Crown className="w-5 h-5" />,
      requiredPlan: 'enterprise',
      usage: 'Custom branding applied'
    },
    {
      id: 'priority_support',
      name: 'Priority Support',
      description: '24/7 dedicated support with direct access to our engineering team',
      icon: <Shield className="w-5 h-5" />,
      requiredPlan: 'enterprise',
      usage: '< 1 hour response time'
    }
  ];

  const getFeatureStatus = (feature: Feature) => {
    const planLevels = { free: 0, paid: 1, enterprise: 2 };
    const userLevel = planLevels[userPlan];
    const requiredLevel = planLevels[feature.requiredPlan];

    if (userLevel >= requiredLevel) {
      return {
        status: 'enabled',
        icon: <CheckCircle className="w-4 h-4 text-green-500" />,
        badgeVariant: 'default' as const,
        badgeText: 'Active'
      };
    } else {
      return {
        status: 'locked',
        icon: <Lock className="w-4 h-4 text-gray-400" />,
        badgeVariant: 'secondary' as const,
        badgeText: `${feature.requiredPlan} Plan`
      };
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'paid': return 'text-blue-400';
      case 'enterprise': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const enabledFeatures = features.filter(f => getFeatureStatus(f).status === 'enabled');
  const lockedFeatures = features.filter(f => getFeatureStatus(f).status === 'locked');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Advanced Features</h2>
        <p className="text-gray-400">
          Unlock powerful capabilities to supercharge your Django development
        </p>
      </div>

      {/* Current Plan Summary */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {userPlan === 'enterprise' && <Crown className="w-6 h-6 text-yellow-500" />}
            {userPlan === 'paid' && <Zap className="w-6 h-6 text-blue-500" />}
            {userPlan === 'free' && <Star className="w-6 h-6 text-gray-500" />}
            <div>
              <h3 className="text-lg font-semibold text-white capitalize">{userPlan} Plan</h3>
              <p className="text-sm text-gray-400">
                {enabledFeatures.length} of {features.length} advanced features enabled
              </p>
            </div>
          </div>
          {userPlan !== 'enterprise' && (
            <Button 
              onClick={() => onUpgrade(userPlan === 'free' ? 'paid' : 'enterprise')}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
            >
              <ArrowUpCircle className="w-4 h-4 mr-2" />
              Upgrade Plan
            </Button>
          )}
        </div>
      </Card>

      {/* Enabled Features */}
      {enabledFeatures.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Your Active Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {enabledFeatures.map((feature) => {
              const status = getFeatureStatus(feature);
              return (
                <Card key={feature.id} className="p-4 bg-gray-800 border-gray-700 border-l-4 border-l-green-500">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2 text-green-400">
                      {feature.icon}
                      <span className="font-semibold">{feature.name}</span>
                    </div>
                    <Badge variant={status.badgeVariant} className="text-xs">
                      {status.badgeText}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{feature.description}</p>
                  {feature.usage && (
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-400">Current usage:</span>
                      <span className="text-white font-medium">{feature.usage}</span>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Locked Features */}
      {lockedFeatures.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-gray-400" />
            Available with Upgrade
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {lockedFeatures.map((feature) => {
              const status = getFeatureStatus(feature);
              return (
                <Card key={feature.id} className="p-4 bg-gray-800 border-gray-700 opacity-75 hover:opacity-100 transition-opacity">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2 text-gray-400">
                      {feature.icon}
                      <span className="font-semibold">{feature.name}</span>
                    </div>
                    <Badge variant="secondary" className={`text-xs ${getPlanColor(feature.requiredPlan)}`}>
                      {feature.requiredPlan.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-400 mb-3">{feature.description}</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full border-gray-600 text-gray-300 hover:text-white hover:border-gray-500"
                    onClick={() => onUpgrade(feature.requiredPlan)}
                  >
                    Upgrade to unlock
                  </Button>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Feature Comparison */}
      <Card className="p-6 bg-gray-800 border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Feature Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 text-gray-300">Feature</th>
                <th className="text-center py-3 text-gray-400">Free</th>
                <th className="text-center py-3 text-blue-400">Paid</th>
                <th className="text-center py-3 text-purple-400">Enterprise</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {features.map((feature) => (
                <tr key={feature.id}>
                  <td className="py-3 text-gray-300">{feature.name}</td>
                  <td className="text-center py-3">
                    {feature.requiredPlan === 'free' ? 
                      <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : 
                      <XCircle className="w-4 h-4 text-gray-600 mx-auto" />
                    }
                  </td>
                  <td className="text-center py-3">
                    {['free', 'paid'].includes(feature.requiredPlan) ? 
                      <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : 
                      <XCircle className="w-4 h-4 text-gray-600 mx-auto" />
                    }
                  </td>
                  <td className="text-center py-3">
                    <CheckCircle className="w-4 h-4 text-green-500 mx-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Upgrade CTA */}
      {userPlan !== 'enterprise' && (
        <Card className="p-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
          <div className="text-center">
            <Crown className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">
              Ready to unlock more power?
            </h3>
            <p className="text-gray-300 mb-4">
              Upgrade now and get access to {userPlan === 'free' ? 'priority processing, custom templates, and more' : 'team collaboration, analytics, and enterprise features'}
            </p>
            <div className="flex gap-3 justify-center">
              {userPlan === 'free' && (
                <Button 
                  onClick={() => onUpgrade('paid')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Upgrade to Paid
                </Button>
              )}
              <Button 
                onClick={() => onUpgrade('enterprise')}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                Go Enterprise
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default AdvancedFeatures;