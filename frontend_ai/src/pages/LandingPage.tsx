import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowRight, Play, Sparkles, Code, Zap, Shield, Box, Plus, Mail, Github, Twitter, Facebook,
  Terminal, FileText, Database, Server, Lock, Rocket, CheckCircle, Star, Users, Trophy,
  ChevronDown, Menu, X, MousePointer, Layers, Globe
} from 'lucide-react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
}

const LandingPage: React.FC = () => {
  const [typingText, setTypingText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  
  // Code files for enhanced terminal
  const codeFiles = [
    {
      name: 'models.py',
      content: [
        'from django.db import models',
        'from django.contrib.auth.models import User',
        '',
        'class BlogPost(models.Model):',
        '    title = models.CharField(max_length=200)',
        '    content = models.TextField()',
        '    author = models.ForeignKey(User, on_delete=models.CASCADE)',
        '    created_at = models.DateTimeField(auto_now_add=True)',
        '    updated_at = models.DateTimeField(auto_now=True)',
        '    published = models.BooleanField(default=False)',
        '',
        '    def __str__(self):',
        '        return self.title'
      ]
    },
    {
      name: 'views.py',
      content: [
        'from django.shortcuts import render, get_object_or_404',
        'from django.contrib.auth.decorators import login_required',
        'from .models import BlogPost',
        '',
        '@login_required',
        'def create_post(request):',
        '    if request.method == "POST":',
        '        post = BlogPost.objects.create(',
        '            title=request.POST["title"],',
        '            content=request.POST["content"],',
        '            author=request.user',
        '        )',
        '        return redirect("post_detail", pk=post.pk)'
      ]
    },
    {
      name: 'urls.py',
      content: [
        'from django.urls import path',
        'from . import views',
        '',
        'urlpatterns = [',
        '    path("", views.post_list, name="post_list"),',
        '    path("post/<int:pk>/", views.post_detail, name="post_detail"),',
        '    path("create/", views.create_post, name="create_post"),',
        '    path("edit/<int:pk>/", views.edit_post, name="edit_post"),',
        ']'
      ]
    }
  ];

  // Initialize particle system
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
    const particleCount = 100;
    particlesRef.current = Array.from({ length: particleCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.1
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
        ctx.fillStyle = `rgba(59, 130, 246, ${particle.opacity})`;
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
            ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - distance / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        });
      });

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

  // Scroll tracking
  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Typing animation
  useEffect(() => {
    document.title = 'Django AI Builder - Create Django Projects with AI';
    
    const codeText = 'auto_now_add=True';
    let i = 0;
    const typingInterval = setInterval(() => {
      if (i < codeText.length) {
        setTypingText(codeText.slice(0, i + 1));
        i++;
      } else {
        clearInterval(typingInterval);
      }
    }, 100);

    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);

    return () => {
      clearInterval(typingInterval);
      clearInterval(cursorInterval);
    };
  }, []);

  const features = [
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: "AI-Powered Generation",
      description: "Advanced machine learning algorithms generate complete Django applications with intelligent code structure, optimized patterns, and best practices built-in.",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: <Terminal className="w-8 h-8" />,
      title: "Smart CLI Integration", 
      description: "Seamless command-line interface with intelligent auto-completion, real-time validation, and integrated development tools for maximum productivity.",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: "Database Optimization",
      description: "Automatically optimized database schemas, intelligent indexing, and performance-tuned queries that scale with your application growth.",
      gradient: "from-green-500 to-teal-500"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "Enterprise Security",
      description: "Military-grade security protocols, automatic vulnerability scanning, and compliance-ready configurations for enterprise deployments.",
      gradient: "from-red-500 to-orange-500"
    },
    {
      icon: <Rocket className="w-8 h-8" />,
      title: "Cloud-Native Deploy",
      description: "One-click deployment to AWS, GCP, Azure with auto-scaling, load balancing, and intelligent resource management included.",
      gradient: "from-indigo-500 to-purple-500"
    },
    {
      icon: <Layers className="w-8 h-8" />,
      title: "Microservices Ready",
      description: "Built-in support for microservices architecture, API gateways, service mesh integration, and distributed system patterns.",
      gradient: "from-yellow-500 to-red-500"
    }
  ];

  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Lead Developer at TechCorp",
      avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=64&h=64&fit=crop&crop=face",
      content: "Django AI Builder reduced our development time by 80%. What used to take weeks now takes hours.",
      rating: 5
    },
    {
      name: "Marcus Rodriguez", 
      role: "CTO at StartupX",
      avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=64&h=64&fit=crop&crop=face",
      content: "The generated code quality is exceptional. It's like having a senior Django developer on autopilot.",
      rating: 5
    },
    {
      name: "Emily Watson",
      role: "Full Stack Engineer",
      avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=64&h=64&fit=crop&crop=face", 
      content: "From prototype to production in days, not months. This tool is a game-changer for rapid development.",
      rating: 5
    }
  ];

  const pricingPlans = [
    {
      name: "Starter",
      price: "$29",
      period: "/month",
      description: "Perfect for individual developers and small projects",
      features: [
        "5 AI-generated projects/month",
        "Basic templates & components",
        "Community support",
        "Standard deployment",
        "Basic monitoring"
      ],
      highlighted: false
    },
    {
      name: "Professional", 
      price: "$99",
      period: "/month",
      description: "Ideal for teams and growing businesses",
      features: [
        "Unlimited AI projects",
        "Advanced templates & patterns",
        "Priority support",
        "Multi-cloud deployment",
        "Advanced monitoring & analytics",
        "Custom integrations",
        "Team collaboration tools"
      ],
      highlighted: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "",
      description: "For large organizations with specific needs",
      features: [
        "Everything in Professional",
        "Dedicated AI model training",
        "On-premise deployment",
        "24/7 phone support",
        "Custom compliance features",
        "Advanced security auditing",
        "Dedicated success manager"
      ],
      highlighted: false
    }
  ];

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Interactive Particle Canvas */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 pointer-events-none z-0"
        style={{ filter: 'blur(0.5px)' }}
      />

      {/* Cursor Follower */}
      <div 
        className="fixed w-4 h-4 bg-blue-400 rounded-full pointer-events-none z-50 mix-blend-difference transition-transform duration-100"
        style={{
          left: mousePosition.x - 8,
          top: mousePosition.y - 8,
          transform: `scale(${mousePosition.x && mousePosition.y ? 1 : 0})`
        }}
      />

      {/* Enhanced Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-black/20 backdrop-blur-2xl z-40 border-b border-gray-800/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center space-x-4">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div className="relative w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
                  <Code className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <span className="font-bold text-2xl bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Django AI Builder
                </span>
                <div className="text-xs text-gray-400 font-medium">Next-Gen Development</div>
              </div>
            </div>
            
            <div className="hidden lg:flex items-center space-x-8">
              <a href="#features" className="text-gray-300 hover:text-white transition-colors font-medium relative group">
                Features
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-500 transition-all group-hover:w-full"></span>
              </a>
              <a href="#how-it-works" className="text-gray-300 hover:text-white transition-colors font-medium relative group">
                How it Works
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-500 transition-all group-hover:w-full"></span>
              </a>
              <a href="#testimonials" className="text-gray-300 hover:text-white transition-colors font-medium relative group">
                Testimonials
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-500 transition-all group-hover:w-full"></span>
              </a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition-colors font-medium relative group">
                Pricing
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-500 transition-all group-hover:w-full"></span>
              </a>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-300 hover:text-white font-medium transition-colors hidden sm:block"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transform hover:-translate-y-0.5 transition-all duration-200 flex items-center space-x-2"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="lg:hidden text-gray-300 hover:text-white p-2"
              >
                {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="lg:hidden bg-black/95 backdrop-blur-xl border-t border-gray-800/30">
            <div className="px-4 py-6 space-y-4">
              <a href="#features" className="block text-gray-300 hover:text-white py-2">Features</a>
              <a href="#how-it-works" className="block text-gray-300 hover:text-white py-2">How it Works</a>
              <a href="#testimonials" className="block text-gray-300 hover:text-white py-2">Testimonials</a>
              <a href="#pricing" className="block text-gray-300 hover:text-white py-2">Pricing</a>
              <Link to="/login" className="block text-gray-300 hover:text-white py-2">Sign In</Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section with Parallax */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative z-10 min-h-screen flex items-center">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-10">
              <div className="space-y-8">
                <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-full px-6 py-3">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  <span className="text-sm font-medium text-blue-400">AI-Powered Development Platform</span>
                </div>
                
                <h1 className="text-7xl lg:text-8xl font-black leading-tight">
                  <span className="block text-white">Build</span>
                  <span className="block bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent animate-gradient">
                    Django Apps
                  </span>
                  <span className="block text-white">in Minutes</span>
                </h1>
                
                <p className="text-xl text-gray-300 leading-relaxed max-w-2xl">
                  Revolutionary AI platform that transforms your ideas into production-ready Django applications. 
                  Generate complete backends, APIs, and admin interfaces with enterprise-grade code quality.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-6">
                <Link
                  to="/register"
                  className="group relative overflow-hidden bg-gradient-to-r from-blue-500 to-purple-600 text-white px-10 py-5 rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-blue-500/25 transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center space-x-3"
                >
                  <span className="relative z-10">Start Building Now</span>
                  <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform relative z-10" />
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </Link>
                
                <button className="group border-2 border-gray-600 text-gray-300 px-10 py-5 rounded-2xl font-bold text-lg hover:border-blue-500 hover:bg-blue-500/10 transition-all duration-300 flex items-center justify-center space-x-3">
                  <Play className="w-6 h-6 group-hover:scale-110 transition-transform" />
                  <span>Watch Demo</span>
                </button>
              </div>
              
              {/* Enhanced Stats */}
              <div className="grid grid-cols-3 gap-8 pt-8 border-t border-gray-800">
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                    50K+
                  </div>
                  <div className="text-sm text-gray-400 uppercase tracking-wide">Apps Generated</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                    99.9%
                  </div>
                  <div className="text-sm text-gray-400 uppercase tracking-wide">Uptime</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent mb-2">
                    24/7
                  </div>
                  <div className="text-sm text-gray-400 uppercase tracking-wide">Support</div>
                </div>
              </div>
            </div>
            
            {/* Advanced Code Terminal */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-3xl blur-3xl"></div>
              <div className="relative bg-gray-900/90 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border border-gray-700/50">
                {/* Terminal Header */}
                <div className="bg-gray-800/80 px-6 py-4 flex items-center justify-between border-b border-gray-700/50">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    </div>
                    <Terminal className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-400 text-sm font-mono">Django AI Terminal</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span>Connected</span>
                  </div>
                </div>

                {/* File Tabs */}
                <div className="bg-gray-800/50 px-6 py-2 flex space-x-1 border-b border-gray-700/30">
                  {codeFiles.map((file, index) => (
                    <button
                      key={index}
                      onClick={() => setActiveTab(index)}
                      className={`px-4 py-2 rounded-lg text-sm font-mono transition-all ${
                        activeTab === index
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30'
                      }`}
                    >
                      {file.name}
                    </button>
                  ))}
                </div>

                {/* Code Content */}
                <div className="p-6 font-mono text-sm leading-relaxed h-80 overflow-y-auto">
                  {codeFiles[activeTab].content.map((line, index) => (
                    <div key={index} className="flex">
                      <span className="text-gray-500 select-none w-8 text-right mr-4">{index + 1}</span>
                      <span className="text-gray-300">{line}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Features Section */}
      <section id="features" className="py-32 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-6 mb-20">
            <h2 className="text-6xl font-black text-white">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Built for modern development teams who demand speed, quality, and reliability
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="group relative p-8 bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-xl border border-gray-700/30 rounded-3xl hover:border-gray-600/50 transition-all duration-500 hover:-translate-y-2"
                style={{ 
                  transform: `translateY(${scrollY * -0.02 * (index + 1)}px)`,
                  animationDelay: `${index * 100}ms` 
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                <div className={`inline-flex p-4 bg-gradient-to-r ${feature.gradient} rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                
                <h3 className="text-2xl font-bold text-white mb-4 group-hover:text-blue-100 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-32 bg-gradient-to-br from-gray-900/50 to-black/50 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-6 mb-20">
            <h2 className="text-6xl font-black text-white">
              Trusted by Developers
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Join thousands of developers who are building faster and better with Django AI Builder
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div 
                key={index}
                className="bg-gradient-to-br from-gray-800/50 to-gray-900/30 backdrop-blur-xl border border-gray-700/30 rounded-2xl p-8 hover:border-gray-600/50 transition-all duration-300"
              >
                <div className="flex items-center space-x-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                
                <p className="text-gray-300 leading-relaxed mb-6 italic">
                  "{testimonial.content}"
                </p>
                
                <div className="flex items-center space-x-4">
                  <img 
                    src={testimonial.avatar} 
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full border-2 border-gray-600"
                  />
                  <div>
                    <div className="font-semibold text-white">{testimonial.name}</div>
                    <div className="text-sm text-gray-400">{testimonial.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-32 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-6 mb-20">
            <h2 className="text-6xl font-black text-white">
              Simple Pricing
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Choose the plan that fits your needs. All plans include core AI features.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <div 
                key={index}
                className={`relative bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-xl border rounded-3xl p-8 transition-all duration-300 hover:-translate-y-2 ${
                  plan.highlighted 
                    ? 'border-blue-500/50 shadow-2xl shadow-blue-500/10' 
                    : 'border-gray-700/30 hover:border-gray-600/50'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-full text-sm font-bold">
                      Most Popular
                    </div>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-5xl font-black text-white">{plan.price}</span>
                    <span className="text-gray-400">{plan.period}</span>
                  </div>
                  <p className="text-gray-400">{plan.description}</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  to="/register"
                  className={`w-full py-4 rounded-xl font-bold text-center transition-all duration-300 flex items-center justify-center space-x-2 ${
                    plan.highlighted
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/25'
                      : 'border-2 border-gray-600 text-gray-300 hover:border-blue-500 hover:text-blue-400'
                  }`}
                >
                  <span>Get Started</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 bg-gradient-to-r from-blue-600 to-purple-700 relative overflow-hidden z-10">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/90 to-purple-700/90"></div>
        <div className="relative max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 space-y-10">
          <h2 className="text-6xl font-black text-white">
            Ready to Transform Your Development?
          </h2>
          <p className="text-2xl text-blue-100 max-w-2xl mx-auto">
            Join over 50,000 developers building the future with AI-powered Django generation.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center pt-8">
            <Link
              to="/register"
              className="bg-white text-blue-600 hover:bg-gray-100 px-10 py-5 rounded-2xl font-bold text-xl hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center space-x-3"
            >
              <span>Start Building Free</span>
              <ArrowRight className="w-6 h-6" />
            </Link>
            <Link
              to="/login"
              className="border-2 border-white/30 text-white px-10 py-5 rounded-2xl font-bold text-xl hover:bg-white/10 hover:border-white/50 transition-all duration-300"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Enhanced Footer */}
      <footer className="bg-black text-white py-20 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="md:col-span-2 space-y-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
                  <Code className="w-6 h-6 text-white" />
                </div>
                <div>
                  <span className="font-bold text-2xl bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Django AI Builder
                  </span>
                  <div className="text-sm text-gray-400">Next-Gen Development</div>
                </div>
              </div>
              <p className="text-gray-400 max-w-md leading-relaxed">
                Empowering developers worldwide to build Django applications faster with cutting-edge AI technology. 
                Transform your development workflow today.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="w-12 h-12 bg-gray-800 hover:bg-blue-500 rounded-xl flex items-center justify-center transition-colors">
                  <Github className="w-5 h-5" />
                </a>
                <a href="#" className="w-12 h-12 bg-gray-800 hover:bg-blue-500 rounded-xl flex items-center justify-center transition-colors">
                  <Twitter className="w-5 h-5" />
                </a>
                <a href="#" className="w-12 h-12 bg-gray-800 hover:bg-blue-500 rounded-xl flex items-center justify-center transition-colors">
                  <Facebook className="w-5 h-5" />
                </a>
              </div>
            </div>
            
            <div className="space-y-6">
              <h4 className="font-bold text-xl text-white">Product</h4>
              <div className="space-y-3 text-gray-400">
                <a href="#" className="block hover:text-white transition-colors">Features</a>
                <a href="#" className="block hover:text-white transition-colors">Templates</a>
                <a href="#" className="block hover:text-white transition-colors">Integrations</a>
                <a href="#" className="block hover:text-white transition-colors">API</a>
              </div>
            </div>
            
            <div className="space-y-6">
              <h4 className="font-bold text-xl text-white">Support</h4>
              <div className="space-y-3 text-gray-400">
                <a href="#" className="block hover:text-white transition-colors">Documentation</a>
                <a href="#" className="block hover:text-white transition-colors">Help Center</a>
                <a href="#" className="block hover:text-white transition-colors">Community</a>
                <a href="#" className="block hover:text-white transition-colors">Contact</a>
              </div>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-800">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <div className="flex space-x-6 text-gray-400">
                <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-white transition-colors">Cookie Policy</a>
              </div>
              <p className="text-gray-400">
                &copy; 2025 Django AI Builder. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;