import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { 
  MessageSquare, 
  Terminal as TerminalIcon, 
  Play, 
  Square, 
  Settings,
  ArrowLeft,
  Loader2,
  AlertCircle,
  ExternalLink,
  Globe
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ChatWithFiles from '../components/project/ChatWithFiles';
import Terminal from '../components/project/Terminal';
import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import { apiService } from '../services/api';
import { Project } from '../types/api';
import '../styles/design-system.css';

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'chat');
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [terminalActivity, setTerminalActivity] = useState<string>('');
  const [hasNewTerminalActivity, setHasNewTerminalActivity] = useState(false);

  useEffect(() => {
    if (id) {
      loadProject();
    }
  }, [id]);


  // Handle tab change and URL sync
  const handleTabChange = (tabId: string) => {
    console.log('Changing tab to:', tabId);
    setActiveTab(tabId);
    setSearchParams({ tab: tabId }, { replace: true });
  };

  // Initialize tab from URL on mount
  useEffect(() => {
    const urlTab = searchParams.get('tab');
    if (urlTab && ['chat', 'terminal'].includes(urlTab) && urlTab !== activeTab) {
      console.log('Setting tab from URL:', urlTab);
      setActiveTab(urlTab);
    }
  }, []); // Only run on mount

  // Listen for terminal activity updates
  useEffect(() => {
    const handleTerminalActivity = (event: CustomEvent) => {
      const { output, type } = event.detail;
      setTerminalActivity(output);
      
      // Only show notification if not on terminal tab
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
      // Send a welcome message to trigger streaming
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('project-autostart', {
          detail: { 
            projectId: project.id,
            message: `🎉 Welcome to your new project "${project.name}"! Let me help you get started. What features would you like me to add first?`
          }
        }));
        // Remove autostart from URL
        setSearchParams({ tab: activeTab }, { replace: true });
      }, 2000);
    }
  }, [project]); // Only depend on project

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
    
    // Switch to terminal tab to show live streaming
    handleTabChange('terminal');
    
    // Notify terminal about the status change
    window.dispatchEvent(new CustomEvent('project-container-start', {
      detail: { projectId: project.id }
    }));
    
    try {
      const response = await apiService.startContainer(project.id);
      
      if (response.status === 'starting') {
        // Listen for WebSocket container status updates instead of polling
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
        // Immediate response
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
    
    // Notify terminal about the stop action
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

  const handleGenerationComplete = () => {
    // Reload project data after generation
    loadProject();
  };

  const handleContainerStatusChange = (isRunning: boolean) => {
    // Update project state when terminal changes container status
    setProject(prev => prev ? {
      ...prev,
      is_running: isRunning,
      container_port: isRunning ? prev.container_port : null
    } : null);
  };

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'terminal', label: 'Terminal', icon: TerminalIcon }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-primary flex items-center justify-center">
        <Card className="text-center max-w-md mx-auto">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold text-primary mb-1">Loading Project</h3>
              <p className="text-secondary">Please wait while we fetch your project details...</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="min-h-screen bg-primary flex items-center justify-center p-4">
        <Card className="text-center max-w-md mx-auto">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="w-12 h-12 text-red-500" />
            <div>
              <h2 className="text-xl font-semibold text-primary mb-2">Failed to Load Project</h2>
              <p className="text-secondary mb-6">{error}</p>
            </div>
            <div className="flex gap-3">
              <Button onClick={loadProject} variant="primary">
                Retry
              </Button>
              <Button onClick={() => navigate('/dashboard')} variant="secondary">
                Back to Dashboard
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-primary flex items-center justify-center p-4">
        <Card className="text-center max-w-md mx-auto">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="w-12 h-12 text-yellow-500" />
            <div>
              <h2 className="text-xl font-semibold text-primary mb-2">Project Not Found</h2>
              <p className="text-secondary mb-6">The project you're looking for doesn't exist or may have been deleted.</p>
            </div>
            <Button onClick={() => navigate('/dashboard')} variant="primary">
              Back to Dashboard
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <AppLayout>
      <div className="bg-primary text-primary">
        {/* Project Header */}
        <div className="bg-secondary border-b border-secondary">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              {/* Left Section - Project Info */}
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => navigate('/dashboard')}
                  icon={<ArrowLeft className="w-4 h-4" />}
                  className="text-secondary hover:text-primary flex-shrink-0"
                >
                  <span className="hidden sm:inline">Back</span>
                </Button>
                
                <div className="min-w-0 flex-1">
                  <h1 className="text-xl sm:text-2xl font-bold text-primary leading-tight truncate">
                    {project.name}
                  </h1>
                  <div className="flex items-center gap-3 mt-2">
                    <Badge 
                      variant={project.is_running ? 'success' : 'neutral'}
                      size="sm"
                    >
                      {project.is_running ? '🟢 Running' : '⭕ Stopped'}
                    </Badge>
                    {project.container_port && (
                      <span className="text-sm text-tertiary hidden sm:inline">
                        Port {project.container_port}
                      </span>
                    )}
                    {error && (
                      <Badge variant="error" size="sm" className="hidden sm:flex">
                        {error}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Section - Actions */}
              <div className="flex items-center gap-2 flex-shrink-0">
                {project.is_running && project.container_port && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => window.open(`http://localhost:${project.container_port}`, '_blank')}
                    icon={<ExternalLink className="w-4 h-4" />}
                  >
                    <span className="hidden sm:inline">View App</span>
                  </Button>
                )}

                <Button
                  variant={project.is_running ? 'danger' : 'primary'}
                  size="sm"
                  onClick={project.is_running ? handleStopContainer : handleStartContainer}
                  loading={isStarting || isStopping}
                  icon={
                    isStarting || isStopping ? undefined :
                    project.is_running ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />
                  }
                >
                  {isStarting ? 'Starting...' : 
                   isStopping ? 'Stopping...' : 
                   project.is_running ? 'Stop' : 'Start'}
                </Button>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="mt-6 border-t border-primary/10 pt-4">
              <nav className="flex gap-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={`
                        flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all relative
                        ${isActive 
                          ? 'bg-primary text-primary shadow-sm border border-primary/20' 
                          : 'text-secondary hover:text-primary hover:bg-tertiary/30'
                        }
                      `}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                      {/* Activity indicator for terminal tab */}
                      {tab.id === 'terminal' && hasNewTerminalActivity && !isActive && (
                        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse">
                          <div className="absolute inset-0 w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                        </div>
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <main className="h-[calc(100vh-12rem)] relative">
          {console.log('Current activeTab:', activeTab)}
          {activeTab === 'chat' && (
            <div className="h-full">
              <ChatWithFiles projectId={project.id} />
              
              {/* Mini Terminal Preview - Show when there's activity and not on terminal tab */}
              {terminalActivity && hasNewTerminalActivity && (
                <div className="absolute bottom-4 right-4 w-96 max-w-[calc(100vw-2rem)] bg-gray-900 border border-gray-600 rounded-lg shadow-2xl z-50">
                  <div className="bg-gray-800 px-3 py-2 rounded-t-lg flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TerminalIcon className="w-4 h-4 text-green-400" />
                      <span className="text-sm text-white font-medium">Terminal Activity</span>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleTabChange('terminal')}
                        className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                      >
                        Open Terminal
                      </button>
                      <button
                        onClick={() => setHasNewTerminalActivity(false)}
                        className="p-1 text-gray-400 hover:text-white transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                  <div className="p-3 font-mono text-xs text-gray-300 bg-black max-h-32 overflow-y-auto">
                    <div className="whitespace-pre-wrap">
                      {terminalActivity.split('\n').slice(-10).join('\n')}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          {activeTab === 'terminal' && (
            <Terminal 
              projectId={project.id} 
              isProjectRunning={project.is_running}
              onContainerStatusChange={handleContainerStatusChange}
            />
          )}
        </main>
      </div>
    </AppLayout>
  );
};

export default ProjectDetail;