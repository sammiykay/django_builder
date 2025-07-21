interface StreamingMessage {
  type: 'file_created' | 'file_updated' | 'generation_started' | 'generation_completed' | 'error';
  data: any;
}

interface FileStreamData {
  filename: string;
  content: string;
  action: 'create' | 'update' | 'delete';
  progress?: number;
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
    console.log('📨 AI Streaming message:', message);

    switch (message.type) {
      case 'file_created':
      case 'file_updated':
        this.notifyFileListeners(message.data as FileStreamData);
        break;
      
      case 'generation_started':
        this.notifyGenerationListeners(`🚀 Starting AI generation: ${message.data.description || 'Generating project files...'}`);
        this.notifyStatusListeners({ type: 'generation_started', ...message.data });
        break;
      
      case 'generation_completed':
        this.notifyGenerationListeners(`✅ Generation completed! Created ${message.data.files_count || 0} files.`);
        this.notifyStatusListeners({ type: 'generation_completed', ...message.data });
        break;
      
      case 'error':
        this.notifyGenerationListeners(`❌ Error: ${message.data.error}`);
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