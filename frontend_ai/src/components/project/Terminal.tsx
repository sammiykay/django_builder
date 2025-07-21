import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, Send, Loader2, Clock, AlertCircle, Play, Square, Wifi, WifiOff } from 'lucide-react';
import { apiService } from '../../services/api';
import { CommandExecution } from '../../types/api';
import { terminalService } from '../../services/terminalService';
import Toast from '../ui/Toast';

interface TerminalProps {
  projectId: string;
  isProjectRunning?: boolean;
  onContainerStatusChange?: (isRunning: boolean) => void;
}

const Terminal: React.FC<TerminalProps> = ({ projectId, isProjectRunning = false, onContainerStatusChange }) => {
  const [history, setHistory] = useState<CommandExecution[]>([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [streamOutput, setStreamOutput] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [containerRunning, setContainerRunning] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<HTMLDivElement>(null);

  const commonCommands = [
    'python manage.py migrate',
    'python manage.py runserver',
    'python manage.py createsuperuser',
    'python manage.py collectstatic',
    'python manage.py makemigrations',
    'pip install -r requirements.txt',
    'python manage.py shell',
    'python manage.py test'
  ];

  useEffect(() => {
    console.log('📜 streamOutput changed, length:', streamOutput.length);
    
    // Dispatch terminal activity event for background notifications
    if (streamOutput.trim()) {
      window.dispatchEvent(new CustomEvent('terminal-activity', {
        detail: {
          output: streamOutput,
          type: 'stream'
        }
      }));
    }
    
    // Use setTimeout to ensure DOM has updated before scrolling
    const scrollTimer = setTimeout(() => {
      scrollToBottom();
    }, 10);
    
    return () => clearTimeout(scrollTimer);
  }, [streamOutput]); // Only scroll when streamOutput changes

  useEffect(() => {
    loadCommandHistory();
    
    // Connect to terminal service
    terminalService.connect(projectId);
    
    // Subscribe to output updates
    const unsubscribeOutput = terminalService.subscribe((output) => {
      setStreamOutput(output);
    });
    
    // Subscribe to status updates
    const unsubscribeStatus = terminalService.subscribeToStatus((status) => {
      handleServiceMessage(status);
    });
    
    // Set initial connection state
    setWsConnected(terminalService.isConnected());
    setStreamOutput(terminalService.getOutput());
    
    return () => {
      unsubscribeOutput();
      unsubscribeStatus();
      // Don't disconnect the service - let it persist
    };
  }, [projectId]);

  // Synchronize container running state with project state
  useEffect(() => {
    setContainerRunning(isProjectRunning);
  }, [isProjectRunning]);

  const startContainer = () => {
    if (terminalService.isConnected()) {
      setIsStreaming(true);
      
      const success = terminalService.sendMessage({
        type: 'start_container',
        port: 8001
      });
      
      if (!success) {
        setError('Failed to send start command. WebSocket not connected.');
        setShowToast(true);
      } else {
        // Optimistically update container status
        setContainerRunning(true);
        onContainerStatusChange?.(true);
      }
      
      console.log('📤 Sent start_container message via TerminalService');
    } else {
      setError('WebSocket not connected. Please refresh the page.');
      setShowToast(true);
      console.error('❌ WebSocket not connected, cannot start container');
    }
  };

  const stopContainer = () => {
    if (terminalService.isConnected()) {
      const success = terminalService.sendMessage({
        type: 'stop_container'
      });
      
      if (!success) {
        setError('Failed to send stop command. WebSocket not connected.');
        setShowToast(true);
      } else {
        // Optimistically update container status
        setContainerRunning(false);
        setIsStreaming(false);
        onContainerStatusChange?.(false);
      }
    } else {
      setError('WebSocket not connected');
      setShowToast(true);
    }
  };

  // Listen for container control events from navbar
  useEffect(() => {
    const handleProjectStart = (event: CustomEvent) => {
      if (event.detail.projectId === projectId) {
        startContainer();
      }
    };

    const handleProjectStop = (event: CustomEvent) => {
      if (event.detail.projectId === projectId) {
        stopContainer();
      }
    };

    window.addEventListener('project-container-start', handleProjectStart as EventListener);
    window.addEventListener('project-container-stop', handleProjectStop as EventListener);

    return () => {
      window.removeEventListener('project-container-start', handleProjectStart as EventListener);
      window.removeEventListener('project-container-stop', handleProjectStop as EventListener);
    };
  }, [projectId]);

  const handleServiceMessage = (data: any) => {
    switch (data.type) {
      case 'connected':
        setWsConnected(true);
        setError(null);
        setShowToast(false);
        break;
        
      case 'disconnected':
        setWsConnected(false);
        break;
        
      case 'connection_established':
        console.log('Container WebSocket established:', data.message);
        break;
        
      case 'container_starting':
        setIsStreaming(true);
        break;
        
      case 'container_started':
        setContainerRunning(true);
        setIsStreaming(true);
        onContainerStatusChange?.(true);
        
        // Dispatch container status event for non-polling updates
        window.dispatchEvent(new CustomEvent('container-status-update', {
          detail: {
            status: 'running',
            isRunning: true,
            port: data.port,
            containerId: data.container_id
          }
        }));
        break;
        
      case 'container_stopping':
        window.dispatchEvent(new CustomEvent('container-status-update', {
          detail: {
            status: 'stopping',
            isRunning: false
          }
        }));
        break;
        
      case 'container_stopped':
        setContainerRunning(false);
        setIsStreaming(false);
        onContainerStatusChange?.(false);
        
        // Dispatch container status event
        window.dispatchEvent(new CustomEvent('container-status-update', {
          detail: {
            status: 'stopped',
            isRunning: false,
            port: null,
            containerId: null
          }
        }));
        break;
        
      case 'command_started':
        setIsExecuting(true);
        break;
        
      case 'command_completed':
        setIsExecuting(false);
        break;
        
      case 'error':
        setError(data.message);
        setShowToast(true);
        setIsExecuting(false);
        setIsStreaming(false);
        break;
    }
  };

  const loadCommandHistory = async () => {
    try {
      setIsLoadingHistory(true);
      setError(null);
      const commands = await apiService.getCommandHistory(projectId);
      setHistory(commands);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load command history');
      setShowToast(true);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const scrollToBottom = () => {
    // Force scroll to bottom using multiple methods for reliability
    requestAnimationFrame(() => {
      // Scroll the main terminal container
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
      
      // Scroll the live stream container specifically (most important)
      if (streamRef.current) {
        streamRef.current.scrollTop = streamRef.current.scrollHeight;
        // Force scroll with smooth behavior as backup
        streamRef.current.scrollIntoView({ 
          behavior: 'instant',
          block: 'end'
        });
      }
    });
  };

  const executeCommand = async () => {
    if (!currentCommand.trim() || isExecuting) return;

    const command = currentCommand.trim();
    setCurrentCommand('');

    // If WebSocket is connected and container is running, use WebSocket for real-time execution
    if (terminalService.isConnected() && containerRunning) {
      const success = terminalService.sendMessage({
        type: 'execute_command',
        command: command
      });
      
      if (success) {
        return;
      }
    }

    // Fallback to REST API
    setIsExecuting(true);
    setError(null);

    // Add command to history immediately
    const tempCommand: CommandExecution = {
      id: Date.now(),
      command,
      output: '',
      error_output: '',
      exit_code: 0,
      execution_time: 0,
      executed_at: new Date().toISOString()
    };

    setHistory(prev => [...prev, tempCommand]);

    try {
      const result = await apiService.executeCommand(projectId, command);
      
      // Update the command in history with real results
      setHistory(prev => 
        prev.map(cmd => 
          cmd.id === tempCommand.id 
            ? {
                ...cmd,
                output: result.output,
                error_output: result.error,
                exit_code: result.exit_code,
                execution_time: 0 // API doesn't return execution time in this format
              }
            : cmd
        )
      );
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to execute command');
      setShowToast(true);
      
      // Update the command with error
      setHistory(prev => 
        prev.map(cmd => 
          cmd.id === tempCommand.id 
            ? {
                ...cmd,
                output: '',
                error_output: err.response?.data?.error || 'Command execution failed',
                exit_code: 1,
                execution_time: 0
              }
            : cmd
        )
      );
    } finally {
      setIsExecuting(false);
    }
  };

  const clearStreamOutput = () => {
    console.log('🧹 Clearing stream output');
    terminalService.clearOutput();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeCommand();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-gray-400">Loading terminal...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Terminal Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <TerminalIcon className="w-5 h-5 text-green-400" />
          <span className="text-white font-medium">Terminal</span>
          <span className="text-xs text-gray-400">Project: {projectId.slice(0, 8)}...</span>
          
          {/* WebSocket Status */}
          <div className="flex items-center space-x-1">
            {wsConnected ? (
              <Wifi className="w-4 h-4 text-green-400" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-400" />
            )}
            <span className={`text-xs ${wsConnected ? 'text-green-400' : 'text-red-400'}`}>
              {wsConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* Container Status */}
          {containerRunning && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-400">Container Running</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Container Controls */}
          {!containerRunning ? (
            <button
              onClick={startContainer}
              disabled={!wsConnected || isStreaming}
              className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded text-sm transition-colors flex items-center space-x-1"
            >
              <Play className="w-3 h-3" />
              <span>Start Server</span>
            </button>
          ) : (
            <button
              onClick={stopContainer}
              disabled={!wsConnected}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded text-sm transition-colors flex items-center space-x-1"
            >
              <Square className="w-3 h-3" />
              <span>Stop Server</span>
            </button>
          )}
          
          <button
            onClick={clearStreamOutput}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm transition-colors"
          >
            Clear Stream
          </button>
          
          <button
            onClick={loadCommandHistory}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm transition-colors"
          >
            Refresh
          </button>
          
          <button
            onClick={() => setHistory([])}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm transition-colors"
          >
            Clear History
          </button>
        </div>
      </div>


      {/* Terminal Output */}
      <div 
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm bg-black"
      >
        {/* Welcome Message */}
        {history.length === 0 && !streamOutput && !isLoadingHistory && (
          <div className="text-gray-500 mb-4">
            <p>🚀 Welcome to the Django Project Terminal</p>
            <p>• Start the server to see live logs</p>
            <p>• Use quick commands or type your own</p>
            <p>• All terminal output will stream here in real-time</p>
          </div>
        )}

        {/* Streaming Status - Make it more prominent */}
        {(isStreaming || containerRunning) && (
          <div className="flex items-center space-x-2 text-green-400 text-sm mb-4 bg-green-900/20 border border-green-500/30 rounded-lg p-3">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="font-medium">
              {isStreaming ? '🔴 LIVE STREAMING' : containerRunning ? '🟢 CONTAINER RUNNING - READY FOR LOGS' : 'Streaming live output...'}
            </span>
            <div className="text-xs text-green-300">
              ({streamOutput.split('\n').length} lines)
            </div>
          </div>
        )}

        {/* Live Stream Output - Make it the primary content */}
        {streamOutput && (
          <div className="mb-6">
            <div className="text-green-400 text-sm mb-3 font-medium flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>📺 LIVE CONTAINER OUTPUT</span>
              <span className="text-xs text-gray-400">({streamOutput.length} chars)</span>
            </div>
            <div 
              ref={streamRef}
              className="text-gray-300 whitespace-pre-wrap bg-black/50 rounded-lg p-4 border border-gray-700 max-h-96 overflow-y-auto"
            >
              {streamOutput}
            </div>
          </div>
        )}

        
        {/* Current executing command */}
        {isExecuting && (
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-green-400">$</span>
              <span className="text-white">{history[history.length - 1]?.command}</span>
            </div>
            <div className="flex items-center space-x-2 text-gray-400 ml-4">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Executing...</span>
            </div>
          </div>
        )}

      </div>

      {/* Quick Commands */}
      <div className="bg-gray-800 border-t border-gray-700 p-4">
        <div className="mb-3">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Quick Commands</h4>
          <div className="flex flex-wrap gap-2">
            {commonCommands.map((cmd, index) => (
              <button
                key={index}
                onClick={() => setCurrentCommand(cmd)}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs transition-colors"
                disabled={isExecuting}
              >
                {cmd}
              </button>
            ))}
          </div>
        </div>

        {/* Command Input */}
        <div className="flex space-x-3">
          <div className="flex-1 flex items-center bg-black rounded-lg px-3 py-2">
            <span className="text-green-400 font-mono mr-2">$</span>
            <input
              type="text"
              value={currentCommand}
              onChange={(e) => setCurrentCommand(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter command..."
              className="flex-1 bg-transparent text-white font-mono outline-none"
              disabled={isExecuting}
            />
          </div>
          <button
            onClick={executeCommand}
            disabled={!currentCommand.trim() || isExecuting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            {isExecuting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Toast Notification */}
      {showToast && error && (
        <Toast
          message={error}
          type="error"
          duration={4000}
          onClose={() => {
            setShowToast(false);
            setError(null);
          }}
        />
      )}
    </div>
  );
};

export default Terminal;