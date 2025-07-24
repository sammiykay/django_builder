import React, { useState, useEffect, useRef } from 'react';
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
  Crown,
  Sparkles,
  DollarSign,
  Zap,
  Shield,
  BarChart3,
  Wallet,
  Star
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

export const BillingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);

  const handlePlanUpgrade = (planType: string) => {
    // TODO: Implement plan upgrade logic
    console.log('Upgrading to plan:', planType);
    // This would typically open a payment modal or redirect to checkout
    // For now, switch to the dashboard tab to show the upgrade was processed
    setActiveTab('dashboard');
  };

  // Particle system setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create particles with billing theme colors (gold, green, blue)
    const colors = ['#F59E0B', '#10B981', '#3B82F6', '#8B5CF6', '#EF4444', '#06B6D4'];
    particlesRef.current = Array.from({ length: 45 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
      color: colors[Math.floor(Math.random() * colors.length)]
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((particle, index) => {
        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Wrap around edges
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        // Draw particle
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.opacity;
        ctx.fill();

        // Draw connections
        particlesRef.current.slice(index + 1).forEach(otherParticle => {
          const dx = particle.x - otherParticle.x;
          const dy = particle.y - otherParticle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 90) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(otherParticle.x, otherParticle.y);
            ctx.strokeStyle = particle.color;
            ctx.globalAlpha = 0.04 * (1 - distance / 90);
            ctx.lineWidth = 0.4;
            ctx.stroke();
          }
        });
      });

      ctx.globalAlpha = 1;
      requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  // Mouse tracking for interactive effects
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <AppLayout>
      <div className="min-h-screen bg-black relative overflow-hidden">
        {/* Animated Background */}
        <canvas
          ref={canvasRef}
          className="fixed inset-0 pointer-events-none z-0"
          style={{ filter: 'blur(0.5px)' }}
        />

        {/* Gradient Orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div 
            className="absolute w-96 h-96 bg-yellow-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"
            style={{
              left: mousePosition.x - 192,
              top: mousePosition.y - 192,
              transition: 'all 0.3s ease-out'
            }}
          />
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-green-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000" />
          <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000" />
        </div>

        {/* Main Content */}
        <div className="relative z-10">
          {/* Enhanced Header */}
          <div className="text-center py-16 px-4">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-yellow-500/20 to-orange-500/20 rounded-2xl backdrop-blur-sm border border-yellow-500/30">
                <DollarSign className="w-8 h-8 text-yellow-400" />
              </div>
              <div className="p-3 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-2xl backdrop-blur-sm border border-green-500/30">
                <BarChart3 className="w-8 h-8 text-green-400" />
              </div>
              <div className="p-3 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-2xl backdrop-blur-sm border border-blue-500/30">
                <Wallet className="w-8 h-8 text-blue-400" />
              </div>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-yellow-400 via-green-400 to-blue-400 bg-clip-text text-transparent mb-4">
              Billing & Usage
            </h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-8">
              Monitor your usage, manage your subscription, and unlock premium features
            </p>
            
            {/* Quick Actions */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link 
                to="/dashboard" 
                className="group flex items-center space-x-2 px-6 py-3 bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl text-gray-300 hover:text-white hover:border-blue-500/50 transition-all duration-300"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Dashboard</span>
              </Link>
              
              <button className="group relative flex items-center space-x-2 px-8 py-3 bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-yellow-500/25">
                <div className="absolute inset-0 bg-gradient-to-r from-yellow-600 to-orange-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <Crown className="w-4 h-4 relative z-10" />
                <span className="relative z-10">Upgrade Plan</span>
              </button>
            </div>
          </div>

          {/* Enhanced Tabs */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <div className="flex justify-center mb-12">
                <div className="p-2 bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                    <button
                      onClick={() => setActiveTab('dashboard')}
                      className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 ${
                        activeTab === 'dashboard'
                          ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 border border-yellow-500/30 shadow-lg shadow-yellow-500/10'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <CreditCard className="w-4 h-4" />
                      <span className="hidden sm:inline">Overview</span>
                    </button>
                    
                    <button
                      onClick={() => setActiveTab('features')}
                      className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 ${
                        activeTab === 'features'
                          ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-400 border border-purple-500/30 shadow-lg shadow-purple-500/10'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <Crown className="w-4 h-4" />
                      <span className="hidden sm:inline">Features</span>
                    </button>
                    
                    <button
                      onClick={() => setActiveTab('analytics')}
                      className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 ${
                        activeTab === 'analytics'
                          ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-400 border border-green-500/30 shadow-lg shadow-green-500/10'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <TrendingUp className="w-4 h-4" />
                      <span className="hidden sm:inline">Analytics</span>
                    </button>
                    
                    <button
                      onClick={() => setActiveTab('history')}
                      className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 ${
                        activeTab === 'history'
                          ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <History className="w-4 h-4" />
                      <span className="hidden sm:inline">History</span>
                    </button>
                    
                    <button
                      onClick={() => setActiveTab('settings')}
                      className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 ${
                        activeTab === 'settings'
                          ? 'bg-gradient-to-r from-red-500/20 to-orange-500/20 text-red-400 border border-red-500/30 shadow-lg shadow-red-500/10'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <Settings className="w-4 h-4" />
                      <span className="hidden sm:inline">Settings</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Enhanced Tab Content */}
              {activeTab === 'dashboard' && (
                <div className="space-y-8">
                  <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-8">
                    <SimpleBillingDashboard />
                  </div>
                </div>
              )}

              {activeTab === 'features' && (
                <div className="space-y-8">
                  <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-8">
                    <AdvancedFeatures 
                      plan={{
                        id: 1,
                        name: "Free Plan",
                        description: "Basic features for getting started",
                        plan_type: "free",
                        price: "$0",
                        billing_interval: "monthly",
                        token_limit: 10000,
                        bonus_tokens: 0,
                        max_projects: 3,
                        max_concurrent_containers: 1,
                        enable_ai_chat: true,
                        enable_auto_error_fix: false,
                        enable_advanced_templates: false,
                        enable_custom_containers: false,
                        enable_code_export: true,
                        enable_version_control: false,
                        enable_collaboration: false,
                        enable_analytics: false,
                        enable_priority_support: false,
                        enable_custom_models: false,
                        enable_api_access: false,
                        enable_white_labeling: false,
                        is_active: true,
                        is_default_free: true,
                        sort_order: 1
                      }}
                    />
                  </div>
                </div>
              )}

              {activeTab === 'analytics' && (
                <div className="space-y-8">
                  <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-8">
                    <TokenUsageChart />
                  </div>
                  
                  {/* Enhanced Analytics Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-2 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg backdrop-blur-sm border border-blue-500/30">
                          <BarChart3 className="w-5 h-5 text-blue-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Top Projects by Usage</h3>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">E-commerce Store</span>
                          <span className="text-sm font-semibold text-blue-400">12,450 tokens</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">Blog Platform</span>
                          <span className="text-sm font-semibold text-green-400">8,230 tokens</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">Task Manager</span>
                          <span className="text-sm font-semibold text-purple-400">5,670 tokens</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-2 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg backdrop-blur-sm border border-green-500/30">
                          <Zap className="w-5 h-5 text-green-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Peak Usage Hours</h3>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">2:00 PM - 4:00 PM</span>
                          <span className="text-sm font-semibold text-green-400">35% of usage</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">10:00 AM - 12:00 PM</span>
                          <span className="text-sm font-semibold text-yellow-400">28% of usage</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">7:00 PM - 9:00 PM</span>
                          <span className="text-sm font-semibold text-blue-400">22% of usage</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="p-2 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg backdrop-blur-sm border border-purple-500/30">
                          <Star className="w-5 h-5 text-purple-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Efficiency Metrics</h3>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">Avg. Response Time</span>
                          <span className="text-sm font-semibold text-purple-400">2.3s</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">Success Rate</span>
                          <span className="text-sm font-semibold text-green-400">97.2%</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-sm text-gray-300">Avg. Tokens per Request</span>
                          <span className="text-sm font-semibold text-blue-400">1,245</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-8">
                  <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-8">
                    <div className="flex items-center space-x-3 mb-6">
                      <div className="p-2 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg backdrop-blur-sm border border-blue-500/30">
                        <History className="w-6 h-6 text-blue-400" />
                      </div>
                      <h3 className="text-2xl font-bold text-white">Usage History</h3>
                    </div>
                    <div className="text-center py-12">
                      <div className="p-4 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-2xl backdrop-blur-sm border border-blue-500/20 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                        <History className="w-12 h-12 text-blue-400" />
                      </div>
                      <h4 className="text-xl font-semibold text-white mb-3">Usage history will be displayed here</h4>
                      <p className="text-gray-400 max-w-md mx-auto">
                        Detailed logs of all AI operations, token usage, and project interactions will appear in this section
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'settings' && (
                <div className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
                      <div className="flex items-center space-x-3 mb-6">
                        <div className="p-2 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg backdrop-blur-sm border border-blue-500/30">
                          <Settings className="w-5 h-5 text-blue-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Billing Preferences</h3>
                      </div>
                      <div className="space-y-4">
                        <label className="flex items-center space-x-3 p-3 bg-gray-800/30 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer">
                          <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50" defaultChecked />
                          <span className="text-sm text-gray-300">Email notifications for billing updates</span>
                        </label>
                        <label className="flex items-center space-x-3 p-3 bg-gray-800/30 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer">
                          <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50" defaultChecked />
                          <span className="text-sm text-gray-300">Usage alerts at 80% of limit</span>
                        </label>
                        <label className="flex items-center space-x-3 p-3 bg-gray-800/30 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer">
                          <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50" />
                          <span className="text-sm text-gray-300">Auto-upgrade when limit reached</span>
                        </label>
                      </div>
                    </div>

                    <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
                      <div className="flex items-center space-x-3 mb-6">
                        <div className="p-2 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg backdrop-blur-sm border border-green-500/30">
                          <Shield className="w-5 h-5 text-green-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Usage Controls</h3>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-3 text-gray-300">
                            Daily Token Limit
                          </label>
                          <input 
                            type="number" 
                            className="w-full px-4 py-3 bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all duration-300"
                            placeholder="No limit"
                          />
                        </div>
                        <label className="flex items-center space-x-3 p-3 bg-gray-800/30 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer">
                          <input type="checkbox" className="rounded bg-gray-700 border-gray-600 text-green-500 focus:ring-green-500/50" />
                          <span className="text-sm text-gray-300">Pause usage when limit reached</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-900/40 backdrop-blur-sm border border-red-500/30 rounded-2xl p-6">
                    <div className="flex items-center space-x-3 mb-6">
                      <div className="p-2 bg-gradient-to-br from-red-500/20 to-orange-500/20 rounded-lg backdrop-blur-sm border border-red-500/30">
                        <Shield className="w-5 h-5 text-red-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-red-400">Danger Zone</h3>
                    </div>
                    <div className="space-y-4">
                      <p className="text-sm text-gray-300 leading-relaxed">
                        These actions cannot be undone. Please proceed with caution when making changes to your subscription.
                      </p>
                      <button className="group relative flex items-center space-x-2 px-6 py-3 bg-red-500/10 backdrop-blur-sm border border-red-500/30 text-red-400 hover:text-white hover:bg-red-500/20 rounded-xl font-semibold transition-all duration-300">
                        <span>Cancel Subscription</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </Tabs>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};