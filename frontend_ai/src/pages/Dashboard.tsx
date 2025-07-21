import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Folder, 
  Clock, 
  Play, 
  Square, 
  ExternalLink,
  Trash2,
  Settings
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import QuickCreateWidget from '../components/dashboard/QuickCreateWidget';
import CreateProjectModal from '../components/dashboard/CreateProjectModal';
import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { apiService } from '../services/api';
import { Project } from '../types/api';
import '../styles/design-system.css';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const projectList = await apiService.getProjects();
      setProjects(projectList || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProjectCreated = () => {
    loadProjects();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <AppLayout>
      <div className="min-h-screen bg-primary">
        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
          {/* Quick Create Section */}
          <QuickCreateWidget onProjectCreated={handleProjectCreated} />

          {/* Projects Section */}
          {!isLoading && projects.length > 0 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-primary">Your Projects</h2>
                  <p className="text-secondary mt-1">
                    Manage and explore your Django applications
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => setIsCreateModalOpen(true)}
                  icon={<Plus className="w-4 h-4" />}
                >
                  New Project
                </Button>
              </div>

              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {projects.map((project) => (
                  <Card 
                    key={project.id} 
                    className="group hover:border-blue-500/50 transition-all duration-200 cursor-pointer"
                    onClick={() => navigate(`/project/${project.id}`)}
                    elevated
                  >
                    <div className="space-y-4">
                      {/* Project Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                            <Folder className="w-5 h-5 text-blue-500" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="font-semibold text-primary truncate group-hover:text-blue-400 transition-colors">
                              {project.name}
                            </h3>
                            <p className="text-xs text-tertiary">
                              {formatDate(project.created_at)}
                            </p>
                          </div>
                        </div>
                        
                        <Badge 
                          variant={project.is_running ? 'success' : 'neutral'}
                          size="sm"
                        >
                          {project.is_running ? 'Running' : 'Stopped'}
                        </Badge>
                      </div>

                      {/* Project Description */}
                      {project.description && (
                        <p className="text-sm text-secondary line-clamp-2 leading-relaxed">
                          {project.description}
                        </p>
                      )}

                      {/* Project Stats */}
                      <div className="flex items-center gap-4 text-xs text-tertiary">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>Modified {formatDate(project.updated_at)}</span>
                        </div>
                        {project.container_port && (
                          <div className="flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" />
                            <span>Port {project.container_port}</span>
                          </div>
                        )}
                      </div>

                      {/* Project Actions */}
                      <div className="flex items-center gap-2 pt-2 border-t border-secondary">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/project/${project.id}`);
                          }}
                          className="flex-1"
                        >
                          Open
                        </Button>
                        
                        {project.is_running && project.container_port && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(`http://localhost:${project.container_port}`, '_blank');
                            }}
                            icon={<ExternalLink className="w-3 h-3" />}
                          />
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && projects.length === 0 && (
            <Card className="text-center max-w-md mx-auto">
              <div className="space-y-4">
                <div className="w-16 h-16 mx-auto bg-blue-500/10 rounded-full flex items-center justify-center">
                  <Folder className="w-8 h-8 text-blue-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-primary mb-2">
                    No projects yet
                  </h3>
                  <p className="text-secondary text-sm leading-relaxed">
                    Create your first Django project using AI and start building amazing applications.
                  </p>
                </div>
                <Button
                  variant="primary"
                  onClick={() => setIsCreateModalOpen(true)}
                  icon={<Plus className="w-4 h-4" />}
                >
                  Create Your First Project
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>

      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onProjectCreated={handleProjectCreated}
      />
    </AppLayout>
  );
};

export default Dashboard;