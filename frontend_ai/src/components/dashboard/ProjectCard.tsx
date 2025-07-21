import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Square, MessageSquare, FileText, Calendar, Settings, Trash2, Loader2, Terminal } from 'lucide-react';
import { Project } from '../../types/api';
import { apiService } from '../../services/api';
import { useState } from 'react';

interface ProjectCardProps {
  project: Project;
  viewMode: 'grid' | 'list';
  onProjectDeleted: (projectId: string) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, viewMode, onProjectDeleted }) => {
  const navigate = useNavigate();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [containerStatus, setContainerStatus] = useState({
    is_running: project.is_running,
    container_port: project.container_port
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'generating': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'generating': return 'Generating...';
      case 'error': return 'Error';
      default: return 'Ready';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleStartContainer = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsStarting(true);
    
    // Navigate to terminal tab immediately to show live streaming
    navigate(`/project/${project.id}?tab=terminal`);
    
    try {
      const response = await apiService.startContainer(project.id);
      setContainerStatus({
        is_running: true,
        container_port: response.port
      });
    } catch (error) {
      console.error('Failed to start container:', error);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopContainer = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsStopping(true);
    try {
      await apiService.stopContainer(project.id);
      setContainerStatus({
        is_running: false,
        container_port: null
      });
    } catch (error) {
      console.error('Failed to stop container:', error);
    } finally {
      setIsStopping(false);
    }
  };

  const handleDeleteProject = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete "${project.name}"? This action cannot be undone.`)) {
      return;
    }
    
    setIsDeleting(true);
    try {
      await apiService.deleteProject(project.id);
      onProjectDeleted(project.id);
    } catch (error) {
      console.error('Failed to delete project:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCardClick = () => {
    navigate(`/project/${project.id}`);
  };

  if (viewMode === 'list') {
    return (
      <div 
        onClick={handleCardClick}
        className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-500 transition-all cursor-pointer"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-4">
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">{project.name}</h3>
                <p className="text-gray-400 text-sm">{project.description}</p>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span className={getStatusColor(project.ai_generation_status)}>
                  {getStatusText(project.ai_generation_status)}
                </span>
                <span>{project.files_count} files</span>
                <span className={containerStatus.is_running ? 'text-green-400' : 'text-gray-400'}>
                  {containerStatus.is_running ? `Running on :${containerStatus.container_port}` : 'Stopped'}
                </span>
                <span>{formatDate(project.updated_at)}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              onClick={containerStatus.is_running ? handleStopContainer : handleStartContainer}
              disabled={isStarting || isStopping}
              className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            >
              {isStarting || isStopping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : containerStatus.is_running ? (
                <Square className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/project/${project.id}?tab=chat`);
              }}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <MessageSquare className="w-5 h-5" />
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/project/${project.id}?tab=files`);
              }}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <FileText className="w-5 h-5" />
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/project/${project.id}?tab=terminal`);
              }}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <Terminal className="w-5 h-5" />
            </button>
            <button 
              onClick={handleDeleteProject}
              disabled={isDeleting}
              className="p-2 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Trash2 className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      onClick={handleCardClick}
      className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-500 transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-2">{project.name}</h3>
          <p className="text-gray-400 text-sm line-clamp-2">{project.description}</p>
        </div>
        <div className="flex items-center space-x-1 ml-4">
          <button 
            onClick={containerStatus.is_running ? handleStopContainer : handleStartContainer}
            disabled={isStarting || isStopping}
            className="p-1.5 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            {isStarting || isStopping ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : containerStatus.is_running ? (
              <Square className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
          <button 
            onClick={handleDeleteProject}
            disabled={isDeleting}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
          >
            {isDeleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Status</span>
          <span className={getStatusColor(project.ai_generation_status)}>
            {getStatusText(project.ai_generation_status)}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Container</span>
          <span className={containerStatus.is_running ? 'text-green-400' : 'text-gray-400'}>
            {containerStatus.is_running ? `Running :${containerStatus.container_port}` : 'Stopped'}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Files</span>
          <span className="text-white">{project.files_count}</span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Updated</span>
          <span className="text-white">{formatDate(project.updated_at)}</span>
        </div>
      </div>

      <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-700">
        <button 
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/project/${project.id}?tab=chat`);
          }}
          className="flex-1 flex items-center justify-center space-x-2 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm">Chat</span>
        </button>
        <button 
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/project/${project.id}?tab=files`);
          }}
          className="flex-1 flex items-center justify-center space-x-2 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <FileText className="w-4 h-4" />
          <span className="text-sm">Files</span>
        </button>
        <button 
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/project/${project.id}?tab=terminal`);
          }}
          className="flex-1 flex items-center justify-center space-x-2 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <Terminal className="w-4 h-4" />
          <span className="text-sm">Terminal</span>
        </button>
        {containerStatus.is_running && containerStatus.container_port && (
          <button 
            onClick={(e) => {
              e.stopPropagation();
              window.open(`http://localhost:${containerStatus.container_port}`, '_blank');
            }}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm"
          >
            View App
          </button>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;