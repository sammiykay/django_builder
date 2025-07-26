import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  AuthResponse, 
  Project, 
  CreateProjectRequest, 
  ProjectFile, 
  ChatMessage, 
  CommandExecution,
  GenerationResponse,
  ConversationResponse,
  User,
  UserProfile
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;
  private isRefreshing: boolean = false;
  private failedQueue: any[] = [];

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If already refreshing, queue the request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject, config: originalRequest });
            });
          }

          originalRequest._retry = true;
          const refreshToken = localStorage.getItem('refresh_token');
          
          if (refreshToken) {
            this.isRefreshing = true;
            
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.access);
              
              // Process the queued requests
              this.failedQueue.forEach(({ resolve, config }) => {
                config.headers.Authorization = `Bearer ${response.access}`;
                resolve(this.api(config));
              });
              this.failedQueue = [];
              
              // Retry the original request
              originalRequest.headers.Authorization = `Bearer ${response.access}`;
              return this.api(originalRequest);
            } catch (refreshError) {
              // Process the queued requests with error
              this.failedQueue.forEach(({ reject }) => {
                reject(refreshError);
              });
              this.failedQueue = [];
              
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            } finally {
              this.isRefreshing = false;
            }
          } else {
            // No refresh token, redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await this.api.post('/auth/login/', { username, password });
    return response.data;
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<AuthResponse> {
    // Add password_confirm field required by backend
    const registrationData = {
      ...userData,
      password_confirm: userData.password
    };
    const response = await this.api.post('/auth/register/', registrationData);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<{ access: string }> {
    // Use direct axios call to avoid interceptor loop
    const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { 
      refresh: refreshToken 
    });
    return response.data;
  }

  async getProfile(): Promise<User> {
    const response = await this.api.get('/auth/profile/');
    return response.data;
  }

  async logout(refreshToken: string): Promise<void> {
    await this.api.post('/auth/logout/', { refresh: refreshToken });
  }

  // Projects
  async getProjects(): Promise<{ results: Project[]; count: number }> {
    const response = await this.api.get('/api/projects/');
    return response.data;
  }

  async createProject(projectData: CreateProjectRequest): Promise<Project> {
    const response = await this.api.post('/api/projects/', projectData);
    return response.data;
  }

  // Quick create and generate project from simple description
  async quickCreateAndGenerate(description: string): Promise<{
    success: boolean;
    project: Project;
    message: string;
    status: string;
    project_id: string;
    ai_response?: string;
    files_generated?: number;
    access_url?: string;
    setup_commands?: string[];
    error?: string;
  }> {
    const response = await this.api.post('/api/projects/quick_create_and_generate/', {
      description
    });
    return response.data;
  }

  async getGenerationStatus(projectId: string): Promise<{
    project_id: string;
    status: string;
    django_project_created: boolean;
    files_count: number;
    latest_message?: string;
    project_name: string;
    is_running: boolean;
    access_url?: string;
    main_app_name?: string;
    setup_complete?: boolean;
  }> {
    const response = await this.api.get(`/api/projects/${projectId}/generation_status/`);
    return response.data;
  }

  async getProject(id: string): Promise<Project> {
    const response = await this.api.get(`/api/projects/${id}/`);
    return response.data;
  }

  async updateProject(id: string, projectData: Partial<CreateProjectRequest>): Promise<Project> {
    const response = await this.api.put(`/api/projects/${id}/`, projectData);
    return response.data;
  }

  async deleteProject(id: string): Promise<void> {
    await this.api.delete(`/api/projects/${id}/`);
  }

  // Container Management
  async startContainer(projectId: string): Promise<{ message: string; port?: number; container_id?: string; status: string }> {
    const response = await this.api.post(`/api/projects/${projectId}/start_container/`);
    return response.data;
  }

  async getContainerStatus(projectId: string): Promise<{ project_id: string; status: string; is_running: boolean; container_port?: number; container_id?: string }> {
    const response = await this.api.get(`/api/projects/${projectId}/container_status/`);
    return response.data;
  }

  async stopContainer(projectId: string, forceKill: boolean = false): Promise<{ message: string }> {
    const response = await this.api.post(`/api/projects/${projectId}/stop_container/`, {
      force_kill: forceKill
    });
    return response.data;
  }

  // AI Generation
  async smartGenerate(projectId: string, message: string): Promise<GenerationResponse> {
    const response = await this.api.post(`/api/projects/${projectId}/smart_generate/`, { message });
    return response.data;
  }

  // Server-Sent Events for streaming generation
  createGenerationStream(projectId: string, message: string): EventSource {
    const token = localStorage.getItem('access_token');
    const url = `${API_BASE_URL}/api/projects/${projectId}/smart_generate_stream/`;
    
    // For SSE with authentication, we need to use a different approach
    // Since EventSource doesn't support custom headers, we'll pass the token as a query parameter
    const urlWithAuth = `${url}?token=${encodeURIComponent(token || '')}&message=${encodeURIComponent(message)}`;
    
    return new EventSource(urlWithAuth);
  }

  // File Management
  async getProjectFiles(projectId: string): Promise<ProjectFile[]> {
    const response = await this.api.get(`/api/projects/${projectId}/files/`);
    return response.data;
  }

  async getFilesystemFiles(projectId: string): Promise<any[]> {
    const response = await this.api.get(`/api/projects/${projectId}/filesystem_files/`);
    return response.data;
  }

  async getFileContent(projectId: string, path: string): Promise<{ path: string; content: string }> {
    const response = await this.api.get(`/api/projects/${projectId}/files/content/?path=${encodeURIComponent(path)}`);
    return response.data;
  }

  async saveFile(projectId: string, path: string, content: string): Promise<{ message: string }> {
    const response = await this.api.post(`/api/projects/${projectId}/save_file/`, { path, content });
    return response.data;
  }

  // Chat & Conversation
  async conversationChat(
    projectId: string, 
    message: string, 
    isError: boolean = false,
    errorType: string = '',
    errorSource: string = ''
  ): Promise<ConversationResponse> {
    const response = await this.api.post(`/api/projects/${projectId}/conversation_chat/`, {
      message,
      is_error: isError,
      error_type: errorType,
      error_source: errorSource
    });
    return response.data;
  }

  async reportError(
    projectId: string,
    errorMessage: string,
    errorType: string,
    errorSource: string
  ): Promise<ConversationResponse> {
    const response = await this.api.post(`/api/projects/${projectId}/report_error/`, {
      error_message: errorMessage,
      error_type: errorType,
      error_source: errorSource
    });
    return response.data;
  }

  async getConversationHistory(projectId: string): Promise<{ messages: ChatMessage[]; total_messages: number; thread_id: string }> {
    const response = await this.api.get(`/api/projects/${projectId}/conversation_history/`);
    return response.data;
  }

  // Command Execution
  async executeCommand(projectId: string, command: string): Promise<{ output: string; error: string; exit_code: number }> {
    const response = await this.api.post(`/api/projects/${projectId}/execute_command/`, { command });
    return response.data;
  }

  async getCommandHistory(projectId: string): Promise<CommandExecution[]> {
    const response = await this.api.get(`/api/projects/${projectId}/executions/`);
    return response.data;
  }

  // Project Statistics
  async getProjectStats(projectId: string): Promise<{
    files_count: number;
    total_lines: number;
    total_size: number;
    messages_count: number;
    executions_count: number;
    last_activity: string;
    is_running: boolean;
  }> {
    const response = await this.api.get(`/api/projects/${projectId}/stats/`);
    return response.data;
  }

  // 🔐 User Profile & Dashboard
  async getUserProfile(): Promise<UserProfile> {
    const response = await this.api.get('/api/user-profile/');
    return response.data;
  }

  async updateUserProfile(profileData: any): Promise<UserProfile> {
    const response = await this.api.patch('/api/user-profile/update_profile/', profileData);
    return response.data;
  }

  async getDashboardStats(): Promise<any> {
    const response = await this.api.get('/api/user-profile/dashboard_stats/');
    return response.data;
  }

  async getProjectHistory(filters?: {
    type?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
  }): Promise<any> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }
    const response = await this.api.get(`/api/project-history/?${params}`);
    return response.data;
  }

  // 💬 Chat Threading
  async getChatThreads(): Promise<any[]> {
    const response = await this.api.get('/api/chat-threads/');
    return response.data;
  }

  async resumeConversation(threadId: string, fromMessageId?: string): Promise<any> {
    const response = await this.api.post(`/api/chat-threads/${threadId}/resume_conversation/`, {
      from_message_id: fromMessageId
    });
    return response.data;
  }

  async clearChatContext(threadId: string): Promise<any> {
    const response = await this.api.post(`/api/chat-threads/${threadId}/clear_context/`);
    return response.data;
  }

  // 🔧 Error Management & Auto-Fix
  async getErrorLogs(projectId?: string): Promise<any[]> {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await this.api.get(`/api/error-logs/${params}`);
    return response.data;
  }

  async getErrorDashboard(projectId?: string): Promise<any> {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await this.api.get(`/api/error-logs/dashboard/${params}`);
    return response.data;
  }

  async autoFixError(errorId: string): Promise<any> {
    const response = await this.api.post(`/api/error-logs/${errorId}/auto_fix/`);
    return response.data;
  }

  async reportError(projectId: string, errorData: {
    error_type: string;
    error_message: string;
    traceback?: string;
    file_path?: string;
    line_number?: number;
    command?: string;
    user_action?: string;
  }): Promise<any> {
    const response = await this.api.post(`/api/error-logs/`, {
      project: projectId,
      ...errorData
    });
    return response.data;
  }

  // 📈 Usage Analytics
  async getAnalyticsDashboard(days: number = 30): Promise<any> {
    const response = await this.api.get(`/api/analytics/dashboard/?days=${days}`);
    return response.data;
  }

  async trackAction(actionData: {
    action_type: string;
    action_data?: any;
    response_time_ms?: number;
    tokens_used?: number;
    success?: boolean;
    page_url?: string;
    referrer?: string;
  }): Promise<any> {
    const response = await this.api.post('/api/analytics/track_action/', actionData);
    return response.data;
  }

  // 📊 Project Sessions
  async getProjectSessions(): Promise<any[]> {
    const response = await this.api.get('/api/sessions/');
    return response.data;
  }

  async startProjectSession(projectId: string): Promise<any> {
    const response = await this.api.post('/api/sessions/start_session/', {
      project_id: projectId
    });
    return response.data;
  }

  async endProjectSession(sessionId: string): Promise<any> {
    const response = await this.api.post(`/api/sessions/${sessionId}/end_session/`);
    return response.data;
  }

  // Enhanced conversation chat with threading
  async enhancedConversationChat(
    projectId: string,
    message: string,
    threadId?: string,
    isError: boolean = false,
    errorType: string = '',
    errorSource: string = ''
  ): Promise<any> {
    const payload: any = {
      message,
      is_error: isError,
      error_type: errorType,
      error_source: errorSource
    };

    if (threadId) {
      payload.thread_id = threadId;
    }

    const response = await this.api.post(`/api/projects/${projectId}/conversation_chat/`, payload);
    return response.data;
  }


  async uploadAvatar(file: File): Promise<{ message: string; avatar_url?: string }> {
    const formData = new FormData();
    formData.append('avatar', file);
    
    const response = await this.api.post('/api/user-profile/upload_avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async removeAvatar(): Promise<{ message: string }> {
    const response = await this.api.delete('/api/user-profile/remove_avatar/');
    return response.data;
  }

  async getDashboardStats(): Promise<any> {
    const response = await this.api.get('/api/user-profile/dashboard_stats/');
    return response.data;
  }

  // Billing API methods
  async getBillingDashboard(): Promise<any> {
    const response = await this.api.get('/api/billing/dashboard/');
    return response.data;
  }

  async getBillingPlans(): Promise<any> {
    const response = await this.api.get('/api/billing/plans/');
    return response.data;
  }

  async getCurrentSubscription(): Promise<any> {
    const response = await this.api.get('/api/billing/subscriptions/current/');
    return response.data;
  }

  async upgradeSubscription(subscriptionId: string, planId: number): Promise<any> {
    const response = await this.api.post(`/api/billing/subscriptions/${subscriptionId}/upgrade/`, {
      plan_id: planId
    });
    return response.data;
  }

  async getTokenUsage(params?: { start_date?: string; end_date?: string; usage_type?: string }): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value) searchParams.append(key, value);
      });
    }
    const response = await this.api.get(`/api/billing/usage/?${searchParams}`);
    return response.data;
  }

  async getTokenUsageChart(days: number = 30): Promise<any> {
    const response = await this.api.get(`/api/billing/dashboard/usage_chart/?days=${days}`);
    return response.data;
  }

  async getBillingInvoices(): Promise<any> {
    const response = await this.api.get('/api/billing/invoices/');
    return response.data;
  }

  // Payment Gateway API methods
  async getPaymentMethods(): Promise<any> {
    const response = await this.api.get('/api/payments/methods/');
    return response.data;
  }

  async createFlutterwavePayment(planId: number, purpose: string = 'subscription'): Promise<any> {
    const response = await this.api.post('/api/payments/flutterwave/create/', {
      plan_id: planId,
      purpose: purpose
    });
    return response.data;
  }

  async createCryptoPayment(planId: number, cryptoType: string, purpose: string = 'subscription'): Promise<any> {
    const response = await this.api.post('/api/payments/crypto/create/', {
      plan_id: planId,
      crypto_type: cryptoType,
      purpose: purpose
    });
    return response.data;
  }

  async checkPaymentStatus(reference: string): Promise<any> {
    const response = await this.api.get(`/api/payments/status/${reference}/`);
    return response.data;
  }

  async verifyFlutterwavePayment(transactionId: string): Promise<any> {
    const response = await this.api.post('/api/payments/flutterwave/verify/', {
      transaction_id: transactionId
    });
    return response.data;
  }

  async cancelPayment(reference: string): Promise<any> {
    const response = await this.api.post(`/api/payments/cancel/${reference}/`);
    return response.data;
  }

  async getUserPayments(): Promise<any> {
    const response = await this.api.get('/api/payments/history/');
    return response.data;
  }
}

export const apiService = new ApiService();