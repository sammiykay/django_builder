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
  Sidebar,
  CreditCard
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
      {/* Enhanced Navigation Header */}
      <header className="relative bg-gradient-to-r from-black/95 via-gray-900/95 to-black/95 backdrop-blur-xl border-b border-gray-700/20 shadow-2xl sticky top-0 z-50">
        {/* Animated background gradient matching dashboard particles */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 via-cyan-500/5 via-green-500/5 to-orange-500/5 opacity-40" />
        
        {/* Dashboard-matching particle overlay */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-2 left-1/4 w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse opacity-40" />
          <div className="absolute top-3 right-1/3 w-1 h-1 bg-purple-500 rounded-full animate-pulse opacity-30" style={{ animationDelay: '1s' }} />
          <div className="absolute bottom-2 left-2/3 w-2 h-2 bg-cyan-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1 right-1/4 w-1 h-1 bg-green-500 rounded-full animate-pulse opacity-35" style={{ animationDelay: '3s' }} />
          <div className="absolute bottom-3 left-1/3 w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse opacity-45" style={{ animationDelay: '4s' }} />
          
          {/* Connecting lines between particles */}
          <div className="absolute top-2 left-1/4 w-16 h-px bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-30 animate-pulse" />
          <div className="absolute bottom-2 right-1/3 w-12 h-px bg-gradient-to-r from-cyan-500/20 to-green-500/20 opacity-25 animate-pulse" style={{ animationDelay: '1.5s' }} />
        </div>

        <div className="relative px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Enhanced Left Section - Logo & Brand */}
            <div className="flex items-center gap-4">
              <Link 
                to="/dashboard" 
                className="group flex items-center gap-4 hover:scale-105 transition-all duration-300"
              >
                <div className="relative">
                  <div className="w-11 h-11 bg-gradient-to-br from-blue-500 via-purple-500 via-cyan-500 via-green-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-500/20 group-hover:shadow-purple-500/30 transition-all duration-500 group-hover:rotate-12 group-hover:scale-110">
                    <Code2 className="w-6 h-6 text-white group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 via-cyan-500 to-orange-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-500 animate-pulse" />
                  
                  {/* Floating particles around logo */}
                  <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse opacity-60" />
                  <div className="absolute -bottom-1 -left-1 w-1 h-1 bg-purple-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                  <div className="absolute top-1/2 -right-2 w-1 h-1 bg-cyan-500 rounded-full animate-pulse opacity-70" style={{ animationDelay: '2s' }} />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-lg font-black bg-gradient-to-r from-blue-400 via-purple-400 via-cyan-400 to-orange-400 bg-clip-text text-transparent group-hover:from-blue-300 group-hover:via-purple-300 group-hover:via-cyan-300 group-hover:to-orange-300 transition-all duration-500">
                    Django AI Builder
                  </h1>
                  <p className="text-xs bg-gradient-to-r from-gray-400 to-gray-500 bg-clip-text text-transparent group-hover:from-gray-300 group-hover:to-gray-400 transition-all duration-300 font-medium">
                    ✨ Build smarter, faster
                  </p>
                </div>
              </Link>
            </div>

            {/* Enhanced Center Section - Navigation (Desktop) */}
            <nav className="hidden lg:flex items-center gap-3">
              <Link
                to="/dashboard"
                className={`group relative flex items-center gap-3 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-500 overflow-hidden ${
                  location.pathname === '/dashboard'
                    ? 'bg-gradient-to-r from-blue-500/15 via-purple-500/15 via-cyan-500/15 to-orange-500/15 text-white shadow-lg shadow-blue-500/20 border border-blue-500/30'
                    : 'text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-blue-500/10 hover:via-purple-500/10 hover:to-cyan-500/10 hover:shadow-lg hover:scale-105'
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 via-cyan-500/10 to-orange-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${location.pathname === '/dashboard' ? 'opacity-100 animate-pulse' : ''}`} />
                
                {/* Floating particles around dashboard link */}
                {location.pathname === '/dashboard' && (
                  <>
                    <div className="absolute -top-1 left-2 w-1 h-1 bg-blue-500 rounded-full animate-pulse opacity-60" />
                    <div className="absolute -bottom-1 right-3 w-1 h-1 bg-purple-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                    <div className="absolute top-1/2 -right-1 w-0.5 h-0.5 bg-cyan-500 rounded-full animate-pulse opacity-70" style={{ animationDelay: '2s' }} />
                  </>
                )}
                
                <Home className="w-4 h-4 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                <span className="relative z-10">Dashboard</span>
                
                {location.pathname === '/dashboard' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-400 via-purple-400 via-cyan-400 to-orange-400 shadow-lg shadow-blue-500/30 animate-pulse" />
                )}
              </Link>

              {/* Billing Link */}
              <Link
                to="/billing"
                className={`group relative flex items-center gap-3 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-500 overflow-hidden ${
                  location.pathname === '/billing'
                    ? 'bg-gradient-to-r from-yellow-500/15 via-green-500/15 via-blue-500/15 to-purple-500/15 text-white shadow-lg shadow-yellow-500/20 border border-yellow-500/30'
                    : 'text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-yellow-500/10 hover:via-green-500/10 hover:to-blue-500/10 hover:shadow-lg hover:scale-105'
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-r from-yellow-500/10 via-green-500/10 via-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${location.pathname === '/billing' ? 'opacity-100 animate-pulse' : ''}`} />
                
                {/* Floating particles around billing link */}
                {location.pathname === '/billing' && (
                  <>
                    <div className="absolute -top-1 left-2 w-1 h-1 bg-yellow-500 rounded-full animate-pulse opacity-60" />
                    <div className="absolute -bottom-1 right-3 w-1 h-1 bg-green-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                    <div className="absolute top-1/2 -right-1 w-0.5 h-0.5 bg-blue-500 rounded-full animate-pulse opacity-70" style={{ animationDelay: '2s' }} />
                  </>
                )}
                
                <CreditCard className="w-4 h-4 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                <span className="relative z-10">Billing</span>
                
                {location.pathname === '/billing' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-yellow-400 via-green-400 via-blue-400 to-purple-400 shadow-lg shadow-yellow-500/30 animate-pulse" />
                )}
              </Link>
              
              {isProjectPage && (
                <div className="relative flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/15 via-pink-500/15 to-orange-500/15 rounded-xl border border-purple-500/30 backdrop-blur-sm">
                  <Sparkles className="w-3 h-3 text-purple-400 animate-pulse" />
                  <span className="text-sm font-semibold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">Project Mode</span>
                  
                  {/* Project mode particles */}
                  <div className="absolute -top-0.5 left-1 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-60" />
                  <div className="absolute -bottom-0.5 right-2 w-1 h-1 bg-pink-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                  
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl animate-pulse opacity-50" />
                </div>
              )}
            </nav>

            {/* Enhanced Right Section - User Menu */}
            <div className="flex items-center gap-4">
              {/* Enhanced Desktop User Menu */}
              <div className="hidden lg:flex items-center gap-3">
                <Link
                  to="/profile"
                  className="group flex items-center gap-3 px-4 py-2.5 text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-blue-500/10 hover:via-purple-500/10 hover:to-cyan-500/10 rounded-xl transition-all duration-500 hover:scale-105"
                >
                  <div className="relative">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-gray-700 via-gray-600 to-gray-700 flex items-center justify-center overflow-hidden border border-gray-600/50 group-hover:border-blue-500/50 group-hover:shadow-lg group-hover:shadow-blue-500/20 transition-all duration-500">
                      {getAvatarUrl(userProfile?.avatar) ? (
                        <img 
                          src={getAvatarUrl(userProfile?.avatar)!} 
                          alt="Profile" 
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                        />
                      ) : (
                        <User className="w-4 h-4 text-gray-300 group-hover:text-blue-400 transition-colors duration-300" />
                      )}
                    </div>
                    
                    {/* Profile particles */}
                    <div className="absolute -top-1 -right-1 w-1 h-1 bg-blue-500 rounded-full animate-pulse opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
                    <div className="absolute -bottom-1 -left-1 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-0 group-hover:opacity-50 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
                    
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-xl blur opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
                  </div>
                  <span className="text-sm font-semibold group-hover:bg-gradient-to-r group-hover:from-blue-300 group-hover:via-purple-300 group-hover:to-cyan-300 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-500">
                    {user.first_name || user.username}
                  </span>
                </Link>
                
                <button
                  onClick={logout}
                  className="group flex items-center gap-2 px-4 py-2.5 text-gray-400 hover:text-red-300 hover:bg-gradient-to-r hover:from-red-500/10 hover:to-orange-500/10 rounded-xl transition-all duration-500 hover:scale-105 border border-transparent hover:border-red-500/30 relative"
                >
                  {/* Logout particles */}
                  <div className="absolute -top-0.5 left-1 w-0.5 h-0.5 bg-red-500 rounded-full animate-pulse opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="absolute -bottom-0.5 right-2 w-1 h-1 bg-orange-500 rounded-full animate-pulse opacity-0 group-hover:opacity-50 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
                  
                  <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                  <span className="text-sm font-medium">Logout</span>
                </button>
              </div>

              {/* Enhanced Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden relative p-2.5 text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-blue-500/10 hover:via-purple-500/10 hover:to-cyan-500/10 rounded-xl transition-all duration-500 hover:scale-110 group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                {/* Mobile menu button particles */}
                <div className="absolute -top-1 -right-1 w-1 h-1 bg-blue-500 rounded-full animate-pulse opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
                <div className="absolute -bottom-1 -left-1 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-0 group-hover:opacity-50 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
                
                {isMobileMenuOpen ? 
                  <X className="w-5 h-5 relative z-10 group-hover:rotate-90 transition-transform duration-300" /> : 
                  <Menu className="w-5 h-5 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                }
              </button>
            </div>
          </div>

          {/* Enhanced Mobile Menu */}
          {isMobileMenuOpen && (
            <div className="lg:hidden border-t border-gray-600/30 py-4 space-y-3 backdrop-blur-sm">
              <div className="space-y-2">
                <Link
                  to="/dashboard"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`group relative flex items-center gap-4 px-4 py-3.5 rounded-xl font-semibold text-sm transition-all duration-500 overflow-hidden ${
                    location.pathname === '/dashboard'
                      ? 'bg-gradient-to-r from-blue-500/15 via-purple-500/15 via-cyan-500/15 to-orange-500/15 text-white shadow-lg border border-blue-500/30'
                      : 'text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-blue-500/10 hover:via-purple-500/10 hover:to-cyan-500/10'
                  }`}
                >
                  <div className="p-2 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-lg group-hover:from-blue-500/20 group-hover:via-purple-500/20 group-hover:to-cyan-500/20 transition-all duration-500">
                    <Home className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <span>Dashboard</span>
                  
                  {location.pathname === '/dashboard' && (
                    <>
                      <div className="ml-auto w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full animate-pulse" />
                      {/* Dashboard mobile particles */}
                      <div className="absolute -top-1 left-8 w-1 h-1 bg-blue-500 rounded-full animate-pulse opacity-60" />
                      <div className="absolute -bottom-1 right-6 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                    </>
                  )}
                </Link>

                {/* Mobile Billing Link */}
                <Link
                  to="/billing"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`group relative flex items-center gap-4 px-4 py-3.5 rounded-xl font-semibold text-sm transition-all duration-500 overflow-hidden ${
                    location.pathname === '/billing'
                      ? 'bg-gradient-to-r from-yellow-500/15 via-green-500/15 via-blue-500/15 to-purple-500/15 text-white shadow-lg border border-yellow-500/30'
                      : 'text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-yellow-500/10 hover:via-green-500/10 hover:to-blue-500/10'
                  }`}
                >
                  <div className="p-2 bg-gradient-to-br from-yellow-500/10 via-green-500/10 to-blue-500/10 rounded-lg group-hover:from-yellow-500/20 group-hover:via-green-500/20 group-hover:to-blue-500/20 transition-all duration-500">
                    <CreditCard className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <span>Billing</span>
                  
                  {location.pathname === '/billing' && (
                    <>
                      <div className="ml-auto w-2 h-2 bg-gradient-to-r from-yellow-400 to-green-400 rounded-full animate-pulse" />
                      {/* Billing mobile particles */}
                      <div className="absolute -top-1 left-8 w-1 h-1 bg-yellow-500 rounded-full animate-pulse opacity-60" />
                      <div className="absolute -bottom-1 right-6 w-0.5 h-0.5 bg-green-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                    </>
                  )}
                </Link>
                
                {isProjectPage && (
                  <div className="relative flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-purple-500/15 via-pink-500/15 to-orange-500/15 rounded-xl border border-purple-500/20">
                    <div className="p-2 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg">
                      <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                    </div>
                    <span className="text-sm font-semibold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">Project Mode Active</span>
                    
                    {/* Project mode mobile particles */}
                    <div className="absolute -top-0.5 left-2 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-60" />
                    <div className="absolute -bottom-0.5 right-3 w-1 h-1 bg-pink-500 rounded-full animate-pulse opacity-50" style={{ animationDelay: '1s' }} />
                  </div>
                )}
              </div>
              
              <div className="border-t border-gray-600/30 pt-3 space-y-2">
                <Link
                  to="/profile"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="group relative flex items-center gap-4 px-4 py-3.5 text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-blue-500/10 hover:via-purple-500/10 hover:to-cyan-500/10 rounded-xl transition-all duration-500"
                >
                  <div className="relative">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-700 via-gray-600 to-gray-700 flex items-center justify-center overflow-hidden border border-gray-600/50 group-hover:border-blue-500/50 group-hover:shadow-lg group-hover:shadow-blue-500/20 transition-all duration-500">
                      {getAvatarUrl(userProfile?.avatar) ? (
                        <img 
                          src={getAvatarUrl(userProfile?.avatar)!} 
                          alt="Profile" 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <User className="w-4 h-4 text-gray-300 group-hover:text-blue-400 transition-colors duration-300" />
                      )}
                    </div>
                    
                    {/* Mobile profile particles */}
                    <div className="absolute -top-0.5 -right-0.5 w-1 h-1 bg-blue-500 rounded-full animate-pulse opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
                    <div className="absolute -bottom-0.5 -left-0.5 w-0.5 h-0.5 bg-purple-500 rounded-full animate-pulse opacity-0 group-hover:opacity-50 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
                  </div>
                  <div>
                    <div className="text-sm font-semibold group-hover:bg-gradient-to-r group-hover:from-blue-300 group-hover:via-purple-300 group-hover:to-cyan-300 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-500">
                      {user.first_name || user.username}
                    </div>
                    <div className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors duration-300">
                      Profile Settings
                    </div>
                  </div>
                </Link>
                
                <button
                  onClick={() => {
                    logout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="group relative flex items-center gap-4 px-4 py-3.5 w-full text-left text-gray-400 hover:text-red-300 hover:bg-gradient-to-r hover:from-red-500/10 hover:to-orange-500/10 rounded-xl transition-all duration-500 border border-transparent hover:border-red-500/30"
                >
                  <div className="p-2 bg-gradient-to-br from-red-500/10 to-orange-500/10 rounded-lg group-hover:from-red-500/20 group-hover:to-orange-500/20 transition-all duration-500">
                    <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <span className="text-sm font-medium">Logout</span>
                  
                  {/* Mobile logout particles */}
                  <div className="absolute -top-0.5 left-2 w-0.5 h-0.5 bg-red-500 rounded-full animate-pulse opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
                  <div className="absolute -bottom-0.5 right-3 w-1 h-1 bg-orange-500 rounded-full animate-pulse opacity-0 group-hover:opacity-50 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
                </button>
              </div>
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