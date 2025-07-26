import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { 
  MessageSquare, 
  Terminal as TerminalIcon, 
  Play, 
  Square, 
  ArrowLeft,
  Loader2,
  AlertCircle,
  ExternalLink,
  Globe,
  Activity,
  Clock,
  Users,
  Code,
  Server,
  Zap,
  Eye,
  Settings,
  MoreHorizontal,
  Minimize2,
  Maximize2,
  LogOut,
  User,
  Home
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ChatWithFiles from '../components/project/ChatWithFiles';
import Terminal from '../components/project/Terminal';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import { apiService } from '../services/api';
import { Project } from '../types/api';
import { useAuth } from '../contexts/AuthContext';
import '../styles/design-system.css';

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'chat');
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [terminalActivity, setTerminalActivity] = useState<string>('');
  const [hasNewTerminalActivity, setHasNewTerminalActivity] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [sessionStartTime] = useState(new Date());

  useEffect(() => {
    if (id) {
      loadProject();
    }
  }, [id]);

  // Handle tab change and URL sync
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId }, { replace: true });
  };

  // Initialize tab from URL on mount
  useEffect(() => {
    const urlTab = searchParams.get('tab');
    if (urlTab && ['chat', 'terminal'].includes(urlTab) && urlTab !== activeTab) {
      setActiveTab(urlTab);
    }
  }, []);

  // Listen for terminal activity updates
  useEffect(() => {
    const handleTerminalActivity = (event: CustomEvent) => {
      const { output, type } = event.detail;
      setTerminalActivity(output);
      
      if (activeTab !== 'terminal') {
        setHasNewTerminalActivity(true);
      }
    };

    window.addEventListener('terminal-activity', handleTerminalActivity as EventListener);
    
    return () => {
      window.removeEventListener('terminal-activity', handleTerminalActivity as EventListener);
    };
  }, [activeTab]);

  // Clear activity indicator when switching to terminal tab
  useEffect(() => {
    if (activeTab === 'terminal') {
      setHasNewTerminalActivity(false);
    }
  }, [activeTab]);

  // Handle autostart parameter
  useEffect(() => {
    const autostart = searchParams.get('autostart');
    if (autostart === 'true' && project) {
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('project-autostart', {
          detail: { 
            projectId: project.id,
            message: `🎉 Welcome to your new project "${project.name}"! Let me help you get started. What features would you like me to add first?`
          }
        }));
        setSearchParams({ tab: activeTab }, { replace: true });
      }, 2000);
    }
  }, [project]);

  const loadProject = async () => {
    if (!id) return;
    
    try {
      setIsLoading(true);
      setError(null);
      const projectData = await apiService.getProject(id);
      setProject(projectData);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartContainer = async () => {
    if (!project) return;
    
    setIsStarting(true);
    handleTabChange('terminal');
    
    window.dispatchEvent(new CustomEvent('project-container-start', {
      detail: { projectId: project.id }
    }));
    
    try {
      const response = await apiService.startContainer(project.id);
      
      if (response.status === 'starting') {
        const handleContainerStatusUpdate = (event: CustomEvent) => {
          const { status, isRunning, port, containerId } = event.detail;
          
          setProject(prev => prev ? {
            ...prev,
            is_running: isRunning,
            container_port: port || null,
            container_id: containerId || null,
            ai_generation_status: status
          } : null);
          
          if (status !== 'container_starting') {
            setIsStarting(false);
            window.removeEventListener('container-status-update', handleContainerStatusUpdate as EventListener);
          }
        };
        
        window.addEventListener('container-status-update', handleContainerStatusUpdate as EventListener);
      } else {
        setProject(prev => prev ? {
          ...prev,
          is_running: true,
          container_port: response.port || null,
          container_id: response.container_id || null
        } : null);
        setIsStarting(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start container');
      setIsStarting(false);
    }
  };

  const handleStopContainer = async () => {
    if (!project) return;
    
    window.dispatchEvent(new CustomEvent('project-container-stop', {
      detail: { projectId: project.id }
    }));
    
    setIsStopping(true);
    try {
      await apiService.stopContainer(project.id);
      setProject(prev => prev ? {
        ...prev,
        is_running: false,
        container_port: null
      } : null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to stop container');
    } finally {
      setIsStopping(false);
    }
  };

  const handleContainerStatusChange = (isRunning: boolean) => {
    setProject(prev => prev ? {
      ...prev,
      is_running: isRunning,
      container_port: isRunning ? prev.container_port : null
    } : null);
  };

  const getSessionDuration = () => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - sessionStartTime.getTime()) / (1000 * 60));
    return `${diff}m`;
  };

  const tabs = [
    { 
      id: 'chat', 
      label: 'AI Workspace', 
      icon: MessageSquare,
      description: 'Chat with AI to build your project'
    },
    { 
      id: 'terminal', 
      label: 'Terminal', 
      icon: TerminalIcon,
      description: 'Run commands and manage your application'
    }
  ];

  // Loading State
  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 dark:border-blue-800 rounded-full animate-spin">
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-blue-500 rounded-full animate-spin"></div>
            </div>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-white">Loading Project</h3>
          <p className="mt-2 text-gray-400">Getting your workspace ready...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error && !project) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Failed to Load Project</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={loadProject} variant="primary">
              Try Again
            </Button>
            <Button onClick={() => navigate('/dashboard')} variant="secondary">
              Back to Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Not Found State
  if (!project) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-yellow-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Project Not Found</h2>
          <p className="text-gray-400 mb-6">The project you're looking for doesn't exist or may have been deleted.</p>
          <Button onClick={() => navigate('/dashboard')} variant="primary">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-screen flex flex-col bg-black ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
        {/* Unified Header */}
        <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-700/50 px-4 py-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            {/* Left Section - Brand & Navigation */}
            <div className="flex items-center space-x-4 min-w-0">
              {/* Brand */}
              <button 
                onClick={() => navigate('/dashboard')}
                className="group flex items-center space-x-2 text-white hover:opacity-80 transition-opacity"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Code className="w-4 h-4 text-white" />
                </div>
                <div className="hidden md:block">
                  <div className="text-sm font-bold">Django AI Builder</div>
                </div>
              </button>

              {/* Breadcrumb */}
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <ArrowLeft className="w-3 h-3" />
                <button 
                  onClick={() => navigate('/dashboard')}
                  className="hover:text-white transition-colors"
                >
                  Dashboard
                </button>
                <span>/</span>
                <span className="font-medium text-white max-w-32 truncate">
                  {project.name}
                </span>
              </div>

              {/* Project Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${project.is_running ? 'bg-green-500' : 'bg-gray-400'}`} />
                <span className={`text-sm font-medium ${project.is_running ? 'text-green-400' : 'text-gray-400'}`}>
                  {project.is_running ? 'Running' : 'Stopped'}
                </span>
                {project.container_port && (
                  <span className="text-sm text-gray-400">
                    :{project.container_port}
                  </span>
                )}
              </div>
            </div>

            {/* Center Section - Tabs */}
            <div className="flex items-center">
              <div className="flex space-x-1 bg-gray-800/50 backdrop-blur-sm border border-gray-700/30 p-1 rounded-lg">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={`relative flex items-center space-x-1.5 px-3 py-1.5 rounded-md font-medium text-sm transition-all duration-200 ${
                        isActive 
                          ? 'bg-gray-700/50 backdrop-blur-sm text-white shadow-sm border border-gray-600/50' 
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/30'
                      }`}
                      title={tab.description}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden sm:inline">{tab.label}</span>
                      
                      {/* Activity indicator for terminal */}
                      {tab.id === 'terminal' && hasNewTerminalActivity && !isActive && (
                        <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right Section - Actions & User Menu */}
            <div className="flex items-center space-x-2 flex-shrink-0">
              {/* Project Actions */}
              {project.is_running && project.container_port && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(`http://localhost:${project.container_port}`, '_blank')}
                  className="hidden sm:flex text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                  title="View Application"
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              )}

              <button
                onClick={project.is_running ? handleStopContainer : handleStartContainer}
                disabled={isStarting || isStopping}
                className={`group relative flex items-center space-x-2 px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-300 min-w-[90px] justify-center overflow-hidden ${
                  project.is_running
                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg hover:shadow-red-500/25 disabled:bg-red-400'
                    : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg hover:shadow-green-500/25 disabled:from-gray-400 disabled:to-gray-500'
                } disabled:cursor-not-allowed transform hover:scale-105 disabled:hover:scale-100 active:scale-95`}
                title={
                  isStarting ? 'Starting container...' :
                  isStopping ? 'Stopping container...' :
                  project.is_running ? 'Stop container' : 'Start container'
                }
              >
                {/* Background Animation */}
                <div className={`absolute inset-0 transition-opacity duration-300 ${
                  isStarting || isStopping ? 'opacity-100' : 'opacity-0'
                }`}>
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                </div>
                
                {/* Content */}
                <div className="relative z-10 flex items-center space-x-2">
                  {isStarting ? (
                    <>
                      <div className="relative">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <div className="absolute inset-0 w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
                      </div>
                      <span className="hidden sm:inline">Starting...</span>
                    </>
                  ) : isStopping ? (
                    <>
                      <div className="relative">
                        <Loader2 className="w-4 h-4 animate-spin text-red-200" />
                        <div className="absolute inset-0 w-4 h-4 border-2 border-red-300/50 border-t-white rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.2s' }} />
                      </div>
                      <span className="hidden sm:inline">Stopping...</span>
                    </>
                  ) : project.is_running ? (
                    <>
                      <Square className="w-4 h-4 group-hover:animate-pulse" />
                      <span className="hidden sm:inline">Stop</span>
                      
                      {/* Pulse effect for stop */}
                      <div className="absolute inset-0 bg-red-400 rounded-lg opacity-0 group-hover:opacity-20 group-hover:animate-ping" />
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
                      <span className="hidden sm:inline">Start</span>
                      
                      {/* Shimmer effect for start */}
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                    </>
                  )}
                </div>
                
                {/* Status indicator dot */}
                <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full transition-all duration-300 ${
                  project.is_running ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                }`}>
                  {project.is_running && (
                    <div className="absolute inset-0 w-3 h-3 bg-green-400 rounded-full animate-ping opacity-40" />
                  )}
                </div>
              </button>

              {/* Divider */}
              <div className="w-px h-6 bg-gray-200 dark:bg-gray-600 mx-1" />

              {/* User Menu */}
              {user && (
                <div className="flex items-center space-x-2">
                  <div className="hidden sm:flex items-center space-x-2">
                    <div className="w-7 h-7 bg-gradient-to-br from-gray-600 to-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm text-gray-700 dark:text-gray-300 max-w-20 truncate">
                      {user.first_name || user.username}
                    </span>
                  </div>
                  
                  <button
                    onClick={logout}
                    className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              )}

              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                title="Toggle Fullscreen"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </header>

        {/* Enhanced Content Area */}
        <main className="flex-1 overflow-hidden relative">
          {error && (
            <div className="absolute top-0 left-0 right-0 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-6 py-3 z-10">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto text-red-500 hover:text-red-700 dark:hover:text-red-300"
                >
                  ×
                </button>
              </div>
            </div>
          )}

          <div className={`h-full ${error ? 'pt-12' : ''}`}>
            {activeTab === 'chat' && (
              <div className="h-full relative">
                <ChatWithFiles projectId={project.id} />
                
                {/* Enhanced Mini Terminal Preview */}
                {terminalActivity && hasNewTerminalActivity && (
                  <div className="absolute bottom-6 right-6 w-96 max-w-[calc(100vw-3rem)] bg-gray-900 dark:bg-gray-800 border border-gray-700 dark:border-gray-600 rounded-xl shadow-2xl z-50 overflow-hidden">
                    <div className="bg-gray-800 dark:bg-gray-700 px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <TerminalIcon className="w-4 h-4 text-green-400" />
                        <span className="text-sm text-white dark:text-gray-200 font-medium">Terminal Activity</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleTabChange('terminal')}
                          className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                          Open Terminal
                        </button>
                        <button
                          onClick={() => setHasNewTerminalActivity(false)}
                          className="p-1 text-gray-400 hover:text-white dark:hover:text-gray-200 transition-colors"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                    <div className="p-4 font-mono text-xs text-gray-300 dark:text-gray-400 bg-black dark:bg-gray-900 max-h-32 overflow-y-auto">
                      <div className="whitespace-pre-wrap">
                        {terminalActivity.split('\n').slice(-10).join('\n')}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'terminal' && (
              <div className="h-full">
                <Terminal 
                  projectId={project.id} 
                  isProjectRunning={project.is_running}
                  onContainerStatusChange={handleContainerStatusChange}
                />
              </div>
            )}
          </div>
        </main>
      </div>
  );
};

export default ProjectDetail;