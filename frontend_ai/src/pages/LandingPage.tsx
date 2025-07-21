import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Play, Sparkles, Code, Zap, Shield, Box, Plus } from 'lucide-react';

const LandingPage: React.FC = () => {
  useEffect(() => {
    // Load external landing page scripts and styles if needed
    document.title = 'Django AI Builder - Create Django Projects with AI';
  }, []);

  const features = [
    {
      icon: <Sparkles className="w-12 h-12" />,
      title: "AI-Powered Generation",
      description: "Leverage advanced AI to generate complete Django projects with models, views, and templates automatically."
    },
    {
      icon: <Box className="w-12 h-12" />,
      title: "Container Ready",
      description: "Every project comes with Docker configuration for instant deployment and scalability across environments."
    },
    {
      icon: <Zap className="w-12 h-12" />,
      title: "Instant Deployment",
      description: "Deploy your projects immediately with our integrated container management and hosting solutions."
    },
    {
      icon: <Shield className="w-12 h-12" />,
      title: "Secure by Default",
      description: "Built-in security best practices, authentication systems, and protected deployment environments."
    },
    {
      icon: <Code className="w-12 h-12" />,
      title: "Full CRUD Operations",
      description: "Complete Create, Read, Update, Delete functionality with beautiful admin interfaces and user forms."
    },
    {
      icon: <Plus className="w-12 h-12" />,
      title: "Extensible Architecture",
      description: "Modular design allows easy customization and extension of your generated projects with additional features."
    }
  ];

  const steps = [
    {
      number: "01",
      title: "Describe Your Project",
      description: "Tell our AI what kind of Django application you want to build. Specify features, models, and functionality in plain English.",
      example: '"Create a blog app with user authentication, post creation, and comments"'
    },
    {
      number: "02", 
      title: "AI Generates Code",
      description: "Our intelligent system analyzes your requirements and generates a complete Django project with all necessary files and configurations."
    },
    {
      number: "03",
      title: "Deploy & Customize", 
      description: "Your project is containerized and ready to deploy. Make customizations, add features, and scale as needed."
    }
  ];

  const stats = [
    { number: "1,000+", label: "Projects Created" },
    { number: "50+", label: "Templates" },
    { number: "99.9%", label: "Uptime" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md z-50 border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Code className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Django AI Builder
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200 flex items-center space-x-2"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                  <span className="block">Build Django Projects</span>
                  <span className="block bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    with AI Power
                  </span>
                </h1>
                
                <p className="text-xl text-gray-600 leading-relaxed max-w-xl">
                  Transform your ideas into fully functional Django applications in minutes. 
                  Our AI-powered platform generates complete projects with CRUD operations, 
                  containerization, and modern UI components.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/register"
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 flex items-center justify-center space-x-2"
                >
                  <span>Start Building Now</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl font-semibold text-lg hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 flex items-center justify-center space-x-2">
                  <Play className="w-5 h-5" />
                  <span>Watch Demo</span>
                </button>
              </div>
              
              {/* Stats */}
              <div className="flex space-x-8 pt-4">
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      {stat.number}
                    </div>
                    <div className="text-sm text-gray-500 uppercase tracking-wide">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Code Preview */}
            <div className="relative">
              <div className="bg-gray-900 rounded-xl shadow-2xl overflow-hidden">
                <div className="bg-gray-800 px-4 py-3 flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-gray-400 text-sm ml-4">models.py</span>
                </div>
                <div className="p-6 font-mono text-sm leading-relaxed">
                  <div className="text-blue-400">class <span className="text-yellow-300">User</span><span className="text-gray-300">(</span><span className="text-yellow-300">models.Model</span><span className="text-gray-300">):</span></div>
                  <div className="text-gray-300 ml-4">name = <span className="text-yellow-300">models.CharField</span><span className="text-gray-300">(</span><span className="text-green-300">max_length=100</span><span className="text-gray-300">)</span></div>
                  <div className="text-gray-300 ml-4">email = <span className="text-yellow-300">models.EmailField</span><span className="text-gray-300">()</span></div>
                  <div className="text-gray-300 ml-4">created_at = <span className="text-yellow-300">models.DateTimeField</span><span className="text-gray-300">(</span><span className="text-green-300">auto_now_add=True</span><span className="text-gray-300">)</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-gray-900">Why Choose Django AI Builder?</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Powerful features designed to accelerate your Django development workflow
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="group p-8 bg-white border border-gray-200 rounded-xl hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="text-blue-500 mb-4 group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-gray-900">How It Works</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From idea to deployed application in three simple steps
            </p>
          </div>
          
          <div className="space-y-16">
            {steps.map((step, index) => (
              <div key={index} className={`grid lg:grid-cols-2 gap-12 items-center ${index % 2 === 1 ? 'lg:grid-flow-col-dense' : ''}`}>
                <div className={`space-y-6 ${index % 2 === 1 ? 'lg:col-start-2' : ''}`}>
                  <div className="text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {step.number}
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-2xl font-bold text-gray-900">{step.title}</h3>
                    <p className="text-lg text-gray-600 leading-relaxed">{step.description}</p>
                    {step.example && (
                      <div className="bg-white p-4 rounded-lg border-l-4 border-blue-500 italic text-gray-700">
                        {step.example}
                      </div>
                    )}
                  </div>
                </div>
                <div className={`bg-white p-8 rounded-xl shadow-lg ${index % 2 === 1 ? 'lg:col-start-1' : ''}`}>
                  <div className="h-32 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center">
                    <div className="text-4xl">
                      {index === 0 && '💬'}
                      {index === 1 && '⚡'}
                      {index === 2 && '🚀'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 space-y-8">
          <h2 className="text-4xl font-bold">Ready to Build Something Amazing?</h2>
          <p className="text-xl opacity-90">
            Join thousands of developers who are building faster with AI-powered Django generation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold text-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <span>Get Started Free</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="border-2 border-white/30 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-white/10 transition-all duration-200"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Code className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold text-xl">Django AI Builder</span>
              </div>
              <p className="text-gray-400 max-w-md">
                Empowering developers to build Django applications faster with AI-powered project generation.
              </p>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold text-lg">Quick Links</h4>
              <div className="grid grid-cols-2 gap-2 text-gray-400">
                <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
                <Link to="/register" className="hover:text-white transition-colors">Register</Link>
                <a href="#" className="hover:text-white transition-colors">Documentation</a>
                <a href="#" className="hover:text-white transition-colors">Support</a>
              </div>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-800 text-center text-gray-400">
            <p>&copy; 2025 Django AI Builder. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;