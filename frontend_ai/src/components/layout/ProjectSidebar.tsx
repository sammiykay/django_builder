import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Folder, 
  Play, 
  Square, 
  ExternalLink, 
  Settings, 
  Trash2, 
  Clock, 
  Code, 
  Database,
  ChevronRight,
  Plus,
  Search,
  Sparkles
} from 'lucide-react';
import { Project } from '../../types/api';
import { apiService } from '../../services/api';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
  life: number;
}

interface ProjectSidebarProps {
  isVisible: boolean;
  onClose?: () => void;
}

// Memoized Project Item Component for better performance
const ProjectItem = React.memo<{
  project: Project;
  index: number;
  isVisible: boolean;
  hoveredProject: string | null;
  onProjectClick: (projectId: string) => void;
  onStartContainer: (e: React.MouseEvent, projectId: string) => void;
  onStopContainer: (e: React.MouseEvent, projectId: string) => void;
  onMouseEnter: (projectId: string) => void;
  onMouseLeave: () => void;
  getProjectTypeIcon: (project: Project) => React.ReactNode;
  getStatusColor: (project: Project) => string;
  formatDate: (dateString: string) => string;
}>(({ 
  project, 
  index, 
  isVisible, 
  hoveredProject, 
  onProjectClick, 
  onStartContainer, 
  onStopContainer, 
  onMouseEnter, 
  onMouseLeave, 
  getProjectTypeIcon, 
  getStatusColor, 
  formatDate 
}) => {
  const navigate = useNavigate();
  
  return (
    <div
      className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-300 transform hover:scale-[1.02] backdrop-blur-sm border overflow-hidden ${
        hoveredProject === project.id
          ? 'bg-gradient-to-br from-gray-800/80 to-gray-700/80 shadow-xl shadow-blue-500/20 border-blue-500/40 translate-y-0'
          : 'bg-gradient-to-br from-gray-800/40 to-gray-700/40 hover:from-gray-800/60 hover:to-gray-700/60 border-gray-600/30 hover:border-gray-500/50'
      }`}
      style={{
        animationDelay: isVisible ? `${index * 100}ms` : '0ms',
      }}
      onClick={() => onProjectClick(project.id)}
      onMouseEnter={() => onMouseEnter(project.id)}
      onMouseLeave={onMouseLeave}
    >
      {/* Animated background gradient on hover */}
      <div className={`absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
      
      {/* Shimmer effect */}
      <div className={`absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/5 to-transparent ${hoveredProject === project.id ? 'animate-pulse' : ''}`} />
      
      {/* Project Content - Relative positioning to appear above effects */}
      <div className="relative z-10">
        {/* Project Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className={`relative p-2.5 rounded-xl bg-gradient-to-br from-gray-700/50 to-gray-600/50 backdrop-blur-sm border border-gray-500/30 ${getStatusColor(project)} transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg`}>
              {getProjectTypeIcon(project)}
              {project.is_running && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-white font-semibold truncate group-hover:text-blue-300 transition-colors duration-300 text-base">
                {project.name}
              </h3>
              <p className="text-gray-400 text-xs truncate group-hover:text-gray-300 transition-colors duration-300">
                {project.description || 'No description'}
              </p>
            </div>
          </div>

          {/* Enhanced Status Indicator */}
          <div className="flex items-center space-x-2">
            {project.is_running && (
              <div className="relative">
                <div className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
                <div className="absolute inset-0 w-2.5 h-2.5 bg-green-400 rounded-full animate-ping opacity-30"></div>
              </div>
            )}
            <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-blue-400 group-hover:translate-x-1 transition-all duration-300" />
          </div>
        </div>

        {/* Enhanced Project Meta */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4 text-gray-500 group-hover:text-gray-400 transition-colors duration-300">
            <span className="flex items-center space-x-1.5">
              <Clock className="w-3 h-3" />
              <span>{formatDate(project.updated_at)}</span>
            </span>
            <span className="px-2 py-1 bg-gray-700/50 rounded-md text-gray-400 capitalize font-medium">
              {project.complexity_level}
            </span>
          </div>

          {/* Enhanced Quick Actions */}
          <div 
            className={`flex items-center space-x-1 transition-all duration-300 ${
              hoveredProject === project.id 
                ? 'opacity-100 translate-x-0' 
                : 'opacity-0 translate-x-2'
            }`}
          >
            {project.is_running ? (
              <button
                onClick={(e) => onStopContainer(e, project.id)}
                className="p-1.5 hover:bg-red-500/20 bg-red-500/10 rounded-lg transition-all duration-300 hover:scale-110 border border-red-500/20 hover:border-red-500/40"
                title="Stop Container"
              >
                <Square className="w-3 h-3 text-red-400" />
              </button>
            ) : (
              <button
                onClick={(e) => onStartContainer(e, project.id)}
                className="p-1.5 hover:bg-green-500/20 bg-green-500/10 rounded-lg transition-all duration-300 hover:scale-110 border border-green-500/20 hover:border-green-500/40"
                title="Start Container"
              >
                <Play className="w-3 h-3 text-green-400" />
              </button>
            )}

            <button
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/project/${project.id}/settings`);
              }}
              className="p-1.5 hover:bg-gray-500/20 bg-gray-500/10 rounded-lg transition-all duration-300 hover:scale-110 border border-gray-500/20 hover:border-gray-500/40"
              title="Settings"
            >
              <Settings className="w-3 h-3 text-gray-400 hover:text-white" />
            </button>
          </div>
        </div>

        {/* Enhanced Progress Bar for Generating Projects */}
        {project.ai_generation_status === 'generating' && (
          <div className="mt-3 space-y-2">
            <div className="relative w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full"></div>
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full animate-pulse shadow-lg shadow-blue-500/30 transition-all duration-300" 
                style={{ width: '60%' }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
            </div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-3 h-3 text-blue-400 animate-pulse" />
              <p className="text-xs text-blue-400 font-medium">AI is generating your project...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

ProjectItem.displayName = 'ProjectItem';

const ProjectSidebar: React.FC<ProjectSidebarProps> = ({ isVisible, onClose }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [hoveredProject, setHoveredProject] = useState<string | null>(null);
  const [shouldRender, setShouldRender] = useState(false);
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number>();
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Control rendering to avoid empty sidebar showing
  React.useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
    } else {
      // Delay unmounting to allow exit animation
      const timeout = setTimeout(() => setShouldRender(false), 400);
      return () => clearTimeout(timeout);
    }
  }, [isVisible]);

  // Highly optimized particle system with better performance controls
  useEffect(() => {
    if (!isVisible) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Use willReadFrequently for better performance when reading canvas data
    const contextOptions = { willReadFrequently: false };
    
    const resizeCanvas = () => {
      canvas.width = 320; // Sidebar width
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas, { passive: true });

    // Further reduced particles for optimal performance
    const colors = ['#3B82F6', '#8B5CF6', '#06B6D4', '#10B981'];
    particlesRef.current = Array.from({ length: 10 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.15, // Reduced velocity for smoother animation
      vy: (Math.random() - 0.5) * 0.15,
      size: Math.random() * 1 + 0.3, // Slightly smaller particles
      opacity: Math.random() * 0.15 + 0.08, // Reduced opacity for better performance
      color: colors[Math.floor(Math.random() * colors.length)],
      life: Math.random() * 400 + 300 // Longer life for fewer regenerations
    }));

    let lastTime = 0;
    let frameCount = 0;
    const targetFPS = 24; // Further reduced FPS for optimal performance
    const frameInterval = 1000 / targetFPS;

    const animate = (currentTime: number) => {
      if (currentTime - lastTime < frameInterval) {
        if (isVisible) {
          animationRef.current = requestAnimationFrame(animate);
        }
        return;
      }
      lastTime = currentTime;
      frameCount++;

      // Only clear and redraw every other frame for better performance
      if (frameCount % 2 === 0) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      // Batch particle updates for efficiency
      const updateParticlesBatch = () => {
        const particles = particlesRef.current;
        const particleCount = particles.length;
        
        // Use a single loop for all particle operations
        for (let i = 0; i < particleCount; i++) {
          const particle = particles[i];
          
          // Update position
          particle.x += particle.vx;
          particle.y += particle.vy;
          particle.life--;

          // Efficient edge wrapping
          if (particle.x < 0) particle.x = canvas.width;
          else if (particle.x > canvas.width) particle.x = 0;
          if (particle.y < 0) particle.y = canvas.height;
          else if (particle.y > canvas.height) particle.y = 0;

          // Regenerate particle less frequently
          if (particle.life <= 0) {
            Object.assign(particle, {
              x: Math.random() * canvas.width,
              y: Math.random() * canvas.height,
              life: Math.random() * 400 + 300,
              opacity: Math.random() * 0.15 + 0.08
            });
          }

          // Efficient particle rendering
          ctx.fillStyle = particle.color;
          ctx.globalAlpha = particle.opacity;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();

          // Optimized connection rendering (reduced calculations)
          if (i < particleCount - 1) {
            const maxConnections = Math.min(2, particleCount - i - 1);
            for (let j = 1; j <= maxConnections; j++) {
              const other = particles[i + j];
              const dx = particle.x - other.x;
              const dy = particle.y - other.y;
              const distSq = dx * dx + dy * dy;

              if (distSq < 3600) { // Reduced connection distance
                ctx.strokeStyle = particle.color;
                ctx.globalAlpha = 0.03 * (1 - distSq / 3600);
                ctx.lineWidth = 0.2;
                ctx.beginPath();
                ctx.moveTo(particle.x, particle.y);
                ctx.lineTo(other.x, other.y);
                ctx.stroke();
              }
            }
          }
        }
      };

      // Use requestIdleCallback for better performance on busy threads
      if (window.requestIdleCallback && frameCount % 3 === 0) {
        window.requestIdleCallback(updateParticlesBatch, { timeout: 8 });
      } else {
        updateParticlesBatch();
      }

      ctx.globalAlpha = 1;
      if (isVisible) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isVisible]);

  useEffect(() => {
    if (isVisible) {
      loadProjects();
    }
  }, [isVisible]);

  // Memoized functions for better performance
  const loadProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getProjects();
      setProjects(response.results || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleProjectClick = useCallback((projectId: string) => {
    navigate(`/project/${projectId}`);
    onClose?.();
  }, [navigate, onClose]);

  const handleStartContainer = useCallback(async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    try {
      await apiService.startContainer(projectId);
      // Update the specific project in the state immediately for better UX
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, is_running: true } : p
      ));
    } catch (error) {
      console.error('Failed to start container:', error);
    }
  }, []);

  const handleStopContainer = useCallback(async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    try {
      await apiService.stopContainer(projectId);
      // Update the specific project in the state immediately for better UX
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, is_running: false } : p
      ));
    } catch (error) {
      console.error('Failed to stop container:', error);
    }
  }, []);

  // Memoized filtered projects for better performance
  const filteredProjects = useMemo(() => {
    if (!searchTerm.trim()) return projects;
    const term = searchTerm.toLowerCase();
    return projects.filter(project =>
      project.name.toLowerCase().includes(term) ||
      project.description?.toLowerCase().includes(term)
    );
  }, [projects, searchTerm]);

  // Memoized utility functions
  const getProjectTypeIcon = useCallback((project: Project) => {
    switch (project.project_type) {
      case 'api':
        return <Database className="w-4 h-4" />;
      case 'blog':
        return <Code className="w-4 h-4" />;
      default:
        return <Folder className="w-4 h-4" />;
    }
  }, []);

  const getStatusColor = useCallback((project: Project) => {
    if (project.is_running) return 'text-green-400';
    if (project.ai_generation_status === 'generating') return 'text-blue-400';
    if (project.ai_generation_status === 'error') return 'text-red-400';
    if (project.ai_generation_status === 'completed') return 'text-gray-400';
    return 'text-gray-500';
  }, []);

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  }, []);

  // Don't render anything if sidebar shouldn't be shown
  if (!shouldRender) return null;

  return (
    <>
      {/* Backdrop */}
      {isVisible && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full w-80 bg-gradient-to-br from-gray-900/95 via-gray-800/95 to-gray-900/95 backdrop-blur-xl border-r border-gray-600/50 z-50 transform transition-all duration-500 ease-out shadow-2xl flex flex-col overflow-hidden ${
          isVisible ? 'translate-x-0 opacity-100 scale-100' : '-translate-x-full opacity-0 scale-95'
        }`}
        style={{
          background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(31, 41, 55, 0.95) 50%, rgba(17, 24, 39, 0.95) 100%)',
          boxShadow: isVisible ? '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 100px rgba(59, 130, 246, 0.15)' : 'none'
        }}
        onMouseLeave={() => {
          // Add a small delay to prevent immediate closing
          setTimeout(() => onClose?.(), 100);
        }}
        onTouchStart={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
      >
        {/* Animated Background Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none z-0"
          style={{ filter: 'blur(0.5px)' }}
        />

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-cyan-500/5 pointer-events-none z-10" />

        {/* Content Container */}
        <div className="relative z-20 flex flex-col h-full">
          {/* Header */}
          <div className="flex-shrink-0 p-6 border-b border-gray-600/30 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl backdrop-blur-sm border border-blue-500/30">
                  <Sparkles className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  Projects
                </h2>
              </div>
              <button
                onClick={() => navigate('/dashboard')}
                className="group p-2 bg-gradient-to-br from-gray-800/50 to-gray-700/50 hover:from-blue-500/20 hover:to-purple-500/20 rounded-xl backdrop-blur-sm border border-gray-600/30 hover:border-blue-500/50 transition-all duration-300"
                title="Create New Project"
              >
                <Plus className="w-5 h-5 text-gray-400 group-hover:text-blue-400 transition-colors duration-300" />
              </button>
            </div>

            {/* Enhanced Search */}
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-blue-400 w-4 h-4 transition-colors duration-300" />
              <input
                type="text"
                placeholder="Search projects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-gray-800/50 backdrop-blur-sm border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-gray-800/70 transition-all duration-300 text-sm"
              />
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none" />
            </div>
          </div>

          {/* Enhanced Projects List with Optimized Scrolling */}
          <div 
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto min-h-0 scroll-smooth"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: 'rgba(59, 130, 246, 0.3) transparent'
            }}
          >
            {isLoading ? (
              <div className="p-6 text-center">
                <div className="relative">
                  <div className="animate-spin rounded-full h-10 w-10 border-2 border-transparent border-t-blue-500 border-r-purple-500 mx-auto mb-4"></div>
                  <div className="absolute inset-0 rounded-full h-10 w-10 border-2 border-transparent border-b-cyan-500 border-l-green-500 mx-auto animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                </div>
                <p className="text-gray-300 font-medium">Loading projects...</p>
                <p className="text-gray-500 text-sm mt-1">Preparing your workspace</p>
              </div>
            ) : filteredProjects.length === 0 ? (
              <div className="p-6 text-center">
                <div className="relative mb-4">
                  <div className="w-16 h-16 mx-auto bg-gradient-to-br from-gray-700 to-gray-800 rounded-2xl flex items-center justify-center">
                    <Folder className="w-8 h-8 text-gray-500" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full opacity-75 animate-pulse"></div>
                </div>
                <p className="text-gray-300 font-medium mb-2">
                  {searchTerm ? 'No projects match your search' : 'No projects yet'}
                </p>
                <p className="text-gray-500 text-sm mb-4">
                  {searchTerm ? 'Try a different search term' : 'Start building something amazing'}
                </p>
                {!searchTerm && (
                  <button
                    onClick={() => {
                      navigate('/dashboard');
                      onClose?.();
                    }}
                    className="group inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 border border-blue-500/30 hover:border-blue-500/50 rounded-xl transition-all duration-300"
                  >
                    <Plus className="w-4 h-4 text-blue-400 group-hover:text-blue-300" />
                    <span className="text-blue-400 group-hover:text-blue-300 text-sm font-medium">Create your first project</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="p-3 space-y-3">
                {filteredProjects.map((project, index) => (
                  <ProjectItem
                    key={project.id}
                    project={project}
                    index={index}
                    isVisible={isVisible}
                    hoveredProject={hoveredProject}
                    onProjectClick={handleProjectClick}
                    onStartContainer={handleStartContainer}
                    onStopContainer={handleStopContainer}
                    onMouseEnter={setHoveredProject}
                    onMouseLeave={() => setHoveredProject(null)}
                    getProjectTypeIcon={getProjectTypeIcon}
                    getStatusColor={getStatusColor}
                    formatDate={formatDate}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Enhanced Footer */}
          <div className="flex-shrink-0 p-4 border-t border-gray-600/30 backdrop-blur-sm">
            <div className="flex items-center justify-center space-x-2">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-400 font-medium">
                  {filteredProjects.length} {filteredProjects.length === 1 ? 'project' : 'projects'}
                </span>
              </div>
              {searchTerm && (
                <span className="text-xs text-gray-500">• filtered</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// Memoize the main component for better performance
export default React.memo(ProjectSidebar);