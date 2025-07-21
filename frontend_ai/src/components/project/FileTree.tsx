import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Folder, File, FileText, Code, Search } from 'lucide-react';
import { apiService } from '../../services/api';
import Input from '../ui/Input';
import Badge from '../ui/Badge';
import '../../styles/design-system.css';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface FileTreeProps {
  projectId: string;
  onFileSelect: (filePath: string) => void;
  selectedFile?: string;
}

const FileTree: React.FC<FileTreeProps> = ({ projectId, onFileSelect, selectedFile }) => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [filteredTree, setFilteredTree] = useState<FileNode[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadFileTree();
  }, [projectId]);

  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = filterTree(fileTree, searchQuery.toLowerCase());
      setFilteredTree(filtered);
      // Auto-expand all folders when searching
      const allPaths = new Set<string>();
      getAllPaths(filtered, allPaths);
      setExpandedFolders(allPaths);
    } else {
      setFilteredTree(fileTree);
    }
  }, [searchQuery, fileTree]);

  const buildTreeFromFiles = (files: any[]): FileNode[] => {
    const nodeMap = new Map<string, FileNode>();
    
    // First, create all nodes
    files.forEach(file => {
      if (!file.path) return;
      
      // Normalize path separators to forward slashes
      const normalizedPath = file.path.replace(/\\/g, '/');
      const pathParts = normalizedPath.split('/').filter(part => part.length > 0);
      let currentPath = '';
      
      // Create each part of the path
      pathParts.forEach((part, index) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!nodeMap.has(currentPath)) {
          const isFile = index === pathParts.length - 1;
          const node: FileNode = {
            name: part,
            path: currentPath,
            type: isFile ? 'file' : 'directory',
            children: isFile ? undefined : []
          };
          nodeMap.set(currentPath, node);
        }
      });
    });

    // Build the tree structure
    const rootNodes: FileNode[] = [];
    
    nodeMap.forEach((node, path) => {
      const pathParts = path.split('/');
      if (pathParts.length === 1) {
        // Root level
        rootNodes.push(node);
      } else {
        // Find parent and add as child
        const parentPath = pathParts.slice(0, -1).join('/');
        const parent = nodeMap.get(parentPath);
        if (parent && parent.children) {
          parent.children.push(node);
        }
      }
    });

    // Sort: directories first, then files
    const sortNodes = (nodes: FileNode[]) => {
      nodes.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
      
      nodes.forEach(node => {
        if (node.children) {
          sortNodes(node.children);
        }
      });
    };

    sortNodes(rootNodes);
    return rootNodes;
  };

  const filterTree = (nodes: FileNode[], query: string): FileNode[] => {
    return nodes.reduce<FileNode[]>((acc, node) => {
      if (node.name.toLowerCase().includes(query)) {
        acc.push(node);
      } else if (node.children) {
        const filteredChildren = filterTree(node.children, query);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
        }
      }
      return acc;
    }, []);
  };

  const getAllPaths = (nodes: FileNode[], paths: Set<string>) => {
    nodes.forEach(node => {
      if (node.type === 'directory') {
        paths.add(node.path);
        if (node.children) {
          getAllPaths(node.children, paths);
        }
      }
    });
  };

  const loadFileTree = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getFilesystemFiles(projectId);
      const files = response || [];
      
      const tree = buildTreeFromFiles(files);
      setFileTree(tree);
      setFilteredTree(tree);
      
      // Start with all folders collapsed
      setExpandedFolders(new Set());
    } catch (error) {
      console.error('Failed to load file tree:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath);
      } else {
        newSet.add(folderPath);
      }
      return newSet;
    });
  };

  const getFileIcon = (fileName: string, type: string) => {
    if (type === 'directory') {
      return <Folder className="w-4 h-4 text-blue-400" />;
    }
    
    if (!fileName) {
      return <File className="w-4 h-4 text-gray-400" />;
    }
    
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return <Code className="w-4 h-4 text-blue-300" />;
      case 'html':
      case 'htm':
        return <Code className="w-4 h-4 text-orange-400" />;
      case 'css':
        return <Code className="w-4 h-4 text-blue-400" />;
      case 'js':
      case 'jsx':
        return <Code className="w-4 h-4 text-yellow-400" />;
      case 'ts':
      case 'tsx':
        return <Code className="w-4 h-4 text-blue-500" />;
      case 'json':
        return <FileText className="w-4 h-4 text-yellow-300" />;
      case 'md':
        return <FileText className="w-4 h-4 text-blue-300" />;
      case 'txt':
        return <FileText className="w-4 h-4 text-gray-300" />;
      default:
        return <File className="w-4 h-4 text-gray-400" />;
    }
  };

  const renderFileNode = (node: FileNode, depth: number = 0): React.ReactNode => {
    if (!node) return null;
    
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    
    return (
      <div key={node.path}>
        {/* Node itself */}
        <div
          className={`
            flex items-center py-2 px-3 rounded-md cursor-pointer transition-all group
            ${isSelected 
              ? 'bg-primary-600/20 border-l-2 border-primary-500 text-primary' 
              : 'hover:bg-tertiary/30 text-secondary hover:text-primary'
            }
          `}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
          onClick={() => {
            if (node.type === 'directory') {
              toggleFolder(node.path);
            } else {
              onFileSelect(node.path);
            }
          }}
        >
          {/* Chevron for directories */}
          {node.type === 'directory' ? (
            <div className="mr-2 flex-shrink-0">
              {isExpanded ? (
                <ChevronDown className="w-3 h-3 text-tertiary group-hover:text-secondary transition-colors" />
              ) : (
                <ChevronRight className="w-3 h-3 text-tertiary group-hover:text-secondary transition-colors" />
              )}
            </div>
          ) : (
            <div className="w-5 mr-2" />
          )}
          
          {/* Icon */}
          <div className="mr-2 flex-shrink-0">
            {getFileIcon(node.name, node.type)}
          </div>
          
          {/* Name */}
          <span className="text-sm font-medium truncate">
            {node.name}
          </span>
          
          {/* File count for directories */}
          {node.type === 'directory' && node.children && (
            <Badge variant="neutral" size="sm" className="ml-auto">
              {node.children.length}
            </Badge>
          )}
        </div>
        
        {/* Children (only show if directory is expanded) */}
        {node.type === 'directory' && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderFileNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <div className="text-gray-400">Loading files...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-secondary border-r border-secondary">
      {/* Header */}
      <div className="px-3 sm:px-4 py-3 border-b border-secondary">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-primary">Explorer</h3>
          {filteredTree.length > 0 && (
            <Badge variant="neutral" size="sm">
              {filteredTree.length}
            </Badge>
          )}
        </div>
        
        {/* Search */}
        <Input
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          icon={<Search className="w-4 h-4" />}
          iconPosition="left"
          className="text-sm"
        />
      </div>
      
      {/* File Tree */}
      <div className="flex-1 overflow-y-auto py-2">
        {Array.isArray(filteredTree) && filteredTree.length > 0 ? (
          <div className="space-y-1 px-1 sm:px-2">
            {filteredTree.filter(node => node && node.path).map(node => renderFileNode(node))}
          </div>
        ) : searchQuery.trim() ? (
          <div className="p-6 text-center">
            <Search className="w-8 h-8 text-tertiary mx-auto mb-2" />
            <p className="text-sm text-secondary mb-1">No files found</p>
            <p className="text-xs text-tertiary">Try a different search term</p>
          </div>
        ) : (
          <div className="p-6 text-center">
            <FileText className="w-8 h-8 text-tertiary mx-auto mb-2" />
            <p className="text-sm text-secondary mb-1">No files found</p>
            <p className="text-xs text-tertiary">This project appears to be empty</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileTree;