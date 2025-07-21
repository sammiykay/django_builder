import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Folder, FileText, Menu, X } from 'lucide-react';
import ChatInterface from './ChatInterface';
import FileTree from './FileTree';
import FileViewer from './FileViewer';
import Button from '../ui/Button';
import '../../styles/design-system.css';

interface ChatWithFilesProps {
  projectId: string;
}

const ChatWithFiles: React.FC<ChatWithFilesProps> = ({ projectId }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [chatWidth, setChatWidth] = useState(50); // Percentage
  const [isDragging, setIsDragging] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [showFilePanel, setShowFilePanel] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
    if (isMobile) {
      setShowFilePanel(false); // Close file panel on mobile after selection
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isMobile) {
      setIsDragging(true);
      e.preventDefault();
    }
  };

  // Check for mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;
      
      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const percentage = ((e.clientX - rect.left) / rect.width) * 100;
      
      // Constrain between 20% and 80%
      const newWidth = Math.max(20, Math.min(80, percentage));
      setChatWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return (
    <div 
      ref={containerRef}
      className="h-full relative bg-primary"
      style={{ cursor: isDragging ? 'col-resize' : 'default' }}
    >
      {isMobile ? (
        /* Mobile Layout */
        <div className="h-full flex flex-col">
          {/* Mobile Header with File Toggle */}
          <div className="flex items-center justify-between p-4 bg-secondary border-b border-secondary">
            <h2 className="text-lg font-semibold text-primary">Chat & Files</h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowFilePanel(!showFilePanel)}
              icon={showFilePanel ? <X className="w-4 h-4" /> : <Folder className="w-4 h-4" />}
            >
              {showFilePanel ? 'Hide Files' : 'Show Files'}
            </Button>
          </div>

          {showFilePanel ? (
            /* Mobile File Panel */
            <div className="flex-1 flex flex-col">
              {/* File Tree */}
              <div className="flex-1 min-h-0">
                <FileTree
                  projectId={projectId}
                  onFileSelect={handleFileSelect}
                  selectedFile={selectedFile}
                />
              </div>
              
              {/* File Viewer (if file selected) */}
              {selectedFile && (
                <div className="flex-1 border-t border-secondary">
                  <FileViewer
                    projectId={projectId}
                    filePath={selectedFile}
                  />
                </div>
              )}
            </div>
          ) : (
            /* Mobile Chat Interface */
            <div className="flex-1">
              <ChatInterface projectId={projectId} />
            </div>
          )}
        </div>
      ) : (
        /* Desktop Layout */
        <div className="h-full flex">
          {/* Left Side - Chat Interface */}
          <div 
            className="flex flex-col min-w-0"
            style={{ width: `${chatWidth}%` }}
          >
            <ChatInterface projectId={projectId} />
          </div>

          {/* Resizer */}
          <div
            className="w-1 bg-tertiary hover:bg-blue-500/50 cursor-col-resize flex-shrink-0 relative group transition-colors"
            onMouseDown={handleMouseDown}
          >
            <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-500/20 transition-colors"></div>
          </div>

          {/* Right Side - File Tree and Viewer */}
          <div 
            className="flex border-l border-secondary"
            style={{ width: `${100 - chatWidth}%` }}
          >
            {/* File Tree */}
            <div className="w-80 flex-shrink-0 min-w-0">
              <FileTree
                projectId={projectId}
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
              />
            </div>

            {/* File Viewer */}
            <div className="flex-1 min-w-0">
              <FileViewer
                projectId={projectId}
                filePath={selectedFile}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWithFiles;