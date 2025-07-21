class TerminalService {
  private ws: WebSocket | null = null;
  private projectId: string | null = null;
  private streamOutput: string = '';
  private listeners: Set<(output: string) => void> = new Set();
  private statusListeners: Set<(status: any) => void> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  connect(projectId: string) {
    if (this.projectId === projectId && this.ws?.readyState === WebSocket.OPEN) {
      // Already connected to the same project
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
    const wsUrl = `${protocol}//${backendHost}/ws/projects/${this.projectId}/container/`;

    console.log('🔌 TerminalService connecting to WebSocket:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ TerminalService WebSocket connected');
        this.reconnectAttempts = 0;
        this.addToOutput('✅ WebSocket connected - Terminal service active\n');
        this.notifyStatusListeners({ type: 'connected', connected: true });
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.ws.onclose = (event) => {
        console.log('❌ TerminalService WebSocket disconnected:', event.code, event.reason);
        this.notifyStatusListeners({ type: 'disconnected', connected: false });

        // Auto-reconnect for non-intentional closures
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ TerminalService WebSocket error:', error);
        this.addToOutput('❌ WebSocket connection error\n');
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    this.addToOutput(`⚠️ Connection lost, retrying in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})\n`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      if (this.projectId) {
        this.establishConnection();
      }
    }, delay);
  }

  private handleMessage(data: any) {
    this.notifyStatusListeners(data);

    switch (data.type) {
      case 'log':
      case 'container_output':
      case 'output':
        this.addToOutput(data.message + '\n');
        break;
      case 'container_starting':
      case 'container_started':
      case 'container_stopping':
      case 'container_stopped':
        this.addToOutput(`\n${data.message}\n`);
        break;
      case 'command_started':
        this.addToOutput(`\n$ ${data.command}\n`);
        break;
      case 'command_completed':
        if (data.output) {
          this.addToOutput(data.output + '\n');
        }
        if (data.error) {
          this.addToOutput(`Error: ${data.error}\n`);
        }
        this.addToOutput(`Exit code: ${data.exit_code}\n\n`);
        break;
      case 'error':
        this.addToOutput(`❌ Error: ${data.message}\n`);
        break;
    }
  }

  private addToOutput(message: string) {
    this.streamOutput += message;
    // Keep only last 10000 characters to prevent memory issues
    if (this.streamOutput.length > 10000) {
      this.streamOutput = this.streamOutput.slice(-8000);
    }
    this.notifyListeners();
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.streamOutput);
      } catch (error) {
        console.error('Error in terminal listener:', error);
      }
    });
  }

  private notifyStatusListeners(status: any) {
    this.statusListeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in terminal status listener:', error);
      }
    });
  }

  subscribe(callback: (output: string) => void) {
    this.listeners.add(callback);
    // Immediately provide current output
    callback(this.streamOutput);

    return () => {
      this.listeners.delete(callback);
    };
  }

  subscribeToStatus(callback: (status: any) => void) {
    this.statusListeners.add(callback);

    return () => {
      this.statusListeners.delete(callback);
    };
  }

  sendMessage(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getOutput() {
    return this.streamOutput;
  }

  clearOutput() {
    this.streamOutput = '';
    this.notifyListeners();
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

  // For cleanup when app is completely closed
  destroy() {
    this.disconnect();
    this.listeners.clear();
    this.statusListeners.clear();
    this.streamOutput = '';
  }
}

// Export singleton instance
export const terminalService = new TerminalService();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    terminalService.destroy();
  });
}