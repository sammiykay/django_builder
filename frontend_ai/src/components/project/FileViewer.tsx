import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FileText, Download, Copy, Check, AlertCircle, Loader2, Edit3, Save, X } from 'lucide-react';
import { apiService } from '../../services/api';
import CodeEditor from './CodeEditor';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Card from '../ui/Card';
import { getLanguageFromFileName, isEditableFile } from '../../utils/languageDetection';
import '../../styles/design-system.css';

interface FileViewerProps {
  projectId: string;
  filePath: string | null;
  showHeader?: boolean;
  showFooter?: boolean;
  forceEditMode?: boolean;
  onEditModeChange?: (isEditing: boolean) => void;
  onUnsavedChanges?: (hasChanges: boolean) => void;
  onSaving?: (isSaving: boolean) => void;
  liveContent?: string;
  isStreaming?: boolean;
}

const FileViewer: React.FC<FileViewerProps> = ({ 
  projectId, 
  filePath, 
  showHeader = true, 
  showFooter = true, 
  forceEditMode = false,
  onEditModeChange,
  onUnsavedChanges,
  onSaving,
  liveContent,
  isStreaming = false
}) => {
  const [fileContent, setFileContent] = useState<string>('');
  const [displayContent, setDisplayContent] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const prevEditingRef = useRef(isEditing);

  useEffect(() => {
    if (filePath) {
      loadFileContent();
    } else {
      setFileContent('');
      setEditedContent('');
      setError(null);
      setIsEditing(false);
      setHasUnsavedChanges(false);
    }
  }, [filePath, projectId]);

  const fileName = filePath?.split('/').pop() || '';
  const language = getLanguageFromFileName(fileName);
  const canEdit = isEditableFile(fileName) || forceEditMode; // Allow editing if forced

  // Handle external edit mode control
  useEffect(() => {
    if (forceEditMode !== undefined && isEditing !== forceEditMode) {
      console.log('FileViewer: Forcing edit mode to:', forceEditMode, 'for file:', filePath);
      setIsEditing(forceEditMode);
    }
  }, [forceEditMode, filePath, isEditing]);

  // Notify parent of edit mode changes
  useEffect(() => {
    if (onEditModeChange && prevEditingRef.current !== isEditing) {
      onEditModeChange(isEditing);
      prevEditingRef.current = isEditing;
    }
  }, [isEditing, onEditModeChange]);

  // Handle live content updates
  useEffect(() => {
    if (liveContent !== undefined) {
      setDisplayContent(liveContent);
      // If we're streaming to this file, show the live content
      if (isStreaming) {
        setFileContent(liveContent);
        setEditedContent(liveContent);
      }
    } else {
      setDisplayContent(fileContent);
    }
  }, [liveContent, isStreaming, fileContent]);

  // Listen for live file content updates
  useEffect(() => {
    const handleLiveContentUpdate = (event: CustomEvent) => {
      const { filename, content, token, isStreaming: streaming } = event.detail;
      
      if (filename === filePath) {
        console.log('📝 FileViewer received live content update:', { filename, contentLength: content?.length || 0, streaming });
        
        if (streaming) {
          // Update content in real-time for streaming
          setDisplayContent(content);
          setFileContent(content);
          setEditedContent(content);
        }
      }
    };

    window.addEventListener('liveFileContentUpdate', handleLiveContentUpdate);
    return () => window.removeEventListener('liveFileContentUpdate', handleLiveContentUpdate);
  }, [filePath]);


  useEffect(() => {
    const hasChanges = fileContent !== editedContent && editedContent !== '';
    setHasUnsavedChanges(hasChanges);
    if (onUnsavedChanges) {
      onUnsavedChanges(hasChanges);
    }
  }, [fileContent, editedContent, onUnsavedChanges]);

  const loadFileContent = async () => {
    if (!filePath) return;
    
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiService.getFileContent(projectId, filePath);
      const content = response.content || '';
      setFileContent(content);
      setEditedContent(content);
      setDisplayContent(content);
      setIsEditing(false);
      setHasUnsavedChanges(false);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load file content');
      setFileContent('');
      setEditedContent('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = useCallback(async () => {
    if (!filePath || !hasUnsavedChanges) return;
    
    try {
      setIsSaving(true);
      if (onSaving) {
        onSaving(true);
      }
      await apiService.saveFile(projectId, filePath, editedContent);
      setFileContent(editedContent);
      setHasUnsavedChanges(false);
      if (onUnsavedChanges) {
        onUnsavedChanges(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save file');
    } finally {
      setIsSaving(false);
      if (onSaving) {
        onSaving(false);
      }
    }
  }, [filePath, hasUnsavedChanges, projectId, editedContent, onSaving, onUnsavedChanges]);

  // Listen for save-file custom event from dropdown
  useEffect(() => {
    const handleSaveEvent = (event: any) => {
      if (event.detail && event.detail.filePath === filePath) {
        handleSave();
      }
    };

    window.addEventListener('save-file', handleSaveEvent);
    return () => {
      window.removeEventListener('save-file', handleSaveEvent);
    };
  }, [filePath, handleSave]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedContent(fileContent);
    setIsEditing(false);
    setHasUnsavedChanges(false);
  };

  const handleCopyContent = async () => {
    try {
      await navigator.clipboard.writeText(fileContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  const handleDownload = () => {
    if (!filePath || !fileContent) return;
    
    const blob = new Blob([fileContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filePath.split('/').pop() || 'file.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!filePath) {
    return (
      <div className="h-full flex items-center justify-center bg-primary p-6">
        <Card className="text-center max-w-sm mx-auto" elevated>
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-primary mb-2">No File Selected</h3>
              <p className="text-secondary text-sm leading-relaxed">
                Choose a file from the explorer to view or edit its contents
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-primary p-6">
        <Card className="text-center">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-secondary">Loading file content...</span>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-primary p-6">
        <Card className="text-center max-w-md mx-auto">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="w-12 h-12 text-red-500" />
            <div>
              <h3 className="text-lg font-semibold text-primary mb-2">Error Loading File</h3>
              <p className="text-secondary text-sm mb-4">{error}</p>
            </div>
            <Button onClick={loadFileContent} variant="primary">
              Retry
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-primary">
      {/* Header */}
      {showHeader && (
        <div className="flex items-center justify-between p-3 sm:p-4 border-b border-secondary bg-secondary shadow-sm">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-blue-500" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-primary truncate">
                  {filePath.split('/').pop()}
                </h3>
                <div className="flex items-center gap-1 flex-wrap">
                  {isEditing && (
                    <Badge variant="success" size="sm">
                      Editing
                    </Badge>
                  )}
                  {!canEdit && (
                    <Badge variant="neutral" size="sm">
                      Read-only
                    </Badge>
                  )}
                  {hasUnsavedChanges && (
                    <Badge variant="warning" size="sm">
                      Unsaved
                    </Badge>
                  )}
                </div>
              </div>
              <p className="text-xs text-tertiary font-mono truncate hidden sm:block">{filePath}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
            {isEditing ? (
              <>
                <Button
                  onClick={handleSave}
                  disabled={!hasUnsavedChanges || isSaving}
                  loading={isSaving}
                  variant="primary"
                  size="sm"
                  icon={!isSaving ? <Save className="w-4 h-4" /> : undefined}
                >
                  <span className="hidden sm:inline">Save</span>
                </Button>
                
                <Button
                  onClick={handleCancelEdit}
                  variant="secondary"
                  size="sm"
                  icon={<X className="w-4 h-4" />}
                >
                  <span className="hidden sm:inline">Cancel</span>
                </Button>
              </>
            ) : canEdit ? (
              <Button
                onClick={handleEdit}
                variant="secondary"
                size="sm"
                icon={<Edit3 className="w-4 h-4" />}
              >
                <span className="hidden sm:inline">Edit</span>
              </Button>
            ) : (
              <Badge variant="neutral" size="sm">
                <span className="hidden sm:inline">View Only</span>
                <span className="sm:hidden">RO</span>
              </Badge>
            )}
            
            <Button
              onClick={handleCopyContent}
              variant="ghost"
              size="sm"
              icon={copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
              className="hidden sm:flex"
            >
              {copied ? 'Copied' : 'Copy'}
            </Button>
            
            <Button
              onClick={handleDownload}
              variant="ghost"
              size="sm"
              icon={<Download className="w-4 h-4" />}
              className="hidden sm:flex"
            >
              Download
            </Button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-h-0">
        <CodeEditor
          value={isEditing ? editedContent : (isStreaming && liveContent !== undefined ? displayContent : fileContent)}
          onChange={isEditing ? setEditedContent : () => {}}
          language={language}
          fileName={fileName}
          readOnly={!(canEdit || forceEditMode) || !isEditing}
          onSave={handleSave}
        />
        {/* Debug info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="text-xs text-gray-500 p-2 border-t border-gray-700">
            Debug: canEdit={canEdit.toString()}, isEditing={isEditing.toString()}, readOnly={(!canEdit || !isEditing).toString()}, fileName={fileName}
          </div>
        )}
      </div>
      
      {/* Footer */}
      {showFooter && (
        <div className="px-3 sm:px-4 py-2 border-t border-secondary bg-secondary/50 flex-shrink-0">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 sm:gap-4">
              <span className="text-tertiary">
                {fileContent.split('\n').length} lines
              </span>
              <span className="text-tertiary hidden sm:inline">
                {fileContent.length} characters
              </span>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <Badge variant="neutral" size="sm">
                {language}
              </Badge>
              {!canEdit && (
                <Badge variant="neutral" size="sm" className="hidden sm:flex">
                  Read-only
                </Badge>
              )}
              {isStreaming && (
                <Badge variant="neutral" size="sm" className="bg-blue-600/20 text-blue-400 border-blue-500/30 animate-pulse">
                  Streaming...
                </Badge>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileViewer;