import React, { useState } from 'react';
import { Eye, EyeOff, Loader2, LogIn, Code2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Input from '../ui/Input';
import '../../styles/design-system.css';

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(formData.username, formData.password);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900/20 to-purple-900/20 bg-primary flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-6">
          <div className="flex items-center justify-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Code2 className="w-7 h-7 text-white" />
            </div>
            <div className="text-left">
              <h1 className="text-2xl font-bold text-primary">Django AI Builder</h1>
              <p className="text-sm text-tertiary">Build smarter, faster</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-primary">
              Welcome back! 👋
            </h2>
            <p className="text-secondary text-lg">
              Sign in to continue building amazing Django projects with AI
            </p>
          </div>
        </div>
        
        {/* Login Form */}
        <Card className="space-y-6" elevated>
          {error && (
            <Card className="bg-red-50/5 border-red-500/20">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-red-500/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-red-500 text-xs">!</span>
                </div>
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            </Card>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <Input
              label="Username"
              type="text"
              placeholder="Enter your username"
              value={formData.username}
              onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              required
              disabled={isLoading}
            />
            
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-primary">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  className="input pr-12"
                  value={formData.password}
                  onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-tertiary hover:text-primary transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isLoading}
              loading={isLoading}
              icon={!isLoading ? <LogIn className="w-5 h-5" /> : undefined}
              className="w-full"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <div className="text-center pt-4 border-t border-secondary">
            <p className="text-secondary">
              Don't have an account?{' '}
              <Link 
                to="/register" 
                className="font-semibold text-blue-400 hover:text-blue-300 transition-colors"
              >
                Create one now
              </Link>
            </p>
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-sm text-tertiary">
            ✨ Powered by AI • Built with Django • Deployed in minutes
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;