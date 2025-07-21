import React, { useState } from 'react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { SimpleBillingDashboard } from '../components/billing/SimpleBillingDashboard';
import { TokenUsageChart } from '../components/billing/TokenUsageChart';
import AdvancedFeatures from '../components/billing/AdvancedFeatures';
import AppLayout from '../components/layout/AppLayout';
import { 
  CreditCard, 
  TrendingUp, 
  History, 
  Settings,
  ArrowLeft,
  Crown
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const BillingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const handlePlanUpgrade = (planType: string) => {
    // TODO: Implement plan upgrade logic
    console.log('Upgrading to plan:', planType);
    // This would typically open a payment modal or redirect to checkout
    // For now, switch to the dashboard tab to show the upgrade was processed
    setActiveTab('dashboard');
  };

  return (
    <AppLayout>
      <div className="min-h-screen">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                <Link 
                  to="/dashboard" 
                  className="flex items-center gap-2 text-gray-300 hover:text-white"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Dashboard
                </Link>
                <div className="border-l border-gray-600 h-6" />
                <div className="flex items-center gap-2">
                  <CreditCard className="h-6 w-6 text-blue-400" />
                  <h1 className="text-xl font-semibold text-white">
                    Billing & Usage
                  </h1>
                </div>
              </div>
              <Button className="bg-blue-600 hover:bg-blue-700">
                Upgrade Plan
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-5 mb-8 bg-gray-800 border-gray-600">
              <TabsTrigger value="dashboard" className="flex items-center gap-2 text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                <CreditCard className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="features" className="flex items-center gap-2 text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                <Crown className="h-4 w-4" />
                Features
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2 text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                <TrendingUp className="h-4 w-4" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2 text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                <History className="h-4 w-4" />
                Usage History
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2 text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                <Settings className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <SimpleBillingDashboard />
          </TabsContent>

          <TabsContent value="features" className="space-y-6">
            <AdvancedFeatures 
              userPlan="free" 
              onUpgrade={handlePlanUpgrade}
            />
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <TokenUsageChart />
            
            {/* Additional Analytics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="p-6 bg-gray-800 border-gray-700">
                <h3 className="text-base font-semibold mb-4 text-white">Top Projects by Usage</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">E-commerce Store</span>
                    <span className="text-sm font-semibold text-white">12,450 tokens</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">Blog Platform</span>
                    <span className="text-sm font-semibold text-white">8,230 tokens</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">Task Manager</span>
                    <span className="text-sm font-semibold text-white">5,670 tokens</span>
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gray-800 border-gray-700">
                <h3 className="text-base font-semibold mb-4 text-white">Peak Usage Hours</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">2:00 PM - 4:00 PM</span>
                    <span className="text-sm font-semibold text-white">35% of usage</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">10:00 AM - 12:00 PM</span>
                    <span className="text-sm font-semibold text-white">28% of usage</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">7:00 PM - 9:00 PM</span>
                    <span className="text-sm font-semibold text-white">22% of usage</span>
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gray-800 border-gray-700">
                <h3 className="text-base font-semibold mb-4 text-white">Efficiency Metrics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">Avg. Response Time</span>
                    <span className="text-sm font-semibold text-white">2.3s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">Success Rate</span>
                    <span className="text-sm font-semibold text-white">97.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-300">Avg. Tokens per Request</span>
                    <span className="text-sm font-semibold text-white">1,245</span>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <Card className="p-6 bg-gray-800 border-gray-700">
              <h3 className="text-lg font-semibold mb-4 text-white">Usage History</h3>
              <div className="space-y-4">
                {/* This would be populated from API data */}
                <div className="text-center py-8">
                  <History className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-300">Usage history will be displayed here</p>
                  <p className="text-sm text-gray-400">
                    Detailed logs of all AI operations and token usage
                  </p>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-6 bg-gray-800 border-gray-700">
                <h3 className="text-lg font-semibold mb-4 text-white">Billing Preferences</h3>
                <div className="space-y-4">
                  <div>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500" defaultChecked />
                      <span className="text-sm text-gray-300">Email notifications for billing updates</span>
                    </label>
                  </div>
                  <div>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500" defaultChecked />
                      <span className="text-sm text-gray-300">Usage alerts at 80% of limit</span>
                    </label>
                  </div>
                  <div>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500" />
                      <span className="text-sm text-gray-300">Auto-upgrade when limit reached</span>
                    </label>
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gray-800 border-gray-700">
                <h3 className="text-lg font-semibold mb-4 text-white">Usage Controls</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                      Daily Token Limit
                    </label>
                    <input 
                      type="number" 
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400"
                      placeholder="No limit"
                    />
                  </div>
                  <div>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500" />
                      <span className="text-sm text-gray-300">Pause usage when limit reached</span>
                    </label>
                  </div>
                </div>
              </Card>
            </div>

            <Card className="p-6 bg-gray-800 border-gray-700">
              <h3 className="text-lg font-semibold text-red-400 mb-4">Danger Zone</h3>
              <div className="space-y-4">
                <p className="text-sm text-gray-300">
                  These actions cannot be undone. Please proceed with caution.
                </p>
                <Button className="text-red-400 border-red-600 hover:bg-red-900/20 bg-transparent">
                  Cancel Subscription
                </Button>
              </div>
            </Card>
          </TabsContent>
          </Tabs>
        </div>

        {/* Plan Upgrade Modal can be added later */}
      </div>
    </AppLayout>
  );
};