import React, { useState } from 'react';
import { Wand2, Loader2, CheckCircle, AlertCircle, FileText, Clock } from 'lucide-react';
import { apiService } from '../../services/api';
import { GenerationResponse } from '../../types/api';
import Toast from '../ui/Toast';

interface AIGeneratorProps {
  projectId: string;
  onGenerationComplete?: () => void;
}

interface GenerationProgress {
  status: 'idle' | 'initializing' | 'analyzing' | 'generating' | 'completed' | 'error';
  message: string;
  progress: number;
  filesCreated: string[];
  generationData?: GenerationResponse;
}

const AIGenerator: React.FC<AIGeneratorProps> = ({ projectId, onGenerationComplete }) => {
  const [prompt, setPrompt] = useState('');
  const [progress, setProgress] = useState<GenerationProgress>({
    status: 'idle',
    message: '',
    progress: 0,
    filesCreated: []
  });
  const [useStreaming, setUseStreaming] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const examplePrompts = [
    'Create a blog application with user authentication and post management',
    'Build an e-commerce platform with product catalog and shopping cart',
    'Develop a task management system with user roles and permissions',
    'Create a social media platform with posts, comments, and likes',
    'Build a learning management system with courses and quizzes'
  ];

  const handleStreamingGeneration = async () => {
    try {
      const eventSource = apiService.createGenerationStream(projectId, prompt);
      
      // Set connection timeout
      const connectionTimeout = setTimeout(() => {
        if (eventSource.readyState === EventSource.CONNECTING) {
          console.error('SSE connection timeout');
          eventSource.close();
          handleSSEError('Connection timeout - please check your internet connection');
        }
      }, 10000); // 10 second timeout

      eventSource.onopen = () => {
        console.log('SSE connection established');
        clearTimeout(connectionTimeout);
        setRetryCount(0);
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'status':
              setProgress(prev => ({
                ...prev,
                status: data.status || 'generating',
                message: data.message,
                progress: data.progress || prev.progress
              }));
              break;
              
            case 'file_created':
              setProgress(prev => ({
                ...prev,
                filesCreated: [...prev.filesCreated, data.file],
                progress: data.progress || prev.progress
              }));
              break;
              
            case 'completed':
              setProgress({
                status: 'completed',
                message: 'Project generated successfully!',
                progress: 100,
                filesCreated: data.files?.map((f: any) => f.path) || [],
                generationData: data
              });
              eventSource.close();
              onGenerationComplete?.();
              break;
              
            case 'error':
              const errorMsg = data.message || 'Generation failed';
              setProgress(prev => ({
                ...prev,
                status: 'error',
                message: errorMsg
              }));
              handleSSEError(errorMsg);
              eventSource.close();
              break;
          }
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError);
          handleSSEError('Invalid response format from server');
          eventSource.close();
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        clearTimeout(connectionTimeout);
        
        // Determine error type and message
        let errorMessage = 'Connection error occurred';
        
        if (eventSource.readyState === EventSource.CLOSED) {
          errorMessage = 'Connection closed unexpectedly';
        } else if (eventSource.readyState === EventSource.CONNECTING) {
          errorMessage = 'Failed to connect to server';
        }
        
        // Check if we should retry
        if (retryCount < 2 && eventSource.readyState !== EventSource.OPEN) {
          console.log(`Retrying SSE connection (attempt ${retryCount + 1}/3)...`);
          setRetryCount(prev => prev + 1);
          setProgress(prev => ({
            ...prev,
            message: `Connection failed, retrying... (${retryCount + 1}/3)`
          }));
          
          // Retry after a short delay
          setTimeout(() => {
            eventSource.close();
            handleStreamingGeneration();
          }, 2000);
        } else {
          setProgress(prev => ({
            ...prev,
            status: 'error',
            message: errorMessage
          }));
          handleSSEError(errorMessage);
          eventSource.close();
        }
      };
      
    } catch (err: any) {
      console.error('Failed to create SSE connection:', err);
      handleSSEError(err.message || 'Failed to start generation');
    }
  };

  const handleSSEError = (errorMessage: string) => {
    setError(errorMessage);
    setShowToast(true);
    setProgress(prev => ({
      ...prev,
      status: 'error',
      message: errorMessage
    }));
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setError(null);
    setShowToast(false);
    setRetryCount(0);
    setProgress({
      status: 'initializing',
      message: 'Starting project generation...',
      progress: 0,
      filesCreated: []
    });

    if (useStreaming) {
      handleStreamingGeneration();
    } else {
      // Use regular generation
      try {
        setProgress(prev => ({
          ...prev,
          status: 'generating',
          message: 'Generating your project...',
          progress: 50
        }));
        
        const response = await apiService.smartGenerate(projectId, prompt);
        
        setProgress({
          status: 'completed',
          message: 'Project generated successfully!',
          progress: 100,
          filesCreated: response.files?.map(f => f.path) || [],
          generationData: response
        });
        
        onGenerationComplete?.();
      } catch (err: any) {
        setError(err.response?.data?.error || 'Generation failed');
        setProgress(prev => ({
          ...prev,
          status: 'error',
          message: 'Generation failed'
        }));
      }
    }
  };

  const getStatusIcon = () => {
    switch (progress.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'idle':
        return <Wand2 className="w-5 h-5 text-blue-400" />;
      default:
        return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (progress.status) {
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-blue-400';
    }
  };

  const isGenerating = ['initializing', 'analyzing', 'generating'].includes(progress.status);

  return (
    <div className="h-full bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">AI Project Generator</h2>
          <p className="text-gray-400">
            Describe what you want to build and I'll generate a complete Django project for you
          </p>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-200">{error}</p>
            </div>
          </div>
        )}

        {/* Prompt Input */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-3">
            Project Description
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your project in detail. For example: 'Create a blog application with user authentication, post management, comments, and a clean responsive design.'"
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={4}
            disabled={isGenerating}
          />
          
          <div className="flex items-center justify-between mt-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                disabled={isGenerating}
              />
              <span className="text-sm text-gray-300">Use real-time streaming</span>
            </label>
            
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isGenerating}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5" />
                  <span>Generate Project</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Example Prompts */}
        {progress.status === 'idle' && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Example Prompts</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {examplePrompts.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setPrompt(example)}
                  className="text-left p-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors"
                  disabled={isGenerating}
                >
                  <p className="text-sm text-gray-300">{example}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Progress */}
        {progress.status !== 'idle' && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <div className="flex items-center space-x-3 mb-4">
              {getStatusIcon()}
              <div>
                <h3 className={`font-medium ${getStatusColor()}`}>
                  {progress.status === 'completed' ? 'Generation Complete!' : 
                   progress.status === 'error' ? 'Generation Failed' : 'Generating Project...'}
                </h3>
                <p className="text-sm text-gray-400">{progress.message}</p>
              </div>
            </div>

            {/* Progress Bar */}
            {progress.status !== 'error' && (
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-400 mb-2">
                  <span>Progress</span>
                  <span>{progress.progress}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Files Created */}
            {progress.filesCreated.length > 0 && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <FileText className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-medium text-green-400">
                    Files Created ({progress.filesCreated.length})
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
                  {progress.filesCreated.map((file, index) => (
                    <div key={index} className="text-sm text-gray-300 font-mono bg-gray-700 px-2 py-1 rounded">
                      {file}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Generation Results */}
            {progress.status === 'completed' && progress.generationData && (
              <div className="mt-6 space-y-4">
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">Project Overview</h4>
                  <div className="text-sm text-gray-300 whitespace-pre-wrap">
                    {progress.generationData.message}
                  </div>
                </div>
                
                {progress.generationData.commands && progress.generationData.commands.length > 0 && (
                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="font-medium text-white mb-2">Setup Commands</h4>
                    <div className="space-y-2">
                      {progress.generationData.commands.map((command, index) => (
                        <div key={index} className="font-mono text-sm bg-gray-800 px-3 py-2 rounded">
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {progress.generationData.access_url && (
                  <div className="bg-blue-900/50 border border-blue-500 rounded-lg p-4">
                    <h4 className="font-medium text-blue-400 mb-2">Access Your Project</h4>
                    <a 
                      href={progress.generationData.access_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-300 hover:text-blue-200 underline"
                    >
                      {progress.generationData.access_url}
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast Notification */}
      {showToast && error && (
        <Toast
          message={error}
          type="error"
          duration={5000}
          onClose={() => {
            setShowToast(false);
            setError(null);
          }}
        />
      )}
    </div>
  );
};

export default AIGenerator;