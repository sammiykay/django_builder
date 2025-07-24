import React, { useState, useEffect, useRef } from 'react';
import { 
  Send,
  Sparkles,
  Loader2,
  Lightbulb,
  Zap,
  Code2,
  Rocket
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../components/layout/AppLayout';
import { apiService } from '../services/api';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [userInput, setUserInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Particle system setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create particles
    const colors = ['#3B82F6', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B'];
    particlesRef.current = Array.from({ length: 50 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
      color: colors[Math.floor(Math.random() * colors.length)]
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((particle, index) => {
        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Wrap around edges
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        // Draw particle
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.opacity;
        ctx.fill();

        // Draw connections
        particlesRef.current.slice(index + 1).forEach(otherParticle => {
          const dx = particle.x - otherParticle.x;
          const dy = particle.y - otherParticle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 100) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(otherParticle.x, otherParticle.y);
            ctx.strokeStyle = particle.color;
            ctx.globalAlpha = 0.05 * (1 - distance / 100);
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        });
      });

      ctx.globalAlpha = 1;
      requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  // Mouse tracking
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || isGenerating) return;

    setIsGenerating(true);
    try {
      // Create project with AI generation
      const projectData = {
        name: userInput.split(' ').slice(0, 3).join(' '), // Use first few words as name
        description: userInput,
        python_version: '3.11',
        django_version: '5.0',
        project_type: 'web_app',
        complexity_level: 'simple',
        target_audience: '',
        key_features: [],
        technical_requirements: {}
      };

      const project = await apiService.createProject(projectData);
      
      // Navigate to the project page
      navigate(`/project/${project.id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const examplePrompts = [
    "Build a todo list app with user authentication",
    "Create a blog platform with comments and tags", 
    "Develop an e-commerce store with payment integration",
    "Make a social media dashboard with real-time updates",
    "Build a project management tool with team collaboration",
    "Create a recipe sharing app with ratings and reviews"
  ];

  return (
    <AppLayout>
      <div className="min-h-screen bg-black relative overflow-hidden">
        {/* Animated Background */}
        <canvas
          ref={canvasRef}
          className="fixed inset-0 pointer-events-none z-0"
          style={{ filter: 'blur(0.5px)' }}
        />

        {/* Gradient Orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div 
            className="absolute w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"
            style={{
              left: mousePosition.x - 192,
              top: mousePosition.y - 192,
              transition: 'all 0.3s ease-out'
            }}
          />
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000" />
          <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000" />
        </div>

        {/* Main Content */}
        <div className="relative z-10 min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            
            {/* Header */}
            <div className="space-y-6 mt-8">
              <div className="flex items-center justify-center space-x-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl backdrop-blur-sm border border-blue-500/30">
                  <Code2 className="w-8 h-8 text-blue-400" />
                </div>
                <div className="p-3 bg-gradient-to-br from-purple-500/20 to-cyan-500/20 rounded-2xl backdrop-blur-sm border border-purple-500/30">
                  <Sparkles className="w-8 h-8 text-purple-400" />
                </div>
                <div className="p-3 bg-gradient-to-br from-cyan-500/20 to-green-500/20 rounded-2xl backdrop-blur-sm border border-cyan-500/30">
                  <Rocket className="w-8 h-8 text-cyan-400" />
                </div>
              </div>
              
              <h1 className="text-6xl md:text-7xl font-black text-white leading-tight">
                What do you want to
                <span className="block bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
                  build today?
                </span>
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
                Describe your idea and watch AI transform it into a fully functional Django application
              </p>
            </div>

            {/* Main Input Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="relative group max-w-3xl mx-auto">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
                
                <div className="relative bg-gray-900/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 group-focus-within:border-blue-500/50 transition-all duration-300">
                  <textarea
                    ref={inputRef}
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="e.g., Build a social media app where users can share photos, follow friends, and comment on posts..."
                    rows={4}
                    className="w-full bg-transparent text-white text-lg placeholder-gray-400 resize-none focus:outline-none"
                    disabled={isGenerating}
                  />
                  
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-700/50">
                    <div className="flex items-center space-x-2 text-sm text-gray-400">
                      <Lightbulb className="w-4 h-4" />
                      <span>Be specific about features you want</span>
                    </div>
                    
                    <button
                      type="submit"
                      disabled={!userInput.trim() || isGenerating}
                      className="group/btn relative bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center space-x-3 disabled:cursor-not-allowed transform hover:scale-105 disabled:hover:scale-100"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span>Creating...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="w-5 h-5 group-hover/btn:rotate-12 transition-transform duration-300" />
                          <span>Build with AI</span>
                          <Send className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </form>

            {/* Example Prompts */}
            <div className="space-y-4">
              <p className="text-gray-400 text-sm font-medium">Try these examples:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-w-5xl mx-auto">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => setUserInput(prompt)}
                    className="group text-left p-4 bg-gray-900/30 backdrop-blur-sm border border-gray-700/30 rounded-xl hover:border-gray-600/50 hover:bg-gray-900/50 transition-all duration-300 hover:-translate-y-1"
                    disabled={isGenerating}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="p-1.5 bg-blue-500/10 rounded-lg mt-1">
                        <Lightbulb className="w-3 h-3 text-blue-400" />
                      </div>
                      <p className="text-sm text-gray-300 group-hover:text-white transition-colors duration-300 leading-relaxed">
                        {prompt}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Stats Bar */}
            <div className="flex items-center justify-center space-x-8 pt-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">50+</div>
                <div className="text-sm text-gray-400">Project Types</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">AI-Powered</div>
                <div className="text-sm text-gray-400">Code Generation</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">1-Click</div>
                <div className="text-sm text-gray-400">Deployment</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Dashboard;