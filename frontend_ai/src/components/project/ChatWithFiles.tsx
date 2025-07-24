import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  FileText, 
  Code2, 
  Maximize2,
  Minimize2,
  Search,
  X,
  MoreHorizontal,
  Folder,
  ChevronRight,
  Star,
  Settings
} from 'lucide-react';
import ChatInterface from './ChatInterface';
import FileTree from './FileTree';
import FileViewer from './FileViewer';
import '../../styles/design-system.css';

interface ChatWithFilesProps {
  projectId: string;
}

type ViewMode = 'split' | 'chat' | 'files';

const ChatWithFiles: React.FC<ChatWithFilesProps> = ({ projectId }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [chatWidth, setChatWidth] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showFileSearch, setShowFileSearch] = useState(false);
  const [fileSearchTerm, setFileSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle file selection
  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
  };

  // Handle resizing
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;
      
      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const percentage = ((e.clientX - rect.left) / rect.width) * 100;
      const newWidth = Math.max(25, Math.min(75, percentage));
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
      className={`h-full bg-gray-50 dark:bg-gray-900 flex flex-col ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {/* Clean Header */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-1">
          {/* View Mode Tabs */}
          <button
            onClick={() => setViewMode('chat')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'chat'
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <MessageSquare className="w-4 h-4 inline mr-2" />
            Chat
          </button>
          
          <button
            onClick={() => setViewMode('split')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'split'
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <Code2 className="w-4 h-4 inline mr-2" />
            Split
          </button>
          
          <button
            onClick={() => setViewMode('files')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'files'
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Files
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {/* Current File Display */}
          {selectedFile && (
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <FileText className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 max-w-48 truncate">
                {selectedFile.split('/').pop()}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <button
            onClick={() => setShowFileSearch(!showFileSearch)}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all"
          >
            <Search className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* File Search Bar */}
      {showFileSearch && (
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={fileSearchTerm}
              onChange={(e) => setFileSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-gray-100"
            />
            <button
              onClick={() => setShowFileSearch(false)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {viewMode === 'chat' && (
          <div className="w-full h-full">
            <ChatInterface projectId={projectId} />
          </div>
        )}

        {viewMode === 'files' && (
          <div className="w-full h-full flex">
            {/* File Tree */}
            <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-2">
                  <Folder className="w-5 h-5 text-blue-500" />
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Project Files</h3>
                </div>
              </div>
              <div className="flex-1 overflow-auto">
                <FileTree
                  projectId={projectId}
                  onFileSelect={handleFileSelect}
                  selectedFile={selectedFile}
                />
              </div>
            </div>

            {/* File Viewer */}
            <div className="flex-1 bg-white dark:bg-gray-900">
              {selectedFile ? (
                <FileViewer
                  projectId={projectId}
                  filePath={selectedFile}
                />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                      No file selected
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      Choose a file from the sidebar to view its contents
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {viewMode === 'split' && (
          <div className="w-full h-full flex">
            {/* Chat Panel */}
            <div 
              className="bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col"
              style={{ width: `${chatWidth}%` }}
            >
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                  <MessageSquare className="w-5 h-5 text-blue-500 mr-2" />
                  AI Assistant
                </h3>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatInterface projectId={projectId} />
              </div>
            </div>

            {/* Resizer */}
            <div
              className="w-1 bg-gray-200 dark:bg-gray-700 hover:bg-blue-500 cursor-col-resize flex-shrink-0 relative group transition-colors"
              onMouseDown={handleMouseDown}
            >
              <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-500/20" />
            </div>

            {/* Files Panel */}
            <div 
              className="bg-gray-50 dark:bg-gray-800 flex h-full"
              style={{ width: `${100 - chatWidth}%` }}
            >
              {/* File Tree */}
              <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
                  <div className="flex items-center space-x-2">
                    <Folder className="w-5 h-5 text-green-500" />
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">Files</h3>
                  </div>
                </div>
                <div className="flex-1 overflow-auto">
                  <FileTree
                    projectId={projectId}
                    onFileSelect={handleFileSelect}
                    selectedFile={selectedFile}
                  />
                </div>
              </div>

              {/* File Viewer */}
              <div className="flex-1 bg-white dark:bg-gray-900 flex flex-col h-full">
                {selectedFile ? (
                  <>
                    {/* File Header */}
                    <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <FileText className="w-5 h-5 text-blue-500" />
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                            {selectedFile.split('/').pop()}
                          </h3>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button className="p-1.5 text-gray-400 hover:text-yellow-500 rounded transition-colors">
                            <Star className="w-4 h-4" />
                          </button>
                          <button className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors">
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Breadcrumb */}
                      <div className="flex items-center space-x-1 mt-2 text-sm text-gray-500 dark:text-gray-400">
                        {selectedFile.split('/').map((part, index, array) => (
                          <React.Fragment key={index}>
                            <span className="hover:text-gray-700 dark:hover:text-gray-300 cursor-pointer">
                              {part}
                            </span>
                            {index < array.length - 1 && <ChevronRight className="w-3 h-3" />}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                    
                    {/* File Content - This needs to take full remaining height */}
                    <div className="flex-1 min-h-0">
                      <FileViewer
                        projectId={projectId}
                        filePath={selectedFile}
                        showHeader={false}
                        showFooter={true}
                      />
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <Code2 className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                        Select a file to edit
                      </h3>
                      <p className="text-gray-500 dark:text-gray-400">
                        Choose a file from the sidebar to start coding
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatWithFiles;