import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
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
  Settings,
  Download,
  Copy,
  Edit3,
  Trash2,
  Eye,
  RefreshCw,
  FolderOpen,
  Share,
  Info,
  Save
} from 'lucide-react';
import ChatInterface from './ChatInterface';
import FileTree from './FileTree';
import FileViewer from './FileViewer';
import { apiService } from '../../services/api';
import '../../styles/design-system.css';

interface ChatWithFilesProps {
  projectId: string;
  initialPrompt?: string;
}

type ViewMode = 'split' | 'chat' | 'files';

const ChatWithFiles: React.FC<ChatWithFilesProps> = ({ projectId, initialPrompt }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [chatWidth, setChatWidth] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showFileSearch, setShowFileSearch] = useState(false);
  const [fileSearchTerm, setFileSearchTerm] = useState('');
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);
  const [copied, setCopied] = useState(false);
  // Split view states
  const [splitIsEditing, setSplitIsEditing] = useState(false);
  const [splitHasUnsavedChanges, setSplitHasUnsavedChanges] = useState(false);
  const [splitIsSaving, setSplitIsSaving] = useState(false);
  
  // Files view states
  const [filesIsEditing, setFilesIsEditing] = useState(false);
  const [filesHasUnsavedChanges, setFilesHasUnsavedChanges] = useState(false);
  const [filesIsSaving, setFilesIsSaving] = useState(false);
  
  const [fileContent, setFileContent] = useState<string>('');
  
  // Live file streaming state
  const [liveFiles, setLiveFiles] = useState<Map<string, string>>(new Map());
  const [currentStreamingFile, setCurrentStreamingFile] = useState<string | null>(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const fileTreeRef = useRef<any>(null);
  const optionsMenuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Helper functions to get current state based on view mode
  const getCurrentEditState = () => {
    return viewMode === 'files' ? filesIsEditing : splitIsEditing;
  };
  
  const getCurrentUnsavedChanges = () => {
    return viewMode === 'files' ? filesHasUnsavedChanges : splitHasUnsavedChanges;
  };
  
  const getCurrentSavingState = () => {
    return viewMode === 'files' ? filesIsSaving : splitIsSaving;
  };
  
  const setCurrentEditState = useCallback((isEditing: boolean) => {
    if (viewMode === 'files') {
      setFilesIsEditing(isEditing);
    } else {
      setSplitIsEditing(isEditing);
    }
  }, [viewMode]);
  
  const setCurrentUnsavedChanges = useCallback((hasChanges: boolean) => {
    if (viewMode === 'files') {
      setFilesHasUnsavedChanges(hasChanges);
    } else {
      setSplitHasUnsavedChanges(hasChanges);
    }
  }, [viewMode]);
  
  const setCurrentSavingState = useCallback((isSaving: boolean) => {
    if (viewMode === 'files') {
      setFilesIsSaving(isSaving);
    } else {
      setSplitIsSaving(isSaving);
    }
  }, [viewMode]);

  // Reset editing states when switching files or view modes
  useEffect(() => {
    // Reset all editing states when file changes
    setSplitIsEditing(false);
    setFilesIsEditing(false);
    setSplitHasUnsavedChanges(false);
    setFilesHasUnsavedChanges(false);
    setSplitIsSaving(false);
    setFilesIsSaving(false);
  }, [selectedFile]);

  // Handle file selection
  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
    setShowOptionsMenu(false); // Close options menu when selecting new file
  };

  // Handle live file updates from streaming
  const handleLiveFileUpdate = useCallback((event: CustomEvent) => {
    const { filename, content, action, token } = event.detail;
    
    console.log('🔴 ChatWithFiles received live file update:', { filename, action, contentLength: content?.length || 0 });
    
    // Update live files state
    setLiveFiles(prev => {
      const newMap = new Map(prev);
      if (action === 'create' || action === 'update') {
        newMap.set(filename, content || '');
        
        // Auto-select the file being streamed if no file is selected
        if (!selectedFile || currentStreamingFile === filename) {
          setSelectedFile(filename);
          setCurrentStreamingFile(filename);
        }
        
        // Trigger file tree refresh to show new files
        if (action === 'create' && fileTreeRef.current?.refreshFileTree) {
          fileTreeRef.current.refreshFileTree();
        }
      }
      return newMap;
    });
    
    // If this is the currently selected file, update the content in real-time
    if (selectedFile === filename || currentStreamingFile === filename) {
      // Dispatch event to FileViewer to update content in real-time
      window.dispatchEvent(new CustomEvent('liveFileContentUpdate', {
        detail: {
          filename,
          content: content || '',
          token,
          isStreaming: action === 'update'
        }
      }));
    }
  }, [selectedFile, currentStreamingFile]);

  // Set up live file update listener
  useEffect(() => {
    const listener = (event: Event) => handleLiveFileUpdate(event as CustomEvent);
    window.addEventListener('liveFileUpdate', listener);
    return () => window.removeEventListener('liveFileUpdate', listener);
  }, [handleLiveFileUpdate]);

  // Reset streaming state when file changes
  useEffect(() => {
    if (selectedFile !== currentStreamingFile) {
      setCurrentStreamingFile(null);
    }
  }, [selectedFile, currentStreamingFile]);

  // Handle file operations
  const handleCopyFile = async () => {
    if (!selectedFile) return;
    try {
      // Get file content and copy to clipboard
      const response = await apiService.getFileContent(projectId, selectedFile);
      const content = response.content || '';
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      setShowOptionsMenu(false);
    } catch (err) {
      console.error('Failed to copy file content:', err);
      // Fallback to copying file path
      try {
        await navigator.clipboard.writeText(selectedFile);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        setShowOptionsMenu(false);
        alert('Copied file path to clipboard (content copy failed)');
      } catch (pathErr) {
        console.error('Failed to copy file path:', pathErr);
        alert('Failed to copy to clipboard. Please try again.');
        setShowOptionsMenu(false);
      }
    }
  };

  const handleDownloadFile = async () => {
    if (!selectedFile) return;
    try {
      const response = await apiService.getFileContent(projectId, selectedFile);
      const content = response.content || '';
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedFile.split('/').pop() || 'file.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setShowOptionsMenu(false);
    } catch (err) {
      console.error('Failed to download file:', err);
      alert('Failed to download file. Please try again.');
    }
  };

  const handleEditFile = () => {
    if (!selectedFile) return;
    console.log('Setting edit mode to true for file:', selectedFile);
    setCurrentEditState(true);
    setShowOptionsMenu(false);
  };

  const handleViewOnlyFile = () => {
    if (!selectedFile) return;
    setCurrentEditState(false);
    setShowOptionsMenu(false);
  };

  const handleDeleteFile = async () => {
    if (!selectedFile) return;
    const fileName = selectedFile.split('/').pop();
    if (window.confirm(`Are you sure you want to delete ${fileName}? This action cannot be undone.`)) {
      try {
        // Check if deleteFile method exists in apiService
        if (typeof (apiService as any).deleteFile === 'function') {
          await (apiService as any).deleteFile(projectId, selectedFile);
          setSelectedFile(null);
          setShowOptionsMenu(false);
          // Refresh file tree
          window.location.reload();
        } else {
          // Fallback: Save empty content to "delete" the file
          await apiService.saveFile(projectId, selectedFile, '');
          alert('File content cleared (delete functionality not fully implemented)');
          setShowOptionsMenu(false);
        }
      } catch (err) {
        console.error('Failed to delete file:', err);
        alert('Failed to delete file. This feature may not be fully implemented yet.');
        setShowOptionsMenu(false);
      }
    }
  };

  const handleRefreshFile = () => {
    if (!selectedFile) return;
    // Force refresh by re-selecting the file
    const currentFile = selectedFile;
    setSelectedFile(null);
    setTimeout(() => setSelectedFile(currentFile), 100);
    setShowOptionsMenu(false);
  };

  const handleSaveFile = async () => {
    if (!selectedFile || !getCurrentUnsavedChanges()) return;
    try {
      setCurrentSavingState(true);
      // Trigger save via a custom event
      window.dispatchEvent(new CustomEvent('save-file', { detail: { filePath: selectedFile } }));
      setShowOptionsMenu(false);
    } catch (err) {
      console.error('Failed to save file:', err);
      alert('Failed to save file. Please try again.');
    } finally {
      setCurrentSavingState(false);
    }
  };

  const handleDuplicateFile = async () => {
    if (!selectedFile) return;
    try {
      const response = await apiService.getFileContent(projectId, selectedFile);
      const content = response.content || '';
      const originalName = selectedFile.split('/').pop() || 'file';
      const pathParts = selectedFile.split('/');
      const fileName = pathParts.pop();
      const filePath = pathParts.join('/');
      
      // Create new file name
      const nameWithoutExt = originalName.split('.').slice(0, -1).join('.');
      const extension = originalName.split('.').pop();
      const newFileName = `${nameWithoutExt}_copy.${extension}`;
      const newFilePath = filePath ? `${filePath}/${newFileName}` : newFileName;
      
      await apiService.saveFile(projectId, newFilePath, content);
      setShowOptionsMenu(false);
      alert('File duplicated successfully!');
    } catch (err) {
      console.error('Failed to duplicate file:', err);
      alert('Failed to duplicate file. Please try again.');
    }
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

  // Close options menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (optionsMenuRef.current && !optionsMenuRef.current.contains(event.target as Node)) {
        setShowOptionsMenu(false);
      }
    };

    if (showOptionsMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showOptionsMenu]);

  return (
    <div 
      ref={containerRef}
      className={`h-full bg-black flex flex-col ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {/* Clean Header */}
      <div className="flex items-center justify-between p-4 bg-gray-900/50 backdrop-blur-sm border-b border-gray-700/50">
        <div className="flex items-center space-x-1">
          {/* View Mode Tabs */}
          <button
            onClick={() => setViewMode('chat')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'chat'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <MessageSquare className="w-4 h-4 inline mr-2" />
            Chat
          </button>
          
          <button
            onClick={() => setViewMode('split')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'split'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <Code2 className="w-4 h-4 inline mr-2" />
            Split
          </button>
          
          <button
            onClick={() => setViewMode('files')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              viewMode === 'files'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Files
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {/* Current File Display */}
          {selectedFile && (
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-lg">
              <FileText className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-300 max-w-48 truncate">
                {selectedFile.split('/').pop()}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <button
            onClick={() => setShowFileSearch(!showFileSearch)}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all"
          >
            <Search className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* File Search Bar */}
      {showFileSearch && (
        <div className="px-4 py-3 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={fileSearchTerm}
              onChange={(e) => setFileSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800/50 backdrop-blur-sm border border-gray-600/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500/50 text-white placeholder-gray-400"
            />
            <button
              onClick={() => setShowFileSearch(false)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300"
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
            <ChatInterface projectId={projectId} initialPrompt={initialPrompt} />
          </div>
        )}

        {viewMode === 'files' && (
          <div className="w-full h-full flex">
            {/* File Tree */}
            <div className="w-80 bg-gray-900 border-r border-gray-700/50 flex flex-col">
              <div className="p-4 border-b border-gray-700/50">
                <div className="flex items-center space-x-2">
                  <Folder className="w-5 h-5 text-blue-500" />
                  <h3 className="font-semibold text-white">Project Files</h3>
                </div>
              </div>
              <div className="flex-1 overflow-auto">
                <FileTree
                  ref={fileTreeRef}
                  projectId={projectId}
                  onFileSelect={handleFileSelect}
                  selectedFile={selectedFile}
                  liveFiles={liveFiles}
                />
              </div>
            </div>

            {/* File Viewer */}
            <div className="flex-1 bg-black flex flex-col">
              {selectedFile ? (
                <>
                  {/* File Header */}
                  <div className="p-4 border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm flex-shrink-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <FileText className="w-5 h-5 text-blue-500" />
                        <h3 className="font-semibold text-white">
                          {selectedFile.split('/').pop()}
                        </h3>
                        {getCurrentEditState() && (
                          <span className="px-2 py-1 text-xs bg-green-600/20 text-green-400 border border-green-500/30 rounded-md">
                            Editing
                          </span>
                        )}
                        {currentStreamingFile === selectedFile && (
                          <span className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-md animate-pulse">
                            Streaming...
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <button className="p-1.5 text-gray-400 hover:text-yellow-500 rounded transition-colors">
                          <Star className="w-4 h-4" />
                        </button>
                        <div className="relative" ref={optionsMenuRef}>
                          <button 
                            ref={buttonRef}
                            onClick={(e) => {
                              if (!showOptionsMenu) {
                                const rect = e.currentTarget.getBoundingClientRect();
                                setDropdownPosition({
                                  top: rect.bottom + 4,
                                  right: window.innerWidth - rect.right
                                });
                              }
                              setShowOptionsMenu(!showOptionsMenu);
                            }}
                            className="p-1.5 text-gray-400 hover:text-gray-300 rounded transition-colors"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    {/* Breadcrumb */}
                    <div className="flex items-center space-x-1 mt-2 text-sm text-gray-400">
                      {selectedFile.split('/').map((part, index, array) => (
                        <React.Fragment key={index}>
                          <span className="hover:text-gray-300 cursor-pointer">
                            {part}
                          </span>
                          {index < array.length - 1 && <ChevronRight className="w-3 h-3" />}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                  
                  {/* File Content */}
                  <div className="flex-1 min-h-0">
                    <FileViewer
                      projectId={projectId}
                      filePath={selectedFile}
                      showHeader={false}
                      showFooter={true}
                      forceEditMode={getCurrentEditState()}
                      onEditModeChange={setCurrentEditState}
                      onUnsavedChanges={setCurrentUnsavedChanges}
                      onSaving={setCurrentSavingState}
                      liveContent={liveFiles.get(selectedFile)}
                      isStreaming={currentStreamingFile === selectedFile}
                    />
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-white mb-2">
                      No file selected
                    </h3>
                    <p className="text-gray-400">
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
              className="bg-black border-r border-gray-700/50 flex flex-col"
              style={{ width: `${chatWidth}%` }}
            >
              <div className="p-4 border-b border-gray-700/50">
                <h3 className="font-semibold text-white flex items-center">
                  <MessageSquare className="w-5 h-5 text-blue-500 mr-2" />
                  AI Assistant
                </h3>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatInterface projectId={projectId} initialPrompt={initialPrompt} />
              </div>
            </div>

            {/* Resizer */}
            <div
              className="w-1 bg-gray-700/50 hover:bg-blue-500 cursor-col-resize flex-shrink-0 relative group transition-colors"
              onMouseDown={handleMouseDown}
            >
              <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-blue-500/20" />
            </div>

            {/* Files Panel */}
            <div 
              className="bg-gray-800 flex h-full"
              style={{ width: `${100 - chatWidth}%` }}
            >
              {/* File Tree */}
              <div className="w-80 bg-gray-900 border-r border-gray-700/50 flex flex-col h-full">
                <div className="p-4 border-b border-gray-700/50 flex-shrink-0">
                  <div className="flex items-center space-x-2">
                    <Folder className="w-5 h-5 text-green-500" />
                    <h3 className="font-semibold text-white">Files</h3>
                  </div>
                </div>
                <div className="flex-1 overflow-auto">
                  <FileTree
                    ref={fileTreeRef}
                    projectId={projectId}
                    onFileSelect={handleFileSelect}
                    selectedFile={selectedFile}
                    liveFiles={liveFiles}
                  />
                </div>
              </div>

              {/* File Viewer */}
              <div className="flex-1 bg-black flex flex-col h-full">
                {selectedFile ? (
                  <>
                    {/* File Header */}
                    <div className="p-4 border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm flex-shrink-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <FileText className="w-5 h-5 text-blue-500" />
                          <h3 className="font-semibold text-white">
                            {selectedFile.split('/').pop()}
                          </h3>
                          {getCurrentEditState() && (
                            <span className="px-2 py-1 text-xs bg-green-600/20 text-green-400 border border-green-500/30 rounded-md">
                              Editing
                            </span>
                          )}
                          {currentStreamingFile === selectedFile && (
                            <span className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-md animate-pulse">
                              Streaming...
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button className="p-1.5 text-gray-400 hover:text-yellow-500 rounded transition-colors">
                            <Star className="w-4 h-4" />
                          </button>
                          <div className="relative" ref={optionsMenuRef}>
                            <button 
                              ref={buttonRef}
                              onClick={(e) => {
                                if (!showOptionsMenu) {
                                  const rect = e.currentTarget.getBoundingClientRect();
                                  setDropdownPosition({
                                    top: rect.bottom + 4,
                                    right: window.innerWidth - rect.right
                                  });
                                }
                                setShowOptionsMenu(!showOptionsMenu);
                              }}
                              className="p-1.5 text-gray-400 hover:text-gray-300 rounded transition-colors"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                      
                      {/* Breadcrumb */}
                      <div className="flex items-center space-x-1 mt-2 text-sm text-gray-400">
                        {selectedFile.split('/').map((part, index, array) => (
                          <React.Fragment key={index}>
                            <span className="hover:text-gray-300 cursor-pointer">
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
                        forceEditMode={getCurrentEditState()}
                        onEditModeChange={setCurrentEditState}
                        onUnsavedChanges={setCurrentUnsavedChanges}
                        onSaving={setCurrentSavingState}
                        liveContent={liveFiles.get(selectedFile)}
                        isStreaming={currentStreamingFile === selectedFile}
                      />
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <Code2 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-white mb-2">
                        Select a file to edit
                      </h3>
                      <p className="text-gray-400">
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
      
      {/* Portal for Options Dropdown Menu - Renders outside component hierarchy */}
      {showOptionsMenu && createPortal(
        <div 
          className="fixed w-52 bg-gray-900/95 backdrop-blur-sm border border-gray-700/50 rounded-lg shadow-2xl"
          style={{ 
            top: dropdownPosition.top,
            right: dropdownPosition.right,
            zIndex: 999999
          }}
          ref={optionsMenuRef}
        >
                                <div className="py-1">
                                  {/* Save option - only show when editing and has unsaved changes */}
                                  {getCurrentEditState() && getCurrentUnsavedChanges() && (
                                    <>
                                      <button
                                        onClick={handleSaveFile}
                                        disabled={getCurrentSavingState()}
                                        className="w-full px-4 py-2 text-left text-sm text-green-300 hover:bg-green-900/20 hover:text-green-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                      >
                                        <Save className="w-4 h-4" />
                                        <span>{getCurrentSavingState() ? 'Saving...' : 'Save File'}</span>
                                      </button>
                                      <hr className="my-1 border-gray-700/50" />
                                    </>
                                  )}
                                  
                                  <button
                                    onClick={handleCopyFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Copy className="w-4 h-4" />
                                    <span>{copied ? 'Copied!' : 'Copy Content'}</span>
                                  </button>
                                  
                                  <button
                                    onClick={handleDownloadFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Download className="w-4 h-4" />
                                    <span>Download</span>
                                  </button>
                                  
                                  <button
                                    onClick={handleEditFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Edit3 className="w-4 h-4" />
                                    <span>Edit File</span>
                                  </button>
                                  
                                  <button
                                    onClick={handleViewOnlyFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Eye className="w-4 h-4" />
                                    <span>View Only</span>
                                  </button>
                                  
                                  <button
                                    onClick={handleDuplicateFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Copy className="w-4 h-4" />
                                    <span>Duplicate</span>
                                  </button>
                                  
                                  <button
                                    onClick={() => {
                                      if (selectedFile) {
                                        const folder = selectedFile.split('/').slice(0, -1).join('/');
                                        console.log('Open in folder:', folder);
                                        setShowOptionsMenu(false);
                                      }
                                    }}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <FolderOpen className="w-4 h-4" />
                                    <span>Show in Folder</span>
                                  </button>
                                  
                                  <button
                                    onClick={() => {
                                      if (selectedFile) {
                                        navigator.clipboard.writeText(`${window.location.origin}/project/${projectId}/file/${encodeURIComponent(selectedFile)}`);
                                        alert('File link copied to clipboard!');
                                        setShowOptionsMenu(false);
                                      }
                                    }}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Share className="w-4 h-4" />
                                    <span>Copy Link</span>
                                  </button>
                                  
                                  <hr className="my-1 border-gray-700/50" />
                                  
                                  <button
                                    onClick={handleRefreshFile}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <RefreshCw className="w-4 h-4" />
                                    <span>Refresh</span>
                                  </button>
                                  
                                  <button
                                    onClick={() => {
                                      if (selectedFile) {
                                        alert(`File: ${selectedFile.split('/').pop()}\nPath: ${selectedFile}\nLast modified: ${new Date().toLocaleString()}`);
                                        setShowOptionsMenu(false);
                                      }
                                    }}
                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-800/50 hover:text-white flex items-center space-x-2"
                                  >
                                    <Info className="w-4 h-4" />
                                    <span>Properties</span>
                                  </button>
                                  
                                  <button
                                    onClick={handleDeleteFile}
                                    className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 flex items-center space-x-2"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                    <span>Delete</span>
                                  </button>
                                </div>
                              </div>
        , document.body
      )}
    </div>
  );
};

export default ChatWithFiles;