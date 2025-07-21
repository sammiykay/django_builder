import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import { AppRoutes } from './routes';
import Card from './components/ui/Card';
import { Loader2, Code } from 'lucide-react';
import './styles/design-system.css';

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <Card className="text-center max-w-md w-full bg-gray-800 border-gray-700">
          <div className="flex flex-col items-center gap-6 p-8">
            {/* Loading Animation */}
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Code className="w-8 h-8 text-white" />
              </div>
              <Loader2 className="w-6 h-6 animate-spin text-blue-500 absolute -bottom-2 -right-2 bg-gray-800 rounded-full p-1" />
            </div>
            
            {/* Loading Text */}
            <div className="space-y-2">
              <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Django AI Builder
              </h3>
              <p className="text-gray-400">Initializing your workspace...</p>
            </div>
            
            {/* Loading Progress */}
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <AppRoutes />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;