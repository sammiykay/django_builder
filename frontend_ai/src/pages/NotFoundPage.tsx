import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, Search, Bug } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full text-center space-y-8 p-8">
        {/* 404 Illustration */}
        <div className="space-y-4">
          <div className="text-8xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            404
          </div>
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
            <Search className="w-16 h-16 text-gray-400" />
          </div>
        </div>

        {/* Error Message */}
        <div className="space-y-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Page Not Found
          </h1>
          <p className="text-lg text-gray-600 max-w-md mx-auto leading-relaxed">
            Sorry, we couldn't find the page you're looking for. The page may have been moved, deleted, or you entered an incorrect URL.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={() => navigate(-1)}
            variant="secondary"
            className="flex items-center justify-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </Button>
          
          <Link to="/">
            <Button className="flex items-center justify-center space-x-2 w-full sm:w-auto">
              <Home className="w-4 h-4" />
              <span>Go Home</span>
            </Button>
          </Link>
        </div>

        {/* Help Section */}
        <div className="pt-8 border-t border-gray-200 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Need Help?
          </h3>
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Search className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Search</span>
              </div>
              <p className="text-gray-600">
                Try searching for what you need in our dashboard
              </p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Bug className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Report Issue</span>
              </div>
              <p className="text-gray-600">
                Let us know if you think this is a bug
              </p>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="pt-4">
          <p className="text-sm text-gray-500 mb-4">Quick links:</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <Link 
              to="/dashboard" 
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              Dashboard
            </Link>
            <Link 
              to="/profile" 
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              Profile
            </Link>
            <Link 
              to="/billing" 
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              Billing
            </Link>
            <a 
              href="#" 
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              Support
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default NotFoundPage;