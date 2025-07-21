import React, { useState, useEffect } from 'react';
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
  Search
} from 'lucide-react';
import { Project } from '../../types/api';
import { apiService } from '../../services/api';

interface ProjectSidebarProps {
  isVisible: boolean;
  onClose?: () => void;
}

const ProjectSidebar: React.FC<ProjectSidebarProps> = ({ isVisible, onClose }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [hoveredProject, setHoveredProject] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isVisible) {
      loadProjects();
    }
  }, [isVisible]);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getProjects();
      setProjects(response.results);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProjectClick = (projectId: string) => {
    navigate(`/project/${projectId}`);
    onClose?.();
  };

  const handleStartContainer = async (e: React.MouseEvent, projectId: string) => {
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
  };

  const handleStopContainer = async (e: React.MouseEvent, projectId: string) => {
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
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getProjectTypeIcon = (project: Project) => {
    switch (project.project_type) {
      case 'api':
        return <Database className="w-4 h-4" />;
      case 'blog':
        return <Code className="w-4 h-4" />;
      default:
        return <Folder className="w-4 h-4" />;
    }
  };

  const getStatusColor = (project: Project) => {
    if (project.is_running) return 'text-green-400';
    if (project.ai_generation_status === 'generating') return 'text-blue-400';
    if (project.ai_generation_status === 'error') return 'text-red-400';
    if (project.ai_generation_status === 'completed') return 'text-gray-400';
    return 'text-gray-500';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

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
        className={`fixed left-0 top-0 h-full w-80 bg-gradient-to-b from-gray-900 to-gray-800 border-r border-gray-700 z-50 transform transition-all duration-300 ease-in-out shadow-2xl flex flex-col ${
          isVisible ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Projects</h2>
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5 text-gray-400 hover:text-white" />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
        </div>

        {/* Projects List */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {isLoading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
              <p className="text-gray-400">Loading projects...</p>
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="p-6 text-center">
              <Folder className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 mb-2">
                {searchTerm ? 'No projects match your search' : 'No projects yet'}
              </p>
              {!searchTerm && (
                <button
                  onClick={() => {
                    navigate('/dashboard');
                    onClose?.();
                  }}
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  Create your first project
                </button>
              )}
            </div>
          ) : (
            <div className="p-3 space-y-2">
              {filteredProjects.map((project, index) => (
                <div
                  key={project.id}
                  className={`group relative p-3 rounded-lg cursor-pointer transition-all duration-200 transform hover:scale-[1.02] animate-in slide-in-from-left ${
                    hoveredProject === project.id
                      ? 'bg-gray-800 shadow-lg shadow-blue-500/20 border border-blue-500/30'
                      : 'bg-gray-800/50 hover:bg-gray-800 border border-transparent hover:border-gray-700'
                  }`}
                  style={{
                    animationDelay: isVisible ? `${index * 50}ms` : '0ms',
                    animationDuration: '300ms'
                  }}
                  onClick={() => handleProjectClick(project.id)}
                  onMouseEnter={() => setHoveredProject(project.id)}
                  onMouseLeave={() => setHoveredProject(null)}
                >
                  {/* Project Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <div className={`p-2 rounded-lg bg-gray-700 ${getStatusColor(project)}`}>
                        {getProjectTypeIcon(project)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium truncate group-hover:text-blue-300 transition-colors">
                          {project.name}
                        </h3>
                        <p className="text-gray-400 text-xs truncate">
                          {project.description || 'No description'}
                        </p>
                      </div>
                    </div>

                    {/* Status Indicator */}
                    <div className="flex items-center space-x-1">
                      {project.is_running && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      )}
                      <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-white transition-colors" />
                    </div>
                  </div>

                  {/* Project Meta */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center space-x-4">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(project.updated_at)}</span>
                      </span>
                      <span className="capitalize">{project.complexity_level}</span>
                    </div>

                    {/* Quick Actions */}
                    <div 
                      className={`flex items-center space-x-1 transition-opacity duration-200 ${
                        hoveredProject === project.id ? 'opacity-100' : 'opacity-0'
                      }`}
                    >
                      {project.is_running ? (
                        <button
                          onClick={(e) => handleStopContainer(e, project.id)}
                          className="p-1 hover:bg-red-600 rounded transition-colors"
                          title="Stop Container"
                        >
                          <Square className="w-3 h-3 text-red-400" />
                        </button>
                      ) : (
                        <button
                          onClick={(e) => handleStartContainer(e, project.id)}
                          className="p-1 hover:bg-green-600 rounded transition-colors"
                          title="Start Container"
                        >
                          <Play className="w-3 h-3 text-green-400" />
                        </button>
                      )}

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/project/${project.id}/settings`);
                          onClose?.();
                        }}
                        className="p-1 hover:bg-gray-600 rounded transition-colors"
                        title="Settings"
                      >
                        <Settings className="w-3 h-3 text-gray-400" />
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar for Generating Projects */}
                  {project.ai_generation_status === 'generating' && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-700 rounded-full h-1">
                        <div className="bg-blue-500 h-1 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                      <p className="text-xs text-blue-400 mt-1">Generating...</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t border-gray-700">
          <div className="text-xs text-gray-500 text-center">
            {filteredProjects.length} {filteredProjects.length === 1 ? 'project' : 'projects'}
          </div>
        </div>
      </div>
    </>
  );
};

export default ProjectSidebar;