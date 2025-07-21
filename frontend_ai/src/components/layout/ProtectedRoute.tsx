import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ROUTES } from '../../routes';
import Card from '../ui/Card';
import { Loader2, Shield, Code } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiresAuth?: boolean;
  redirectTo?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiresAuth = true, 
  redirectTo = ROUTES.LOGIN 
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="text-center max-w-md w-full">
          <div className="flex flex-col items-center gap-6 p-8">
            {/* Loading Animation */}
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <Loader2 className="w-6 h-6 animate-spin text-blue-500 absolute -bottom-2 -right-2 bg-white rounded-full p-1" />
            </div>
            
            {/* Loading Text */}
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-gray-900">
                Verifying Access
              </h3>
              <p className="text-gray-600">
                Checking your authentication status...
              </p>
            </div>
            
            {/* Loading Shimmer */}
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-shimmer"></div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // If authentication is required but user is not authenticated
  if (requiresAuth && !user) {
    // Store the attempted URL for redirect after login
    const from = location.pathname + location.search;
    return <Navigate to={`${redirectTo}?from=${encodeURIComponent(from)}`} replace />;
  }

  // If user is authenticated but shouldn't access this route (inverse protection)
  if (!requiresAuth && user) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;