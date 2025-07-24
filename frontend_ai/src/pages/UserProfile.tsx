import React, { useState, useEffect, useRef } from 'react';
import { User, Mail, MapPin, Globe, Github, Twitter, Linkedin, Calendar, Save, Loader2, Camera, X, Sparkles, Code2, Settings, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { UserProfile as UserProfileType } from '../types/api';
import AppLayout from '../components/layout/AppLayout';
import AvatarUpload from '../components/profile/AvatarUpload';
import Toast from '../components/ui/Toast';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

const UserProfile: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastType, setToastType] = useState<'success' | 'error'>('success');
  const [toastMessage, setToastMessage] = useState('');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  
  // Form state - Initialize with auth context data if available
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    bio: '',
    location: '',
    website: '',
    github_username: '',
    twitter_username: '',
    linkedin_username: ''
  });

  useEffect(() => {
    loadProfile();
  }, []);

  // Update form data if user context changes and no profile data exists
  useEffect(() => {
    if (user && !profile && !isLoading) {
      setFormData(prev => ({
        ...prev,
        first_name: user.first_name || prev.first_name,
        last_name: user.last_name || prev.last_name,
        email: user.email || prev.email
      }));
    }
  }, [user, profile, isLoading]);

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

    // Create particles with profile theme colors
    const colors = ['#3B82F6', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444'];
    particlesRef.current = Array.from({ length: 40 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      size: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.3 + 0.1,
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

          if (distance < 80) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(otherParticle.x, otherParticle.y);
            ctx.strokeStyle = particle.color;
            ctx.globalAlpha = 0.03 * (1 - distance / 80);
            ctx.lineWidth = 0.3;
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

  // Mouse tracking for interactive effects
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const profileData = await apiService.getUserProfile();
      setProfile(profileData);
      
      // Populate form with existing data, falling back to auth context data
      setFormData({
        first_name: profileData.user?.first_name || user?.first_name || '',
        last_name: profileData.user?.last_name || user?.last_name || '',
        email: profileData.user?.email || user?.email || '',
        bio: profileData.bio || '',
        location: profileData.location || '',
        website: profileData.website || '',
        github_username: profileData.github_username || '',
        twitter_username: profileData.twitter_username || '',
        linkedin_username: profileData.linkedin_username || ''
      });
    } catch (err: any) {
      console.error('Profile loading error:', err);
      setError(err.response?.data?.error || 'Failed to load profile');
      
      // If profile doesn't exist, just use auth context data
      if (err.response?.status === 404) {
        setFormData(prev => ({
          ...prev,
          first_name: user?.first_name || prev.first_name,
          last_name: user?.last_name || prev.last_name,
          email: user?.email || prev.email
        }));
        setError(null); // Clear error for new profiles
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Validation helper
  const isFormValid = () => {
    return formData.first_name.trim() && formData.last_name.trim() && formData.email.trim();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSaving) return;

    setSaving(true);
    setError(null);

    try {
      const updatedProfile = await apiService.updateUserProfile(formData);
      setProfile(updatedProfile);
      
      // Update auth context if user data changed
      if (user) {
        updateUser({
          ...user,
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email
        });
      }

      const isNewProfile = !profile;
      setToastType('success');
      setToastMessage(isNewProfile ? 'Profile created successfully!' : 'Profile updated successfully!');
      setShowToast(true);
      
      // Notify navbar to refresh profile data
      window.dispatchEvent(new CustomEvent('profileUpdated'));
    } catch (err: any) {
      console.error('Profile save error:', err);
      const errorMessage = err.response?.data?.error || 'Failed to save profile';
      setError(errorMessage);
      setToastType('error');
      setToastMessage(errorMessage);
      setShowToast(true);
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpdate = (avatarUrl: string) => {
    if (profile) {
      setProfile({ ...profile, avatar: avatarUrl });
      // Notify navbar to refresh profile data
      window.dispatchEvent(new CustomEvent('profileUpdated'));
    }
  };

  const getAvatarUrl = (avatar: string | undefined) => {
    if (!avatar) return null;
    
    // If avatar is already a full URL, return as is
    if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
      return avatar;
    }
    
    // If avatar starts with /, it's a relative URL from backend
    if (avatar.startsWith('/')) {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      return `${API_BASE_URL}${avatar}`;
    }
    
    // Otherwise assume it needs /media/ prefix
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${API_BASE_URL}/media/${avatar}`;
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center">
          {/* Animated Background */}
          <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ filter: 'blur(0.5px)' }}
          />
          
          {/* Loading Content */}
          <div className="relative z-10 text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="p-4 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl backdrop-blur-sm border border-blue-500/30">
                <User className="w-12 h-12 text-blue-400" />
              </div>
            </div>
            <div className="flex items-center justify-center space-x-3 mb-4">
              <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
              <span className="text-white text-lg font-medium">Loading your profile...</span>
            </div>
            <div className="w-64 bg-gray-800 rounded-full h-2 mx-auto">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (error && !profile) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center">
          {/* Animated Background */}
          <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ filter: 'blur(0.5px)' }}
          />
          
          {/* Error Content */}
          <div className="relative z-10 text-center max-w-md mx-auto px-6">
            <div className="flex items-center justify-center mb-6">
              <div className="p-4 bg-gradient-to-br from-red-500/20 to-orange-500/20 rounded-2xl backdrop-blur-sm border border-red-500/30">
                <X className="w-12 h-12 text-red-400" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Failed to Load Profile</h2>
            <p className="text-gray-400 mb-8 leading-relaxed">{error}</p>
            <button
              onClick={loadProfile}
              className="group relative px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <span className="relative">Try Again</span>
            </button>
          </div>
        </div>
      </AppLayout>
    );
  }

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
        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header Section */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl backdrop-blur-sm border border-blue-500/30">
                <User className="w-8 h-8 text-blue-400" />
              </div>
              <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl backdrop-blur-sm border border-purple-500/30">
                <Settings className="w-8 h-8 text-purple-400" />
              </div>
              <div className="p-3 bg-gradient-to-br from-cyan-500/20 to-green-500/20 rounded-2xl backdrop-blur-sm border border-cyan-500/30">
                <Shield className="w-8 h-8 text-cyan-400" />
              </div>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
              User Profile
            </h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Manage your account settings, personal information, and connect your social profiles
            </p>
          </div>

          {/* Profile Card */}
          <div className="bg-gray-900/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden">
            {/* Profile Header */}
            <div className="bg-gradient-to-r from-blue-600/80 via-purple-600/80 to-cyan-600/80 backdrop-blur-sm px-8 py-10">
              <div className="flex flex-col md:flex-row items-center md:items-start space-y-6 md:space-y-0 md:space-x-8">
                <div className="relative group">
                  <div className="w-32 h-32 rounded-full bg-gray-700/50 backdrop-blur-sm flex items-center justify-center overflow-hidden border-4 border-white/20 shadow-2xl">
                    {getAvatarUrl(profile?.avatar) ? (
                      <>
                        <img 
                          src={getAvatarUrl(profile?.avatar)!} 
                          alt="Profile" 
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            console.error('Avatar failed to load:', getAvatarUrl(profile?.avatar));
                            e.currentTarget.style.display = 'none';
                            const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                            if (fallback) fallback.style.display = 'flex';
                          }}
                        />
                        <User className="w-16 h-16 text-gray-400" style={{ display: 'none' }} />
                      </>
                    ) : (
                      <User className="w-16 h-16 text-gray-400" />
                    )}
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <AvatarUpload 
                    currentAvatar={getAvatarUrl(profile?.avatar) || undefined}
                    onAvatarUpdate={handleAvatarUpdate}
                  />
                </div>
                <div className="text-center md:text-left flex-1">
                  <h2 className="text-3xl font-bold text-white mb-2">
                    {formData.first_name || formData.last_name ? 
                      `${formData.first_name} ${formData.last_name}`.trim() : 
                      user?.username || 'Your Name'
                    }
                    <Sparkles className="inline w-6 h-6 ml-2 text-yellow-400" />
                  </h2>
                  <p className="text-blue-100 text-lg mb-4">@{user?.username}</p>
                  {profile && (
                    <div className="text-xs text-blue-200 bg-blue-500/20 backdrop-blur-sm rounded-full px-3 py-1 inline-block">
                      ✓ Profile loaded from your saved data
                    </div>
                  )}
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-blue-100 text-sm">
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-3 py-1">
                      <Mail className="w-4 h-4" />
                      <span>{formData.email}</span>
                    </div>
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-3 py-1">
                      <Calendar className="w-4 h-4" />
                      <span>Joined {new Date(user?.date_joined || '').toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Profile Status Indicator */}
            {!isLoading && (
              <div className="px-8 pt-6">
                {profile ? (
                  <div className="flex items-center space-x-2 text-sm text-green-400 bg-green-500/10 backdrop-blur-sm rounded-lg px-4 py-2 border border-green-500/20">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span>Profile data loaded and ready for editing</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 text-sm text-blue-400 bg-blue-500/10 backdrop-blur-sm rounded-lg px-4 py-2 border border-blue-500/20">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                    <span>Creating new profile with your account information</span>
                  </div>
                )}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-8 space-y-8">
              {/* Basic Information Section */}
              <div className="space-y-6">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg backdrop-blur-sm border border-blue-500/30">
                    <User className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Personal Information</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      First Name
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                      placeholder={isLoading ? "Loading..." : "Enter your first name"}
                    />
                  </div>
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                      placeholder={isLoading ? "Loading..." : "Enter your last name"}
                    />
                  </div>
                </div>

                <div className="group">
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    <Mail className="w-4 h-4 inline mr-2" />
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    placeholder={isLoading ? "Loading..." : "your.email@example.com"}
                  />
                </div>

                <div className="group">
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Bio
                  </label>
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleInputChange}
                    rows={4}
                    placeholder="Tell us about yourself... What do you love to build?"
                    className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 resize-none group-hover:border-blue-500/30"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      <MapPin className="w-4 h-4 inline mr-2" />
                      Location
                    </label>
                    <input
                      type="text"
                      name="location"
                      value={formData.location}
                      onChange={handleInputChange}
                      placeholder="San Francisco, CA"
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    />
                  </div>
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      <Globe className="w-4 h-4 inline mr-2" />
                      Website
                    </label>
                    <input
                      type="url"
                      name="website"
                      value={formData.website}
                      onChange={handleInputChange}
                      placeholder="https://yourawesome.site"
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    />
                  </div>
                </div>
              </div>

              {/* Social Links Section */}
              <div className="space-y-6 pt-8 border-t border-gray-700/50">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg backdrop-blur-sm border border-purple-500/30">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Social Connections</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      <Github className="w-4 h-4 inline mr-2" />
                      GitHub
                    </label>
                    <input
                      type="text"
                      name="github_username"
                      value={formData.github_username}
                      onChange={handleInputChange}
                      placeholder="username"
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    />
                  </div>
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      <Twitter className="w-4 h-4 inline mr-2" />
                      Twitter
                    </label>
                    <input
                      type="text"
                      name="twitter_username"
                      value={formData.twitter_username}
                      onChange={handleInputChange}
                      placeholder="username"
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    />
                  </div>
                  <div className="group">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      <Linkedin className="w-4 h-4 inline mr-2" />
                      LinkedIn
                    </label>
                    <input
                      type="text"
                      name="linkedin_username"
                      value={formData.linkedin_username}
                      onChange={handleInputChange}
                      placeholder="username"
                      className="w-full bg-gray-800/40 backdrop-blur-sm border border-gray-600/50 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 group-hover:border-blue-500/30"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end pt-8 border-t border-gray-700/50">
                <button
                  type="submit"
                  disabled={isSaving || !isFormValid()}
                  className="group relative flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25 disabled:hover:scale-100 disabled:hover:shadow-none"
                  title={!isFormValid() ? 'Please fill in your first name, last name, and email' : ''}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative flex items-center space-x-3">
                    {isSaving ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Saving Changes...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-5 h-5" />
                        <span>Save Changes</span>
                      </>
                    )}
                  </div>
                </button>
              </div>
            </form>
          </div>

          {/* Toast Notification */}
          {showToast && (
            <Toast
              message={toastMessage}
              type={toastType}
              duration={3000}
              onClose={() => setShowToast(false)}
            />
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default UserProfile;