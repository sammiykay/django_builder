import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/layout/ProtectedRoute';

// Auth Pages
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';

// Protected Pages
import Dashboard from '../pages/Dashboard';
import ProjectDetail from '../pages/ProjectDetail';
import UserProfile from '../pages/UserProfile';
import { BillingPage } from '../pages/BillingPage';

// Landing Page Component (we'll create this to integrate with the landing.html)
const LandingPage = React.lazy(() => import('../pages/LandingPage'));

// 404 Not Found Page
const NotFoundPage = React.lazy(() => import('../pages/NotFoundPage'));

// Route Constants for better maintainability
export const ROUTES = {
  // Public routes
  HOME: '/',
  LANDING: '/landing',
  LOGIN: '/login',
  REGISTER: '/register',
  
  // Protected routes
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  BILLING: '/billing',
  
  // Project routes
  PROJECT_DETAIL: '/project/:id',
  PROJECT_FILES: '/project/:id/files',
  PROJECT_EDITOR: '/project/:id/editor',
  PROJECT_TERMINAL: '/project/:id/terminal',
  PROJECT_SETTINGS: '/project/:id/settings',
  
  // API routes for future expansion
  API: '/api',
  DOCS: '/docs',
  
  // Catch all
  NOT_FOUND: '*'
} as const;

// Helper function to generate project routes
export const getProjectRoute = (projectId: string, section?: 'files' | 'editor' | 'terminal' | 'settings') => {
  if (section) {
    return `/project/${projectId}/${section}`;
  }
  return `/project/${projectId}`;
};

// Main App Routes Component
export const AppRoutes: React.FC = () => {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route 
        path={ROUTES.HOME} 
        element={
          user ? <Navigate to={ROUTES.DASHBOARD} replace /> : <Navigate to={ROUTES.LANDING} replace />
        } 
      />
      
      <Route 
        path={ROUTES.LANDING} 
        element={
          user ? <Navigate to={ROUTES.DASHBOARD} replace /> : 
          <React.Suspense fallback={<div>Loading...</div>}>
            <LandingPage />
          </React.Suspense>
        } 
      />
      
      {/* Auth Routes */}
      <Route 
        path={ROUTES.LOGIN} 
        element={user ? <Navigate to={ROUTES.DASHBOARD} replace /> : <LoginForm />} 
      />
      
      <Route 
        path={ROUTES.REGISTER} 
        element={user ? <Navigate to={ROUTES.DASHBOARD} replace /> : <RegisterForm />} 
      />

      {/* Protected Routes */}
      <Route 
        path={ROUTES.DASHBOARD} 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.PROFILE} 
        element={
          <ProtectedRoute>
            <UserProfile />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.BILLING} 
        element={
          <ProtectedRoute>
            <BillingPage />
          </ProtectedRoute>
        } 
      />

      {/* Project Routes */}
      <Route 
        path={ROUTES.PROJECT_DETAIL} 
        element={
          <ProtectedRoute>
            <ProjectDetail />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.PROJECT_FILES} 
        element={
          <ProtectedRoute>
            <ProjectDetail />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.PROJECT_EDITOR} 
        element={
          <ProtectedRoute>
            <ProjectDetail />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.PROJECT_TERMINAL} 
        element={
          <ProtectedRoute>
            <ProjectDetail />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path={ROUTES.PROJECT_SETTINGS} 
        element={
          <ProtectedRoute>
            <ProjectDetail />
          </ProtectedRoute>
        } 
      />

      {/* 404 Not Found Route */}
      <Route 
        path={ROUTES.NOT_FOUND} 
        element={
          <React.Suspense fallback={<div>Loading...</div>}>
            <NotFoundPage />
          </React.Suspense>
        } 
      />
    </Routes>
  );
};

// Route Guard Hook for checking permissions
export const useRouteGuard = () => {
  const { user } = useAuth();
  
  const canAccessRoute = (routePath: string) => {
    // Define protected routes
    const protectedRoutes = [
      ROUTES.DASHBOARD,
      ROUTES.PROFILE,
      ROUTES.BILLING,
      ROUTES.PROJECT_DETAIL,
      ROUTES.PROJECT_FILES,
      ROUTES.PROJECT_EDITOR,
      ROUTES.PROJECT_TERMINAL,
      ROUTES.PROJECT_SETTINGS,
    ];
    
    return !protectedRoutes.some(route => 
      routePath.match(new RegExp(route.replace(/:\w+/g, '\\w+')))
    ) || !!user;
  };
  
  const redirectToLogin = () => {
    window.location.href = ROUTES.LOGIN;
  };
  
  return { canAccessRoute, redirectToLogin, isAuthenticated: !!user };
};

export default AppRoutes;