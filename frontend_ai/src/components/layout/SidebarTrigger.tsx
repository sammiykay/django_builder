import React, { useState, useEffect, useRef } from 'react';
import { Folder } from 'lucide-react';

interface SidebarTriggerProps {
  onTrigger: (isTriggered: boolean) => void;
  isActive: boolean;
}

const SidebarTrigger: React.FC<SidebarTriggerProps> = ({ onTrigger, isActive }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showHint, setShowHint] = useState(true);
  const triggerRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const isNearLeftEdge = e.clientX <= 50; // Trigger within 50px of left edge
      const isOverSidebar = e.clientX <= 320 && isActive; // Sidebar is 320px wide (w-80)
      
      if (isNearLeftEdge && !isActive) {
        setIsHovered(true);
        onTrigger(true);
        
        // Clear any existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      } else if (!isNearLeftEdge && !isOverSidebar && isActive) {
        // Only hide if mouse is not near edge AND not over sidebar
        timeoutRef.current = setTimeout(() => {
          setIsHovered(false);
          onTrigger(false);
        }, 300);
      } else if (isOverSidebar) {
        // Clear timeout if mouse is over sidebar
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      }
    };

    const handleMouseLeave = () => {
      // Add delay before hiding when mouse leaves the window
      timeoutRef.current = setTimeout(() => {
        setIsHovered(false);
        onTrigger(false);
      }, 300);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [onTrigger, isActive]);

  useEffect(() => {
    // Hide hint after 5 seconds
    const hintTimeout = setTimeout(() => {
      setShowHint(false);
    }, 5000);

    return () => clearTimeout(hintTimeout);
  }, []);

  return (
    <>
      {/* Invisible trigger zone */}
      <div
        ref={triggerRef}
        className="fixed left-0 top-0 w-12 h-full z-30 pointer-events-none"
      />

      {/* Visual indicator when hovering */}
      {(isHovered || isActive) && (
        <div
          className={`fixed left-0 top-1/2 transform -translate-y-1/2 z-40 transition-all duration-300 ${
            isActive ? 'translate-x-2' : 'translate-x-0'
          }`}
        >
          <div
            className={`bg-blue-600 text-white p-2 rounded-r-lg shadow-lg transition-all duration-300 ${
              isActive ? 'opacity-80 scale-110' : 'opacity-60 scale-100'
            }`}
          >
            <Folder className="w-5 h-5" />
          </div>
        </div>
      )}

      {/* Hint tooltip */}
      {showHint && !isActive && (
        <div
          className={`fixed left-16 top-1/2 transform -translate-y-1/2 z-50 transition-all duration-500 ${
            isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
          }`}
        >
          <div className="bg-gray-800 text-white px-3 py-2 rounded-lg shadow-lg border border-gray-600 text-sm">
            <div className="flex items-center space-x-2">
              <Folder className="w-4 h-4 text-blue-400" />
              <span>Hover here to see your projects</span>
            </div>
            <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1">
              <div className="w-2 h-2 bg-gray-800 rotate-45 border-l border-b border-gray-600"></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SidebarTrigger;