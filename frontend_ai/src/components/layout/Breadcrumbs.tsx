import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { ROUTES } from '../../routes';

interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}

const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const params = useParams();

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Always start with Home/Dashboard
    if (location.pathname !== ROUTES.DASHBOARD) {
      breadcrumbs.push({
        label: 'Dashboard',
        href: ROUTES.DASHBOARD
      });
    }

    // Generate breadcrumbs based on current path
    switch (true) {
      case location.pathname === ROUTES.DASHBOARD:
        breadcrumbs.push({
          label: 'Dashboard',
          active: true
        });
        break;

      case location.pathname === ROUTES.PROFILE:
        breadcrumbs.push({
          label: 'Profile',
          active: true
        });
        break;

      case location.pathname === ROUTES.BILLING:
        breadcrumbs.push({
          label: 'Billing',
          active: true
        });
        break;

      case location.pathname.startsWith('/project/'):
        const projectId = params.id;
        if (projectId) {
          breadcrumbs.push({
            label: `Project ${projectId.substring(0, 8)}...`,
            href: `/project/${projectId}`
          });

          // Add specific project section
          if (location.pathname.includes('/files')) {
            breadcrumbs.push({
              label: 'Files',
              active: true
            });
          } else if (location.pathname.includes('/editor')) {
            breadcrumbs.push({
              label: 'Editor',
              active: true
            });
          } else if (location.pathname.includes('/terminal')) {
            breadcrumbs.push({
              label: 'Terminal',
              active: true
            });
          } else if (location.pathname.includes('/settings')) {
            breadcrumbs.push({
              label: 'Settings',
              active: true
            });
          } else {
            breadcrumbs[breadcrumbs.length - 1].active = true;
          }
        }
        break;

      default:
        // Fallback for unknown routes
        pathSegments.forEach((segment, index) => {
          const href = '/' + pathSegments.slice(0, index + 1).join('/');
          const isLast = index === pathSegments.length - 1;
          
          breadcrumbs.push({
            label: segment.charAt(0).toUpperCase() + segment.slice(1),
            href: isLast ? undefined : href,
            active: isLast
          });
        });
    }

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  // Don't show breadcrumbs on auth pages, landing page, or if only one item
  const hiddenPaths = [ROUTES.LOGIN, ROUTES.REGISTER, ROUTES.LANDING];
  if (hiddenPaths.includes(location.pathname) || breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav className="bg-white/50 backdrop-blur-sm border-b border-gray-200/50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <ol className="flex items-center space-x-2 py-3 text-sm">
          {breadcrumbs.map((item, index) => (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight className="w-4 h-4 text-gray-400 mx-2 flex-shrink-0" />
              )}
              
              {item.active ? (
                <span className="text-gray-900 font-medium truncate max-w-48">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.href!}
                  className="text-gray-500 hover:text-gray-700 transition-colors duration-200 truncate max-w-48"
                >
                  {item.label}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </div>
    </nav>
  );
};

export default Breadcrumbs;