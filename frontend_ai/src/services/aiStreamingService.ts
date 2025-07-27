interface StreamingMessage {
  type: 'connected' | 'file_created' | 'file_updated' | 'file_started' | 'file_content_streaming' | 'file_completed' | 'generation_started' | 'generation_completed' | 'status_update' | 'status' | 'error';
  data?: any;
  message?: string;
  status?: string;
  progress?: number;
  filename?: string;
  content?: string;
  token?: string;
}

interface FileStreamData {
  filename: string;
  content: string;
  action: 'create' | 'update' | 'delete';
  progress?: number;
  file?: string; // Backend sends 'file' field
  content_preview?: string;
}

class AIStreamingService {
  private ws: WebSocket | null = null;
  private projectId: string | null = null;
  private fileListeners: Set<(file: FileStreamData) => void> = new Set();
  private statusListeners: Set<(status: any) => void> = new Set();
  private generationListeners: Set<(message: string) => void> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  connect(projectId: string) {
    if (this.projectId === projectId && this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.disconnect();
    this.projectId = projectId;
    this.reconnectAttempts = 0;
    this.establishConnection();
  }

  private establishConnection() {
    if (!this.projectId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const backendHost = new URL(apiBaseUrl).host;
    const wsUrl = `${protocol}//${backendHost}/ws/projects/${this.projectId}/ai_streaming/`;

    console.log('🎯 AIStreaming connecting to WebSocket:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ AI Streaming WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyStatusListeners({ type: 'connected', connected: true });
      };

      this.ws.onmessage = (event) => {
        const message: StreamingMessage = JSON.parse(event.data);
        this.handleMessage(message);
      };

      this.ws.onclose = (event) => {
        console.log('❌ AI Streaming WebSocket disconnected:', event.code, event.reason);
        this.notifyStatusListeners({ type: 'disconnected', connected: false });

        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ AI Streaming WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create AI streaming WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 5000);

    console.log(`⚠️ AI Streaming reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      if (this.projectId) {
        this.establishConnection();
      }
    }, delay);
  }

  private handleMessage(message: StreamingMessage) {
    console.log('📨 AI Streaming message:', JSON.stringify(message, null, 2));

    switch (message.type) {
      case 'connected':
        this.notifyStatusListeners({ type: 'connected', connected: true, ...message.data });
        console.log('✅ AI Streaming service connected');
        break;
        
      case 'file_created':
      case 'file_updated':
        // Transform backend format to frontend format
        const fileData: FileStreamData = {
          filename: message.data?.file || message.file || 'unknown',
          content: message.data?.content || message.content || '',
          action: message.type === 'file_created' ? 'create' : 'update',
          progress: message.data?.progress || message.progress,
          file: message.data?.file || message.file,
          content_preview: message.data?.content_preview || message.content_preview
        };
        this.notifyFileListeners(fileData);
        break;
        
      case 'file_started':
        // New file being created - bolt.new style
        this.notifyFileListeners({
          filename: message.data?.filename || message.filename || 'unknown',
          content: '',
          action: 'create',
          file: message.data?.filename || message.filename
        });
        break;
        
      case 'file_content_streaming':
        // Token-by-token content streaming - bolt.new style
        this.notifyFileListeners({
          filename: message.data?.filename || message.filename || 'unknown',
          content: message.data?.content || message.content || '',
          action: 'update',
          file: message.data?.filename || message.filename,
          token: message.data?.token || message.token
        });
        break;
        
      case 'file_completed':
        // File generation completed
        this.notifyFileListeners({
          filename: message.data?.filename || message.filename || 'unknown',
          content: message.data?.content || message.content || '',
          action: 'create',
          file: message.data?.filename || message.filename
        });
        this.notifyGenerationListeners(`✅ Completed: ${message.data?.filename || message.filename}`);
        break;
      
      case 'generation_started':
        this.notifyGenerationListeners(`🚀 Starting AI generation: ${message.data?.description || 'Generating project files...'}`);
        this.notifyStatusListeners({ type: 'generation_started', ...message.data });
        break;
      
      case 'generation_completed':
        this.notifyGenerationListeners(`✅ Generation completed! Created ${message.data?.files_count || 0} files.`);
        this.notifyStatusListeners({ type: 'generation_completed', ...message.data });
        break;
      
      case 'status_update':
        this.notifyGenerationListeners(message.data?.message || message.message || 'Status update...');
        this.notifyStatusListeners({ type: 'status_update', ...message.data });
        break;
        
      case 'status':
        this.notifyGenerationListeners(message.message || 'Status update...');
        this.notifyStatusListeners({ type: 'status', status: message.status, progress: message.progress });
        break;
      
      case 'error':
        this.notifyGenerationListeners(`❌ Error: ${message.data?.error || message.message}`);
        this.notifyStatusListeners({ type: 'error', ...message.data });
        break;
      
      default:
        console.log('Unknown AI streaming message type:', message.type);
    }
  }

  private notifyFileListeners(file: FileStreamData) {
    this.fileListeners.forEach(listener => {
      try {
        listener(file);
      } catch (error) {
        console.error('Error in AI streaming file listener:', error);
      }
    });
  }

  private notifyStatusListeners(status: any) {
    this.statusListeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in AI streaming status listener:', error);
      }
    });
  }

  private notifyGenerationListeners(message: string) {
    this.generationListeners.forEach(listener => {
      try {
        listener(message);
      } catch (error) {
        console.error('Error in AI streaming generation listener:', error);
      }
    });
  }

  // Subscribe to file changes during generation
  subscribeToFiles(callback: (file: FileStreamData) => void) {
    this.fileListeners.add(callback);
    return () => {
      this.fileListeners.delete(callback);
    };
  }

  // Subscribe to generation status
  subscribeToStatus(callback: (status: any) => void) {
    this.statusListeners.add(callback);
    return () => {
      this.statusListeners.delete(callback);
    };
  }

  // Subscribe to generation messages
  subscribeToGeneration(callback: (message: string) => void) {
    this.generationListeners.add(callback);
    return () => {
      this.generationListeners.delete(callback);
    };
  }

  // Start AI generation with streaming
  startGeneration(requirements: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'start_generation',
        requirements: requirements
      }));
      return true;
    }
    return false;
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Service disconnect');
      this.ws = null;
    }

    this.projectId = null;
    this.reconnectAttempts = 0;
  }

  destroy() {
    this.disconnect();
    this.fileListeners.clear();
    this.statusListeners.clear();
    this.generationListeners.clear();
  }
}

// Export singleton instance
export const aiStreamingService = new AIStreamingService();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    aiStreamingService.destroy();
  });
}