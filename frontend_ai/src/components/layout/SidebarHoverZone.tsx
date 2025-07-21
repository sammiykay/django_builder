import React, { useState, useEffect, useRef } from 'react';
import { Folder } from 'lucide-react';

interface SidebarHoverZoneProps {
  onTrigger: (isTriggered: boolean) => void;
  isActive: boolean;
}

const SidebarHoverZone: React.FC<SidebarHoverZoneProps> = ({ onTrigger, isActive }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showHint, setShowHint] = useState(true);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Create a larger hover zone that includes the sidebar area when it's open
      const hoverZone = isActive ? 320 : 20; // 320px when sidebar is open, 20px when closed (shifted more left)
      const isInHoverZone = e.clientX <= hoverZone;
      
      if (isInHoverZone && !isActive) {
        // Show sidebar when hovering near left edge
        setIsHovered(true);
        onTrigger(true);
        
        // Clear any existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      } else if (isInHoverZone && isActive) {
        // Keep sidebar open when mouse is in the zone
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      } else if (!isInHoverZone && isActive) {
        // Hide sidebar with delay when mouse leaves the zone
        timeoutRef.current = setTimeout(() => {
          setIsHovered(false);
          onTrigger(false);
        }, 300);
      }
    };

    const handleMouseLeave = () => {
      // Hide sidebar when mouse leaves the window
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
      {/* Always visible sidebar indicator - Bottom Left */}
      <div className="fixed left-0 bottom-4 z-40">
        <div className="ml-px flex items-center">
          <button className="bg-transparent text-gray-400 cursor-pointer flex flex-col items-center group">
            <div className="flex select-none items-center justify-center size-8 overflow-hidden rounded-full shrink-0 bg-gray-800 border border-gray-600 text-gray-400 w-6 h-6 mb-2 group-hover:bg-blue-600 group-hover:text-white transition-colors">
              <Folder className="w-3 h-3" />
            </div>
            <div className="text-lg group-hover:text-blue-400 transition-colors">
              ☰
            </div>
          </button>
        </div>
      </div>

      {/* Enhanced visual indicator when hovering */}
      {(isHovered || isActive) && !isActive && (
        <div
          className="fixed left-0 top-1/2 transform -translate-y-1/2 z-40 transition-all duration-300"
        >
          <div className="bg-blue-600 text-white p-3 rounded-r-lg shadow-lg opacity-90 border-r-4 border-blue-400">
            <div className="flex flex-col items-center space-y-1">
              <Folder className="w-5 h-5" />
              <span className="text-xs">Projects</span>
            </div>
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

export default SidebarHoverZone;