import React, { useState } from 'react';
import { Wand2, Loader2, Sparkles, ArrowRight, Code2, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/api';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import '../../styles/design-system.css';

interface QuickCreateWidgetProps {
  onProjectCreated: () => void;
}

const QuickCreateWidget: React.FC<QuickCreateWidgetProps> = ({ onProjectCreated }) => {
  const navigate = useNavigate();
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastType, setToastType] = useState<'error' | 'success'>('error');
  const [currentStep, setCurrentStep] = useState<'input' | 'creating' | 'generating'>('input');
  const [createdProject, setCreatedProject] = useState<any>(null);

  const examplePrompts = [
    "Build a blog platform where users can write, publish, and comment on articles",
    "Create an e-commerce store with product catalog, shopping cart, and order management",
    "Develop a task management app with team collaboration and project tracking",
    "Build a social media platform with posts, likes, follows, and real-time chat",
    "Create a learning management system with courses, quizzes, and student progress tracking"
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || isCreating) return;

    setIsCreating(true);
    setError(null);
    setShowToast(false);
    setCurrentStep('creating');

    try {
      // Use the new quick create and generate API
      const result = await apiService.quickCreateAndGenerate(description);
      
      if (result.success) {
        setCreatedProject(result.project);
        
        // Navigate to project chat page to watch live generation and interact with AI
        setTimeout(() => {
          navigate(`/project/${result.project.id}?tab=chat&autostart=true`);
        }, 1000);
        
        // Reset form and notify parent
        setDescription('');
        setCurrentStep('input');
        setIsCreating(false);
        onProjectCreated();
        
      } else {
        // Partial success - project created but generation failed
        setCreatedProject(result.project);
        setError(result.error || 'Project created but AI generation failed');
        setToastType('error');
        setShowToast(true);
        setCurrentStep('input');
        setIsCreating(false);
        onProjectCreated(); // Still notify parent as project was created
      }

    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create and generate project');
      setToastType('error');
      setShowToast(true);
      setCurrentStep('input');
      setIsCreating(false);
    }
  };


  const handleExampleClick = (example: string) => {
    setDescription(example);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-primary">
            Build with AI
          </h1>
        </div>
        <p className="text-xl text-secondary max-w-2xl mx-auto leading-relaxed">
          Describe your Django app idea and watch as AI creates a complete, production-ready project for you
        </p>
        
        <div className="flex items-center justify-center gap-6 pt-4">
          <Badge variant="primary" size="lg">
            <Zap className="w-4 h-4 mr-2" />
            AI-Powered
          </Badge>
          <Badge variant="success" size="lg">
            <Code2 className="w-4 h-4 mr-2" />
            Production Ready
          </Badge>
        </div>
      </div>

      {currentStep === 'input' && (
        <Card className="max-w-4xl mx-auto" elevated>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-primary">
                Describe your Django application
              </label>
              <div className="relative">
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What would you like to build? Be as specific as possible about features, functionality, and user interactions..."
                  rows={5}
                  className="input resize-none"
                  disabled={isCreating}
                />
                <div className="absolute bottom-3 right-3 text-xs text-tertiary">
                  {description.length}/500
                </div>
              </div>
              <p className="text-sm text-tertiary">
                💡 Tip: Include details about user roles, key features, and any specific requirements for better results
              </p>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm text-secondary">
                {description.length < 20 ? (
                  <span className="text-yellow-500">
                    {20 - description.length} more characters needed
                  </span>
                ) : (
                  <span className="text-green-500 flex items-center gap-1">
                    <Sparkles className="w-4 h-4" />
                    Ready to build!
                  </span>
                )}
              </div>
              
              <Button
                type="submit"
                disabled={!description.trim() || isCreating || description.length < 20}
                loading={isCreating}
                variant="primary"
                size="lg"
                icon={!isCreating ? <Wand2 className="w-5 h-5" /> : undefined}
              >
                {isCreating ? 'Creating Project...' : 'Create Project'}
              </Button>
            </div>
          </form>

          {/* Examples */}
          <div className="mt-8 pt-6 border-t border-secondary">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <h3 className="text-sm font-semibold text-primary">Popular Ideas</h3>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {examplePrompts.slice(0, 6).map((example, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleExampleClick(example)}
                  className="text-left p-4 bg-tertiary/30 hover:bg-tertiary/50 rounded-xl border border-secondary hover:border-blue-500/50 transition-all duration-200 group"
                >
                  <p className="text-secondary group-hover:text-primary text-sm leading-relaxed">
                    {example}
                  </p>
                  <ArrowRight className="w-4 h-4 text-tertiary group-hover:text-blue-500 mt-2 transition-colors" />
                </button>
              ))}
            </div>
          </div>
        </Card>
      )}

      {(currentStep === 'creating' || currentStep === 'generating') && (
        <Card className="max-w-2xl mx-auto text-center" elevated>
          <div className="space-y-6">
            <div className="w-16 h-16 mx-auto bg-blue-500/10 rounded-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
            
            <div className="space-y-3">
              <h3 className="text-2xl font-semibold text-primary">
                {currentStep === 'creating' 
                  ? '🚀 Creating your project...' 
                  : '🤖 Generating your Django app...'}
              </h3>
              <p className="text-secondary leading-relaxed">
                {currentStep === 'creating'
                  ? 'Analyzing your description and setting up the project structure'
                  : 'Building your complete Django application with AI magic. This may take a moment.'}
              </p>
            </div>

            {createdProject && (
              <Card className="bg-green-50/5 border-green-500/20" padding="sm">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-500/10 rounded-full flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-green-500" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-green-400">
                      Project Created Successfully!
                    </p>
                    <p className="text-xs text-green-300">
                      "{createdProject.name}" is ready for AI generation
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </Card>
      )}

      {/* Error Display */}
      {error && showToast && (
        <Card className="max-w-2xl mx-auto bg-red-50/5 border-red-500/20">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-red-500/10 rounded-full flex items-center justify-center flex-shrink-0">
              <ArrowRight className="w-4 h-4 text-red-500 rotate-45" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-red-400 mb-1">
                Something went wrong
              </h4>
              <p className="text-sm text-red-300">{error}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowToast(false);
                setError(null);
              }}
            >
              ✕
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default QuickCreateWidget;