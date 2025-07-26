import React, { useState, useEffect, useRef } from 'react';
import { Editor } from '@monaco-editor/react';
import { Save, Loader2, FileText, Folder, FolderOpen, ChevronRight, ChevronDown, Zap, Eye, Wifi, WifiOff } from 'lucide-react';
import { apiService } from '../../services/api';
import { aiStreamingService } from '../../services/aiStreamingService';
import { ProjectFile } from '../../types/api';

interface FileEditorProps {
  projectId: string;
}

interface FileSystemNode {
  path: string;
  size: number;
  modified: string;
  type: 'file' | 'directory';
  is_directory: boolean;
  extension?: string;
}

interface FileTreeNode extends FileSystemNode {
  name: string;
  children?: FileTreeNode[];
  isExpanded?: boolean;
}

const FileEditor: React.FC<FileEditorProps> = ({ projectId }) => {
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingTree, setIsLoadingTree] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // AI streaming states
  const [isStreamingConnected, setIsStreamingConnected] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [liveFiles, setLiveFiles] = useState<{[filename: string]: string}>({});
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set());
  const editorRef = useRef<any>(null);

  useEffect(() => {
    loadFileTree();
    initializeAIStreaming();
  }, [projectId]);

  const initializeAIStreaming = () => {
    // Connect to AI streaming service
    aiStreamingService.connect(projectId);
    
    // Subscribe to file changes
    const unsubscribeFiles = aiStreamingService.subscribeToFiles((file) => {
      
      // Update live files state
      setLiveFiles(prev => ({
        ...prev,
        [file.filename]: file.content
      }));
      
      // Mark as recently updated
      setRecentlyUpdated(prev => new Set([...prev, file.filename]));
      
      // If this file is currently open, update the editor
      if (selectedFile === file.filename) {
        setFileContent(file.content);
        setOriginalContent(file.content);
      }
      
      // Clear the recently updated status after 3 seconds
      setTimeout(() => {
        setRecentlyUpdated(prev => {
          const newSet = new Set(prev);
          newSet.delete(file.filename);
          return newSet;
        });
      }, 3000);
      
      // Refresh file tree to show new files
      setTimeout(() => {
        loadFileTree();
      }, 500);
    });

    // Subscribe to status updates
    const unsubscribeStatus = aiStreamingService.subscribeToStatus((status) => {
      switch (status.type) {
        case 'connected':
          setIsStreamingConnected(true);
          break;
        case 'disconnected':
          setIsStreamingConnected(false);
          break;
        case 'generation_started':
          setIsGenerating(true);
          setLiveFiles({});
          setRecentlyUpdated(new Set());
          break;
        case 'generation_completed':
          setIsGenerating(false);
          // Refresh the file tree after generation completes
          setTimeout(() => {
            loadFileTree();
          }, 1000);
          break;
        case 'error':
          setIsGenerating(false);
          break;
      }
    });

    // Cleanup function
    return () => {
      unsubscribeFiles();
      unsubscribeStatus();
    };
  }, [projectId]);


  const loadFileTree = async () => {
    try {
      setIsLoadingTree(true);
      setError(null);
      const files = await apiService.getFilesystemFiles(projectId);
      const tree = buildFileTree(files);
      setFileTree(tree);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load file tree');
    } finally {
      setIsLoadingTree(false);
    }
  };

  const buildFileTree = (files: FileSystemNode[]): FileTreeNode[] => {
    const tree: FileTreeNode[] = [];
    const pathMap: { [key: string]: FileTreeNode } = {};

    // Sort files to ensure directories come before their contents
    const sortedFiles = files.sort((a, b) => {
      if (a.is_directory && !b.is_directory) return -1;
      if (!a.is_directory && b.is_directory) return 1;
      return a.path.localeCompare(b.path);
    });

    sortedFiles.forEach(file => {
      const parts = file.path.split('/');
      const name = parts[parts.length - 1];
      
      const node: FileTreeNode = {
        ...file,
        name,
        children: file.is_directory ? [] : undefined,
        isExpanded: false
      };

      pathMap[file.path] = node;

      if (parts.length === 1) {
        // Root level file/directory
        tree.push(node);
      } else {
        // Nested file/directory
        const parentPath = parts.slice(0, -1).join('/');
        const parent = pathMap[parentPath];
        if (parent && parent.children) {
          parent.children.push(node);
        }
      }
    });

    return tree;
  };

  const handleFileSelect = async (filePath: string) => {
    if (selectedFile === filePath) return;
    
    setSelectedFile(filePath);
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.getFileContent(projectId, filePath);
      setFileContent(response.content);
      setOriginalContent(response.content);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load file content');
      setFileContent('');
      setOriginalContent('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    
    setIsSaving(true);
    setError(null);

    try {
      await apiService.saveFile(projectId, selectedFile, fileContent);
      setOriginalContent(fileContent);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save file');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleFolder = (node: FileTreeNode) => {
    const updateTree = (nodes: FileTreeNode[]): FileTreeNode[] => {
      return nodes.map(n => {
        if (n.path === node.path) {
          return { ...n, isExpanded: !n.isExpanded };
        }
        if (n.children) {
          return { ...n, children: updateTree(n.children) };
        }
        return n;
      });
    };
    
    setFileTree(updateTree(fileTree));
  };

  const renderFileTree = (nodes: FileTreeNode[], depth = 0) => {
    return nodes.map(node => {
      const isGenerating = currentlyGenerating === node.path;
      const isSelected = selectedFile === node.path;
      
      return (
        <div key={node.path}>
          <div
            className={`flex items-center space-x-2 py-1 px-2 hover:bg-gray-700 cursor-pointer relative ${
              isSelected ? 'bg-blue-600' : isGenerating ? 'bg-green-900/50 border-l-2 border-green-400' : ''
            }`}
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
            onClick={() => {
              if (node.is_directory) {
                toggleFolder(node);
              } else {
                handleFileSelect(node.path);
              }
            }}
          >
          {node.is_directory && (
            <span className="text-gray-400">
              {node.isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </span>
          )}
          <span className="text-gray-400">
            {node.is_directory ? (
              node.isExpanded ? (
                <FolderOpen className="w-4 h-4" />
              ) : (
                <Folder className="w-4 h-4" />
              )
            ) : (
              <FileText className="w-4 h-4" />
            )}
          </span>
          <span className={`text-sm ${isSelected ? 'text-white' : recentlyUpdated.has(node.path) ? 'text-green-300' : 'text-gray-300'}`}>
            {node.name}
          </span>
          
          {/* Recently Updated Indicator */}
          {recentlyUpdated.has(node.path) && (
            <span className="flex items-center space-x-1 ml-auto">
              <Zap className="w-3 h-3 text-green-400 animate-pulse" />
              <span className="text-xs text-green-400">Live</span>
            </span>
          )}
          
          {/* Live File from Streaming */}
          {liveFiles[node.path] && !recentlyUpdated.has(node.path) && (
            <span className="flex items-center space-x-1 ml-auto">
              <Wifi className="w-3 h-3 text-blue-400" />
              <span className="text-xs text-blue-400">Updated</span>
            </span>
          )}
          
          {/* File Size (when not live updating) */}
          {!node.is_directory && !recentlyUpdated.has(node.path) && !liveFiles[node.path] && (
            <span className="text-xs text-gray-500 ml-auto">
              {formatFileSize(node.size)}
            </span>
          )}
        </div>
        {node.is_directory && node.isExpanded && node.children && (
          <div>
            {renderFileTree(node.children, depth + 1)}
          </div>
        )}
      </div>
    )});
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getLanguage = (filePath: string) => {
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py': return 'python';
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'jsx': return 'javascript';
      case 'tsx': return 'typescript';
      case 'html': return 'html';
      case 'css': return 'css';
      case 'scss': return 'scss';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'yml':
      case 'yaml': return 'yaml';
      case 'xml': return 'xml';
      case 'sql': return 'sql';
      case 'sh': return 'shell';
      case 'txt': return 'plaintext';
      default: return 'plaintext';
    }
  };

  if (isLoadingTree) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-gray-400">Loading files...</span>
        </div>
      </div>
    );
  }

  if (error && fileTree.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadFileTree}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (fileTree.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No files found in this project</p>
          <p className="text-sm mt-2">Generate some code using the AI Generator first</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-900">
      {/* File Tree */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 overflow-y-auto">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white">Project Files</h3>
            <button
              onClick={loadFileTree}
              className="p-1 text-gray-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <Loader2 className="w-4 h-4" />
            </button>
          </div>
          
          {/* Streaming Status */}
          <div className="flex items-center gap-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${isStreamingConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
            <span className={isStreamingConnected ? 'text-green-400' : 'text-gray-500'}>
              {isStreamingConnected ? 'Live Updates' : 'Disconnected'}
            </span>
            {isGenerating && (
              <>
                <span className="text-gray-400">•</span>
                <span className="text-blue-400 flex items-center gap-1">
                  <Zap className="w-3 h-3 animate-pulse" />
                  Generating
                </span>
              </>
            )}
          </div>
          
          {/* Live Files Counter */}
          {Object.keys(liveFiles).length > 0 && (
            <div className="mt-2 text-xs text-green-300 bg-green-900/20 border border-green-500/30 rounded px-2 py-1">
              {Object.keys(liveFiles).length} files updating live
            </div>
          )}
        </div>
        <div className="p-2">
          {renderFileTree(fileTree)}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="bg-red-900/50 border-b border-red-500 p-4">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {selectedFile ? (
          <>
            {/* Editor Header */}
            <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {recentlyUpdated.has(selectedFile) ? (
                    <Zap className="w-5 h-5 text-green-400 animate-pulse" />
                  ) : liveFiles[selectedFile] ? (
                    <Wifi className="w-5 h-5 text-blue-400" />
                  ) : (
                    <FileText className="w-5 h-5 text-gray-400" />
                  )}
                  <span className={`font-medium ${recentlyUpdated.has(selectedFile) ? 'text-green-300' : liveFiles[selectedFile] ? 'text-blue-300' : 'text-white'}`}>
                    {selectedFile}
                  </span>
                </div>
                
                {/* Live Update Indicator */}
                {recentlyUpdated.has(selectedFile) && (
                  <div className="flex items-center space-x-2 px-2 py-1 bg-green-900/30 border border-green-500/30 rounded-lg">
                    <Eye className="w-4 h-4 text-green-400" />
                    <span className="text-xs text-green-300">Live Update</span>
                  </div>
                )}
                
                {/* AI Generated Indicator */}
                {liveFiles[selectedFile] && !recentlyUpdated.has(selectedFile) && (
                  <div className="flex items-center space-x-2 px-2 py-1 bg-blue-900/30 border border-blue-500/30 rounded-lg">
                    <Wifi className="w-4 h-4 text-blue-400" />
                    <span className="text-xs text-blue-300">AI Generated</span>
                  </div>
                )}
                
                {/* Unsaved Changes Indicator */}
                {!recentlyUpdated.has(selectedFile) && !liveFiles[selectedFile] && fileContent !== originalContent && (
                  <span className="w-2 h-2 bg-yellow-400 rounded-full" title="Unsaved changes" />
                )}
              </div>
              <button
                onClick={handleSave}
                disabled={isSaving || fileContent === originalContent || recentlyUpdated.has(selectedFile)}
                className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span className="text-sm">{isSaving ? 'Saving...' : 'Save'}</span>
              </button>
            </div>

            {/* Generation Status */}
            {isGenerating && (
              <div className="bg-blue-900/20 border-b border-blue-500/30 px-4 py-2">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 animate-pulse text-blue-400" />
                  <span className="text-blue-300 text-sm">AI is generating files in real-time...</span>
                </div>
              </div>
            )}

            {/* Editor Content */}
            <div className="flex-1">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                    <span className="text-gray-400">Loading file...</span>
                  </div>
                </div>
              ) : (
                <Editor
                  height="100%"
                  language={getLanguage(selectedFile)}
                  value={isLiveMode && currentlyGenerating === selectedFile ? liveStreamContent : fileContent}
                  onChange={(value) => !isLiveMode && setFileContent(value || '')}
                  theme="vs-dark"
                  onMount={(editor) => {
                    editorRef.current = editor;
                  }}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 12,
                    wordWrap: 'on',
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    renderWhitespace: 'selection',
                    tabSize: 4,
                    insertSpaces: true,
                    readOnly: isLiveMode && currentlyGenerating === selectedFile,
                    cursorStyle: isLiveMode && currentlyGenerating === selectedFile ? 'block-outline' : 'line'
                  }}
                />
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Select a file to edit</p>
              <p className="text-sm mt-2">Choose a file from the tree on the left</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileEditor;