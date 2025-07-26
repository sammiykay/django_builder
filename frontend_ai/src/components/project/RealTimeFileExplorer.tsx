import React, { useState, useEffect } from 'react';
import { 
  Folder, 
  File, 
  Code, 
  FileText, 
  Image, 
  Settings,
  ChevronDown,
  ChevronRight,
  Eye,
  Edit,
  Sparkles
} from 'lucide-react';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  size?: number;
  modified?: string;
  isAiGenerated?: boolean;
  isNew?: boolean;
}

interface RealTimeFileExplorerProps {
  projectId: string;
  filesCreated: string[];
  currentFile?: string;
  onFileSelect?: (file: FileNode) => void;
}

const RealTimeFileExplorer: React.FC<RealTimeFileExplorerProps> = ({
  projectId,
  filesCreated,
  currentFile,
  onFileSelect
}) => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['']));
  const [selectedFile, setSelectedFile] = useState<string>('');

  // Convert flat file list to tree structure
  const buildFileTree = (files: string[]): FileNode[] => {
    const root: { [key: string]: FileNode } = {};
    
    files.forEach(filePath => {
      const parts = filePath.split('/');
      let current = root;
      let currentPath = '';
      
      parts.forEach((part, index) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!current[part]) {
          current[part] = {
            name: part,
            path: currentPath,
            type: index === parts.length - 1 ? 'file' : 'folder',
            children: index === parts.length - 1 ? undefined : [],
            isAiGenerated: true,
            isNew: filesCreated.includes(filePath)
          };
        }
        
        if (current[part].children) {
          if (!current[part].children.find(child => child.name === parts[index + 1])) {
            current = current[part].children.reduce((acc, child) => {
              acc[child.name] = child;
              return acc;
            }, {} as { [key: string]: FileNode });
          } else {
            current = current[part].children.reduce((acc, child) => {
              acc[child.name] = child;
              return acc;
            }, {} as { [key: string]: FileNode });
          }
        }
      });
    });
    
    return Object.values(root);
  };

  useEffect(() => {
    const tree = buildFileTree(filesCreated);
    setFileTree(tree);
  }, [filesCreated]);

  const getFileIcon = (fileName: string, isFolder: boolean) => {
    if (isFolder) {
      return <Folder className="w-4 h-4 text-blue-400" />;
    }
    
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'py':
        return <Code className="w-4 h-4 text-green-400" />;
      case 'html':
        return <Code className="w-4 h-4 text-orange-400" />;
      case 'css':
        return <Code className="w-4 h-4 text-purple-400" />;
      case 'js':
        return <Code className="w-4 h-4 text-yellow-400" />;
      case 'json':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'txt':
      case 'md':
        return <FileText className="w-4 h-4 text-gray-400" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
        return <Image className="w-4 h-4 text-pink-400" />;
      case 'yml':
      case 'yaml':
        return <Settings className="w-4 h-4 text-indigo-400" />;
      default:
        return <File className="w-4 h-4 text-gray-400" />;
    }
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const handleFileClick = (file: FileNode) => {
    if (file.type === 'file') {
      setSelectedFile(file.path);
      onFileSelect?.(file);
    } else {
      toggleFolder(file.path);
    }
  };

  const renderFileNode = (node: FileNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    const isCurrent = currentFile === node.path;
    
    return (
      <div key={node.path}>
        <div
          className={`flex items-center space-x-2 px-2 py-1 rounded cursor-pointer transition-all duration-200 ${
            isSelected 
              ? 'bg-blue-600 text-white' 
              : isCurrent
              ? 'bg-blue-800 text-blue-200 border border-blue-600'
              : 'hover:bg-gray-700 text-gray-300'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => handleFileClick(node)}
        >
          {node.type === 'folder' && (
            isExpanded ? 
              <ChevronDown className="w-4 h-4" /> : 
              <ChevronRight className="w-4 h-4" />
          )}
          
          {getFileIcon(node.name, node.type === 'folder')}
          
          <span className="flex-1 truncate text-sm">{node.name}</span>
          
          {node.isAiGenerated && (
            <Sparkles className="w-3 h-3 text-purple-400" title="AI Generated" />
          )}
          
          {node.isNew && (
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Recently created" />
          )}
          
          {isCurrent && (
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" title="Currently processing" />
          )}
          
          {node.type === 'file' && (
            <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Eye className="w-3 h-3 text-gray-400 hover:text-white cursor-pointer" title="View" />
              <Edit className="w-3 h-3 text-gray-400 hover:text-white cursor-pointer" title="Edit" />
            </div>
          )}
        </div>
        
        {node.type === 'folder' && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderFileNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const getFileStats = () => {
    const totalFiles = filesCreated.length;
    const pythonFiles = filesCreated.filter(f => f.endsWith('.py')).length;
    const templateFiles = filesCreated.filter(f => f.endsWith('.html')).length;
    const configFiles = filesCreated.filter(f => f.includes('requirements') || f.includes('settings')).length;
    
    return { totalFiles, pythonFiles, templateFiles, configFiles };
  };

  const stats = getFileStats();

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-2">Project Files</h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-800 p-2 rounded">
            <span className="text-gray-400">Total</span>
            <div className="text-white font-semibold">{stats.totalFiles}</div>
          </div>
          <div className="bg-gray-800 p-2 rounded">
            <span className="text-gray-400">Python</span>
            <div className="text-green-400 font-semibold">{stats.pythonFiles}</div>
          </div>
          <div className="bg-gray-800 p-2 rounded">
            <span className="text-gray-400">Templates</span>
            <div className="text-orange-400 font-semibold">{stats.templateFiles}</div>
          </div>
          <div className="bg-gray-800 p-2 rounded">
            <span className="text-gray-400">Config</span>
            <div className="text-blue-400 font-semibold">{stats.configFiles}</div>
          </div>
        </div>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {fileTree.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <File className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No files generated yet</p>
          </div>
        ) : (
          <div className="space-y-1 group">
            {fileTree.map(node => renderFileNode(node))}
          </div>
        )}
      </div>

      {/* Current File Indicator */}
      {currentFile && (
        <div className="p-3 border-t border-gray-700 bg-gray-800">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-blue-400">Processing:</span>
          </div>
          <div className="text-xs text-gray-300 font-mono mt-1 truncate">
            {currentFile}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeFileExplorer;