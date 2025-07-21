import React, { useState, useEffect } from 'react';
import { 
  LogOut, 
  User, 
  Settings, 
  Home, 
  FolderOpen, 
  Menu, 
  X,
  Sparkles,
  Code2,
  Sidebar
} from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { UserProfile } from '../../types/api';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import ProjectSidebar from './ProjectSidebar';
import SidebarHoverZone from './SidebarHoverZone';
import '../../styles/design-system.css';

interface AppLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, className = '' }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarVisible, setIsSidebarVisible] = useState(false);

  useEffect(() => {
    if (user) {
      loadUserProfile();
    }
  }, [user]);

  // Listen for profile updates
  useEffect(() => {
    const handleProfileUpdate = () => {
      loadUserProfile();
    };

    window.addEventListener('profileUpdated', handleProfileUpdate);
    return () => {
      window.removeEventListener('profileUpdated', handleProfileUpdate);
    };
  }, []);

  const loadUserProfile = async () => {
    try {
      const profile = await apiService.getUserProfile();
      setUserProfile(profile);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  const getAvatarUrl = (avatar: string | undefined) => {
    if (!avatar) return null;
    
    if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
      return avatar;
    }
    
    if (avatar.startsWith('/')) {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      return `${API_BASE_URL}${avatar}`;
    }
    
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${API_BASE_URL}/media/${avatar}`;
  };

  // Don't show navbar on auth pages
  if (location.pathname === '/login' || location.pathname === '/register') {
    return (
      <div className={`min-h-screen bg-gray-900 ${className}`}>
        {children}
      </div>
    );
  }

  if (!user) {
    return (
      <div className={`min-h-screen bg-gray-900 ${className}`}>
        {children}
      </div>
    );
  }

  const isProjectPage = location.pathname.includes('/project/');
  const isDashboard = location.pathname === '/dashboard';

  return (
    <div className={`min-h-screen bg-gray-900 ${className}`}>
      {/* Unified Navigation Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-sm sticky top-0 z-50">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left Section - Logo & Brand */}
            <div className="flex items-center gap-4">
              <Link 
                to="/dashboard" 
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Code2 className="w-6 h-6 text-white" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-lg font-bold text-white">Django AI Builder</h1>
                  <p className="text-xs text-gray-400">Build smarter, faster</p>
                </div>
              </Link>
            </div>

            {/* Center Section - Navigation (Desktop) */}
            <nav className="hidden lg:flex items-center gap-2">
              <Link
                to="/dashboard"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                  location.pathname === '/dashboard'
                    ? 'bg-gray-700 text-white shadow-sm'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <Home className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              
              {(isProjectPage || isDashboard) && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsSidebarVisible(!isSidebarVisible)}
                    icon={<Sidebar className="w-4 h-4" />}
                    className="text-gray-300 hover:text-white"
                  >
                    Projects
                  </Button>
                  {isProjectPage && (
                    <Badge variant="primary" size="sm">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Project Mode
                    </Badge>
                  )}
                </>
              )}
            </nav>

            {/* Right Section - User Menu */}
            <div className="flex items-center gap-3">
              {/* Desktop User Menu */}
              <div className="hidden lg:flex items-center gap-3">
                <Link
                  to="/profile"
                  className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center overflow-hidden">
                    {getAvatarUrl(userProfile?.avatar) ? (
                      <img 
                        src={getAvatarUrl(userProfile?.avatar)!} 
                        alt="Profile" 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User className="w-4 h-4 text-gray-300" />
                    )}
                  </div>
                  <span className="text-sm font-medium">
                    {user.first_name || user.username}
                  </span>
                </Link>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  icon={<LogOut className="w-4 h-4" />}
                  className="text-gray-300 hover:text-white"
                >
                  Logout
                </Button>
              </div>

              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                icon={isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                className="lg:hidden text-gray-300 hover:text-white"
              />
            </div>
          </div>

          {/* Mobile Menu */}
          {isMobileMenuOpen && (
            <div className="lg:hidden border-t border-gray-700 py-4 space-y-2">
              <Link
                to="/dashboard"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium text-sm transition-all ${
                  location.pathname === '/dashboard'
                    ? 'bg-gray-700 text-white shadow-sm'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <Home className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              
              {(isProjectPage || isDashboard) && (
                <button
                  onClick={() => {
                    setIsSidebarVisible(!isSidebarVisible);
                    setIsMobileMenuOpen(false);
                  }}
                  className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors w-full text-left"
                >
                  <Sidebar className="w-4 h-4" />
                  <span className="text-sm font-medium">Projects</span>
                </button>
              )}
              
              <Link
                to="/profile"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
              >
                <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center overflow-hidden">
                  {getAvatarUrl(userProfile?.avatar) ? (
                    <img 
                      src={getAvatarUrl(userProfile?.avatar)!} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="w-4 h-4 text-gray-300" />
                  )}
                </div>
                <span className="text-sm font-medium">
                  Profile Settings
                </span>
              </Link>
              
              <button
                onClick={() => {
                  logout();
                  setIsMobileMenuOpen(false);
                }}
                className="flex items-center gap-3 px-4 py-3 w-full text-left text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm font-medium">Logout</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Project Sidebar - Show on dashboard and project pages */}
      {(isProjectPage || isDashboard) && (
        <>
          <SidebarHoverZone 
            onTrigger={setIsSidebarVisible} 
            isActive={isSidebarVisible} 
          />
          <ProjectSidebar 
            isVisible={isSidebarVisible} 
            onClose={() => setIsSidebarVisible(false)}
          />
        </>
      )}
    </div>
  );
};

export default AppLayout;