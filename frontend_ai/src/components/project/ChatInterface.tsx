import React, { useState, useEffect, useRef } from "react";
import {
  Send,
  Bot,
  User,
  AlertCircle,
  FileText,
  Clock,
  Loader2,
  History,
  RefreshCw,
  MessageSquare,
  Sparkles,
  CheckCircle,
  XCircle,
  Code2,
  Zap
} from "lucide-react";
import { useLocation } from "react-router-dom";
import { apiService } from "../../services/api";
import { aiStreamingService } from "../../services/aiStreamingService";
import { ChatMessage } from "../../types/api";
import Button from "../ui/Button";
import Badge from "../ui/Badge";
import Card from "../ui/Card";
import "../../styles/design-system.css";

interface ChatInterfaceProps {
  projectId: string;
  initialPrompt?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ projectId, initialPrompt }) => {
  const location = useLocation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [availableThreads, setAvailableThreads] = useState<any[]>([]);
  const [showThreadHistory, setShowThreadHistory] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // AI Streaming states
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationMessages, setGenerationMessages] = useState<string[]>([]);
  const [liveFiles, setLiveFiles] = useState<{[filename: string]: string}>({});
  const [streamingConnected, setStreamingConnected] = useState(false);
  const [typingIndicator, setTypingIndicator] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<string>('');
  const [generationProgress, setGenerationProgress] = useState({
    status: 'idle',
    progress: 0,
    currentFile: '',
    filesCreated: [] as string[]
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentStreamId = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initializeChat();
    initializeAIStreaming();
  }, [projectId]);

  // Auto-trigger initial prompt for project generation
  
useEffect(() => {
  if (
    initialPrompt &&
    initialPrompt.trim() &&
    messages.length === 0 &&
    !isLoadingHistory
  ) {
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: initialPrompt.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages([userMessage]);
    setInputMessage('');

    // Trigger streaming generation
    handleStreamingGeneration(initialPrompt.trim());
  }
}, [initialPrompt, messages.length, isLoadingHistory]);

useEffect(() => {
  const handleAutostart = (event: Event) => {
    const customEvent = event as CustomEvent;

    if (customEvent.detail.projectId === projectId) {
      const welcomeMessage: ChatMessage = {
        id: Date.now(),
        role: 'assistant',
        content: customEvent.detail.message,
        message_type: 'normal',
        timestamp: new Date().toISOString(),
        tokens_used: null,
        processing_time: null,
        is_error_report: false,
        error_type: '',
        error_source: '',
        files_modified: [],
        code_changes: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, welcomeMessage]);
    }
  };

  window.addEventListener('project-autostart', handleAutostart);

  return () => {
    window.removeEventListener('project-autostart', handleAutostart);
  };
}, [projectId]);

  // Handle URL prompt parameter from Dashboard
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const promptFromUrl = urlParams.get('prompt');
    
    console.log('🔍 URL parsing debug:', {
      fullUrl: window.location.href,
      search: location.search,
      urlParams: Object.fromEntries(urlParams.entries()),
      promptFromUrl,
      decodedPrompt: promptFromUrl ? decodeURIComponent(promptFromUrl) : null
    });
    
    console.log('🔍 Dashboard prompt check:', {
      promptFromUrl,
      hasPrompt: !!promptFromUrl,
      messagesLength: messages.length,
      isLoadingHistory,
      streamingConnected,
      allConditionsMet: promptFromUrl && promptFromUrl.trim() && messages.length === 0 && !isLoadingHistory && streamingConnected
    });
    
    // Check if we should auto-start (allow if only welcome message exists)
    const hasOnlyWelcomeMessage = messages.length === 1 && messages[0]?.role === 'assistant';
    const shouldAutoStart = promptFromUrl &&
      promptFromUrl.trim() &&
      (messages.length === 0 || hasOnlyWelcomeMessage) &&
      !isLoadingHistory &&
      streamingConnected;
    
    console.log('🔍 Auto-start evaluation:', {
      hasOnlyWelcomeMessage,
      shouldAutoStart,
      currentMessages: messages.map(m => ({ role: m.role, content: m.content?.substring(0, 50) + '...' }))
    });
    
    if (shouldAutoStart) {
      console.log('🎯 Auto-starting generation from Dashboard prompt:', promptFromUrl);
      
      const userMessage: ChatMessage = {
        id: Date.now(),
        role: 'user',
        content: promptFromUrl.trim(),
        message_type: 'normal',
        timestamp: new Date().toISOString(),
        tokens_used: null,
        processing_time: null,
        is_error_report: false,
        error_type: '',
        error_source: '',
        files_modified: [],
        code_changes: {},
        created_at: new Date().toISOString(),
      };

      setMessages([userMessage]);
      setInputMessage('');

      // Auto-start streaming with the Dashboard prompt
      const success = aiStreamingService.startGeneration(promptFromUrl.trim());
      if (success) {
        console.log('🚀 Successfully started auto-generation from Dashboard');
      } else {
        console.warn('⚠️ Failed to start auto-generation, falling back to manual');
      }
      
      // Clean up the URL parameter after processing
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('prompt');
      window.history.replaceState({}, '', newUrl.toString());
      console.log('🧹 Cleaned prompt from URL');
    }
  }, [location.search, messages.length, isLoadingHistory, streamingConnected]);

  const initializeAIStreaming = () => {
    // Connect to AI streaming service
    aiStreamingService.connect(projectId);
    
    // Subscribe to file changes - real-time like bolt.new
    const unsubscribeFiles = aiStreamingService.subscribeToFiles((file) => {
      console.log('📁 Live file update:', file);
      
      // Update live files for real-time viewing in file explorer
      setLiveFiles(prev => ({
        ...prev,
        [file.filename || file.file || 'unknown']: file.content
      }));
      
      // Notify parent component (ChatWithFiles) about file updates for file explorer
      window.dispatchEvent(new CustomEvent('liveFileUpdate', {
        detail: {
          filename: file.filename || file.file,
          content: file.content,
          action: file.action,
          token: file.token
        }
      }));
    });

    // Subscribe to generation messages
    const unsubscribeGeneration = aiStreamingService.subscribeToGeneration((message) => {
      console.log('💬 Generation message:', message);
      setGenerationMessages(prev => [...prev, message]);
    });

    // Subscribe to status updates
    const unsubscribeStatus = aiStreamingService.subscribeToStatus((status) => {
      console.log('📊 AI Streaming status:', JSON.stringify(status, null, 2));
      switch (status.type) {
        case 'connected':
          setStreamingConnected(true);
          break;
        case 'disconnected':
          setStreamingConnected(false);
          break;
        case 'generation_started':
          setIsGenerating(true);
          setGenerationMessages([]);
          setLiveFiles({});
          break;
        case 'generation_completed':
          setIsGenerating(false);
          // Refresh the conversation to show final results
          setTimeout(() => {
            loadConversationHistory();
          }, 1000);
          break;
        case 'error':
          setIsGenerating(false);
          setError(status.error || 'Generation failed');
          break;
      }
    });

    // Cleanup function
    return () => {
      unsubscribeFiles();
      unsubscribeGeneration();
      unsubscribeStatus();
    };
  };

  const initializeChat = async () => {
    try {
      // Start a new session
      const sessionResponse = await apiService.startProjectSession(projectId);
      setSessionId(sessionResponse.session_id);

      // Load conversation history and thread info
      await Promise.all([
        loadConversationHistory(),
        loadAvailableThreads()
      ]);
    } catch (err) {
      console.error('Failed to initialize chat:', err);
    }
  };

  const loadAvailableThreads = async () => {
    try {
      const threads = await apiService.getChatThreads();
      const threadArray = Array.isArray(threads) ? threads : [];
      const projectThreads = threadArray.filter((thread: any) => 
        thread.project === projectId
      );
      setAvailableThreads(projectThreads);
    } catch (err) {
      console.error('Failed to load threads:', err);
      setAvailableThreads([]);
    }
  };

  const loadConversationHistory = async () => {
    try {
      setIsLoadingHistory(true);
      setError(null);
      const response = await apiService.getConversationHistory(projectId);
      const processedMessages = response.messages.map((msg: any) => {
        console.log('Processing message:', msg);
        let content = msg.content;
        
        // Handle different content types properly
        if (typeof content === "string") {
          // Content is already a string, use as is
          content = content;
        } else if (content && typeof content === "object") {
          // If content is an object, try to extract the actual content
          if (content.content && typeof content.content === "string") {
            content = content.content;
          } else if (content.message && typeof content.message === "string") {
            content = content.message;
          } else if (content.text && typeof content.text === "string") {
            content = content.text;
          } else {
            // Fallback to stringifying the object
            content = JSON.stringify(content);
          }
        } else {
          // Handle null, undefined, or other types
          content = content ? String(content) : "Empty message";
        }
        
        console.log('Final content:', content);
        return {
          ...msg,
          content
        };
      });
      setMessages(processedMessages);

      // Add welcome message if no messages exist
      if (response.messages.length === 0) {
        const welcomeMessage: ChatMessage = {
          id: 0,
          role: "assistant",
          content:
            "Hello! I'm here to help you with your Django project. You can ask me to add features, fix bugs, or modify your code. What would you like to work on?",
          message_type: "normal",
          timestamp: new Date().toISOString(),
          tokens_used: null,
          processing_time: null,
          is_error_report: false,
          error_type: "",
          error_source: "",
          files_modified: [],
          code_changes: {},
          created_at: new Date().toISOString(),
        };
        setMessages([welcomeMessage]);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error || "Failed to load conversation history"
      );
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || isGenerating) return;

    const messageText = inputMessage.trim();
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: messageText,
      message_type: "normal",
      timestamp: new Date().toISOString(),
      tokens_used: null,
      processing_time: null,
      is_error_report: false,
      error_type: "",
      error_source: "",
      files_modified: [],
      code_changes: {},
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setError(null);

    // Comprehensive detection for streaming operations
    const streamingKeywords = {
      generation: ['create', 'generate', 'build', 'implement', 'add feature', 'develop', 'make', 'setup', 'initialize'],
      modification: ['update', 'modify', 'change', 'edit', 'improve', 'enhance', 'refactor', 'optimize'],
      debugging: ['fix', 'debug', 'resolve', 'error', 'bug', 'issue', 'problem', 'troubleshoot'],
      testing: ['test', 'verify', 'check', 'validate', 'ensure'],
      deployment: ['deploy', 'publish', 'release', 'launch', 'migrate', 'run']
    };

    const lowerText = messageText.toLowerCase();
    let operationType = 'chat';
    let shouldStream = false;

    // Determine operation type and streaming necessity
    for (const [type, keywords] of Object.entries(streamingKeywords)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        operationType = type;
        shouldStream = true;
        break;
      }
    }

    // Force streaming for complex operations or file-related requests
    const fileRelatedTerms = ['file', 'model', 'view', 'template', 'form', 'url', 'api', 'database', 'migration'];
    if (!shouldStream && fileRelatedTerms.some(term => lowerText.includes(term))) {
      shouldStream = true;
      operationType = 'modification';
    }

    console.log(`🎯 Detected operation: ${operationType}, shouldStream: ${shouldStream}`);

    // Use streaming for all operations that might involve file changes
    if (shouldStream) {
      console.log('🚀 Starting streaming operation via WebSocket');
      
      // First try WebSocket streaming if connected
      if (streamingConnected && aiStreamingService.isConnected()) {
        console.log('📡 Using WebSocket streaming for operation:', operationType);
        const success = aiStreamingService.startGeneration(messageText);
        if (success) {
          setIsLoading(false);
          return; // Let WebSocket handle the streaming
        } else {
          console.warn('⚠️ WebSocket streaming failed, trying SSE fallback');
        }
      }
      
      // Fallback to SSE streaming
      try {
        console.log('📡 Using SSE streaming for operation:', operationType);
        await handleStreamingGeneration(messageText, operationType);
        return;
      } catch (error) {
        console.warn('⚠️ SSE Streaming failed, falling back to regular chat:', error);
      }
    }

    // Fallback to regular chat API for simple conversational requests
    setIsLoading(true);
    try {
      const response = await apiService.conversationChat(
        projectId,
        messageText
      );

      // Process response message content properly
      let assistantContent = response.message;
      if (typeof assistantContent === "string") {
        assistantContent = assistantContent;
      } else if (assistantContent && typeof assistantContent === "object") {
        if (assistantContent.content && typeof assistantContent.content === "string") {
          assistantContent = assistantContent.content;
        } else if (assistantContent.message && typeof assistantContent.message === "string") {
          assistantContent = assistantContent.message;
        } else if (assistantContent.text && typeof assistantContent.text === "string") {
          assistantContent = assistantContent.text;
        } else {
          assistantContent = JSON.stringify(assistantContent);
        }
      } else {
        assistantContent = assistantContent ? String(assistantContent) : "Empty response";
      }

      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: assistantContent,
        message_type: "normal",
        timestamp: new Date().toISOString(),
        tokens_used: null,
        processing_time: response.processing_time,
        is_error_report: false,
        error_type: "",
        error_source: "",
        files_modified: response.files_modified || [],
        code_changes: response.code_changes || {},
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to send message");

      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "system",
        content:
          "Sorry, I encountered an error while processing your request. Please try again.",
        message_type: "normal",
        timestamp: new Date().toISOString(),
        tokens_used: null,
        processing_time: null,
        is_error_report: false,
        error_type: "",
        error_source: "",
        files_modified: [],
        code_changes: {},
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleReportError = async (
    errorMessage: string,
    errorType: string,
    errorSource: string
  ) => {
    try {
      setIsLoading(true);
      const response = await apiService.reportError(
        projectId,
        errorMessage,
        errorType,
        errorSource
      );

      // Process response message content properly
      let reportContent = response.message;
      if (typeof reportContent === "string") {
        reportContent = reportContent;
      } else if (reportContent && typeof reportContent === "object") {
        if (reportContent.content && typeof reportContent.content === "string") {
          reportContent = reportContent.content;
        } else if (reportContent.message && typeof reportContent.message === "string") {
          reportContent = reportContent.message;
        } else if (reportContent.text && typeof reportContent.text === "string") {
          reportContent = reportContent.text;
        } else {
          reportContent = JSON.stringify(reportContent);
        }
      } else {
        reportContent = reportContent ? String(reportContent) : "Empty response";
      }

      const assistantMessage: ChatMessage = {
        id: Date.now(),
        role: "assistant",
        content: reportContent,
        message_type: "fix_applied",
        timestamp: new Date().toISOString(),
        tokens_used: null,
        processing_time: response.processing_time,
        is_error_report: false,
        error_type: "",
        error_source: "",
        files_modified: response.files_modified || [],
        code_changes: response.code_changes || {},
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to report error");
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getMessageIcon = (role: string, messageType?: string) => {
    if (role === "user") return <User className="w-5 h-5" />;
    if (messageType === "error_report")
      return <AlertCircle className="w-5 h-5 text-red-400" />;
    return <Bot className="w-5 h-5" />;
  };

  const getMessageBgColor = (role: string, messageType?: string) => {
    if (role === "user") return "bg-blue-600";
    if (messageType === "error_report") return "bg-red-600";
    if (messageType === "fix_applied") return "bg-green-600";
    return "bg-gray-700";
  };

  // Comprehensive streaming function for all AI operations
  const handleStreamingGeneration = async (prompt: string, operationType = 'project_generation') => {
    if (isGenerating) return;
    
    setIsGenerating(true);
    setTypingIndicator(true);
    
    // Set initial status based on operation type
    const initialStatus = {
      'generation': 'initializing',
      'modification': 'analyzing',
      'debugging': 'investigating',
      'testing': 'preparing',
      'deployment': 'configuring',
      'chat': 'processing'
    }[operationType] || 'processing';
    
    setGenerationProgress({
      status: initialStatus,
      progress: 0,
      currentFile: '',
      filesCreated: []
    });

    try {
      // Create a streaming ID for this operation
      const streamId = Date.now().toString();
      currentStreamId.current = streamId;

      // Add operation-specific initial message
      const initialMessages = {
        'generation': '🚀 Initializing project generation...',
        'modification': '🔧 Analyzing code for modifications...',
        'debugging': '🐛 Investigating the issue...',
        'testing': '🧪 Preparing test scenarios...',
        'deployment': '📦 Configuring deployment settings...',
        'chat': '💭 Processing your request...'
      };

      const streamingMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: initialMessages[operationType] || 'Processing your request...',
        created_at: new Date().toISOString(),
        streaming: true,
        operationType
      };
      setMessages(prev => [...prev, streamingMessage]);

      // Enhanced streaming endpoint selection based on operation type
      let streamEndpoint;
      switch (operationType) {
        case 'generation':
          streamEndpoint = `smart_generate_stream`;
          break;
        case 'modification':
        case 'debugging':
        case 'testing':
          streamEndpoint = `conversation_stream`;
          break;
        default:
          streamEndpoint = `conversation_stream`;
      }

      // Get auth token for streaming
      const token = localStorage.getItem('access_token');

      // Start the streaming with operation-specific endpoint
      const eventSource = new EventSource(
        `http://localhost:8000/api/projects/${projectId}/${streamEndpoint}/?prompt=${encodeURIComponent(prompt)}&operation_type=${operationType}&token=${token}`,
        { withCredentials: true }
      );
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Enhanced real-time message updates with operation context
          setMessages(prev => prev.map(msg => 
            msg.streaming && msg.id === streamingMessage.id 
              ? { 
                  ...msg, 
                  content: data.message || msg.content,
                  files_modified: data.files_modified || msg.files_modified || []
                }
              : msg
          ));

          switch (data.type) {
            case 'status':
              setGenerationProgress(prev => ({
                ...prev,
                status: data.status || 'processing',
                progress: data.progress || prev.progress
              }));
              setCurrentStreamingMessage(data.message);
              break;
              
            case 'thinking':
              setCurrentStreamingMessage(`🤔 ${data.message}`);
              break;
              
            case 'analyzing':
              setCurrentStreamingMessage(`🔍 ${data.message}`);
              setGenerationProgress(prev => ({ ...prev, progress: 20 }));
              break;
              
            case 'planning':
              setCurrentStreamingMessage(`📋 ${data.message}`);
              setGenerationProgress(prev => ({ ...prev, progress: 35 }));
              break;
              
            case 'file_processing':
              setGenerationProgress(prev => ({
                ...prev,
                currentFile: data.current_file,
                progress: data.progress || prev.progress
              }));
              setCurrentStreamingMessage(`📝 Processing: ${data.current_file}`);
              break;
              
            case 'file_created':
            case 'file_modified':
              setGenerationProgress(prev => ({
                ...prev,
                filesCreated: [...prev.filesCreated, data.file],
                currentFile: data.file,
                progress: data.progress || prev.progress
              }));
              const action = data.type === 'file_created' ? 'Created' : 'Modified';
              setCurrentStreamingMessage(`✅ ${action}: ${data.file}`);
              break;
              
            case 'error_found':
              setCurrentStreamingMessage(`❌ Found error: ${data.message}`);
              break;
              
            case 'error_fixing':
              setCurrentStreamingMessage(`🔧 Fixing: ${data.message}`);
              setGenerationProgress(prev => ({ ...prev, progress: 60 }));
              break;
              
            case 'testing':
              setCurrentStreamingMessage(`🧪 Testing: ${data.message}`);
              setGenerationProgress(prev => ({ ...prev, progress: 80 }));
              break;
              
            case 'deployment':
              setCurrentStreamingMessage(`🚀 Deploying: ${data.message}`);
              setGenerationProgress(prev => ({ ...prev, progress: 90 }));
              break;
              
            case 'template_generated':
              setCurrentStreamingMessage(`📄 Generated template: ${data.template_name}`);
              break;
              
            case 'migration_created':
              setCurrentStreamingMessage(`🗃️ Created migration: ${data.migration_name}`);
              break;
              
            case 'dependency_installed':
              setCurrentStreamingMessage(`📦 Installed: ${data.package}`);
              break;
              
            case 'live_update':
              // Real-time file content updates
              if (data.file && data.content) {
                setLiveFiles(prev => ({
                  ...prev,
                  [data.file]: data.content
                }));
              }
              break;
              
            case 'completed':
              // Enhanced completion message with operation summary
              const completionMessages = {
                'generation': `🎉 Project generated successfully! Created ${data.files?.length || 0} files.`,
                'modification': `✅ Code modifications completed! Updated ${data.files?.length || 0} files.`,
                'debugging': `🐛 Debug fixes applied! Resolved issues in ${data.files?.length || 0} files.`,
                'testing': `🧪 Testing completed! Verified ${data.files?.length || 0} components.`,
                'deployment': `🚀 Deployment ready! Configured ${data.files?.length || 0} files.`,
                'chat': `💬 Task completed successfully!`
              };
              
              const finalMessage = {
                ...streamingMessage,
                content: data.message || completionMessages[operationType] || 'Task completed successfully!',
                streaming: false,
                files_modified: data.files || [],
                operationType: `${operationType}_complete`
              };
              
              setMessages(prev => prev.map(msg => 
                msg.id === streamingMessage.id ? finalMessage : msg
              ));
              
              setGenerationProgress({
                status: 'completed',
                progress: 100,
                currentFile: '',
                filesCreated: data.files?.map((f: any) => f.path || f) || []
              });
              
              // Refresh file tree and project state
              setTimeout(() => {
                window.dispatchEvent(new CustomEvent('refresh-file-tree'));
                loadConversationHistory();
              }, 1000);
              
              eventSource.close();
              setIsGenerating(false);
              setTypingIndicator(false);
              currentStreamId.current = null;
              break;
              
            case 'error':
              const errorMessage = {
                ...streamingMessage,
                content: `❌ Error: ${data.message || 'Operation failed'}`,
                streaming: false,
                messageType: 'error'
              };
              
              setMessages(prev => prev.map(msg => 
                msg.id === streamingMessage.id ? errorMessage : msg
              ));
              
              eventSource.close();
              setIsGenerating(false);
              setTypingIndicator(false);
              currentStreamId.current = null;
              break;
              
            default:
              // Handle any custom operation types
              if (data.message) {
                setCurrentStreamingMessage(data.message);
              }
              if (data.progress) {
                setGenerationProgress(prev => ({ ...prev, progress: data.progress }));
              }
          }
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        
        const errorMessage = {
          ...streamingMessage,
          content: '🔌 Connection error occurred. Please try again.',
          streaming: false,
          messageType: 'error'
        };
        
        setMessages(prev => prev.map(msg => 
          msg.id === streamingMessage.id ? errorMessage : msg
        ));
        
        eventSource.close();
        setIsGenerating(false);
        setTypingIndicator(false);
        currentStreamId.current = null;
      };
      
    } catch (error) {
      console.error('Failed to start streaming generation:', error);
      setIsGenerating(false);
      setTypingIndicator(false);
      currentStreamId.current = null;
    }
  };

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-full bg-primary">
        <Card className="text-center">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-secondary">Loading conversation...</span>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-black">
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        </div>
      )}


      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6 bg-black">
        {messages.map((message) => (
          <div key={message.id} className="flex gap-3 sm:gap-4">
            {/* Avatar */}
            <div
              className={`flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shadow-sm ${
                message.role === "user"
                  ? "bg-blue-600"
                  : message.message_type === "error_report"
                  ? "bg-red-600"
                  : message.message_type === "fix_applied"
                  ? "bg-green-600"
                  : "bg-purple-600"
              }`}
            >
              {message.role === "user" ? (
                <User className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              ) : message.message_type === "error_report" ? (
                <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              ) : (
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              )}
            </div>

            {/* Message Content */}
            <div className="flex-1 min-w-0">
              {/* Message Header */}
              <div className="flex items-center gap-3 mb-2">
                <span className="text-sm font-semibold text-white">
                  {message.role === "user" ? "You" : "AI Assistant"}
                </span>
                <span className="text-xs text-gray-400">
                  {formatTimestamp(message.created_at)}
                </span>
                {message.streaming && (
                  <Badge variant="neutral" size="sm" className="animate-pulse">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    Generating...
                  </Badge>
                )}
                {message.processing_time && (
                  <Badge variant="neutral" size="sm">
                    <Clock className="w-3 h-3 mr-1" />
                    {message.processing_time.toFixed(1)}s
                  </Badge>
                )}
              </div>

              {/* Message Text */}
              <div 
                className={`
                  prose prose-sm max-w-none
                  ${message.role === "user" 
                    ? "bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-3 sm:p-4" 
                    : "text-gray-300"
                  }
                `}
              >
                <div className="whitespace-pre-wrap leading-relaxed text-sm sm:text-base">
                  {(() => {
                    if (typeof message.content === "string") {
                      return message.content;
                    } else if (message.content && typeof message.content === "object") {
                      if (message.content.content && typeof message.content.content === "string") {
                        return message.content.content;
                      } else if (message.content.message && typeof message.content.message === "string") {
                        return message.content.message;
                      } else if (message.content.text && typeof message.content.text === "string") {
                        return message.content.text;
                      } else {
                        return JSON.stringify(message.content, null, 2);
                      }
                    } else {
                      return message.content ? String(message.content) : "Empty message";
                    }
                  })()}
                </div>
              </div>

              {/* Streaming Progress Section */}
              {message.streaming && message.role === 'assistant' && generationProgress.status !== 'idle' && (
                <div className="mt-4 bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-blue-400 flex items-center">
                      <Zap className="w-4 h-4 mr-2" />
                      {generationProgress.status === 'completed' ? 'Generation Complete' : 'Live Generation Progress'}
                    </h4>
                    <span className="text-xs text-gray-400">{generationProgress.progress}%</span>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${generationProgress.progress}%` }}
                    />
                  </div>
                  
                  {/* Current File */}
                  {generationProgress.currentFile && (
                    <div className="mb-3">
                      <div className="text-xs text-blue-400 mb-1">Currently processing:</div>
                      <div className="text-sm font-mono bg-gray-800 px-2 py-1 rounded border-l-2 border-blue-500">
                        {generationProgress.currentFile}
                      </div>
                    </div>
                  )}
                  
                  {/* Files Created */}
                  {generationProgress.filesCreated.length > 0 && (
                    <div>
                      <div className="text-xs text-green-400 mb-2 flex items-center">
                        <FileText className="w-3 h-3 mr-1" />
                        Files Created ({generationProgress.filesCreated.length})
                      </div>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {generationProgress.filesCreated.slice(-5).map((file, index) => (
                          <div key={index} className="text-xs font-mono bg-gray-800 px-2 py-1 rounded text-green-300">
                            ✓ {file}
                          </div>
                        ))}
                        {generationProgress.filesCreated.length > 5 && (
                          <div className="text-xs text-gray-400 text-center">
                            ... and {generationProgress.filesCreated.length - 5} more files
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Files Modified Section */}
              {Array.isArray(message.files_modified) &&
                message.files_modified.length > 0 && (
                  <Card className="mt-4 bg-gray-800/50 border-gray-700/50" padding="sm">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-medium text-green-400">
                        Files Modified ({message.files_modified.length})
                      </span>
                    </div>
                    <div className="space-y-2">
                      {message.files_modified.map((file: string, index: number) => (
                        <div key={index} className="text-sm">
                          <div className="flex items-center gap-2">
                            <FileText className="w-3 h-3 text-blue-400" />
                            <span className="font-mono text-blue-300">{file}</span>
                          </div>
                          {message.code_changes?.[file] && (
                            <div className="ml-5 mt-1 text-xs text-gray-400">
                              {(() => {
                                const change = message.code_changes[file];
                                if (typeof change === "string") {
                                  return change;
                                } else if (change && typeof change === "object") {
                                  if (change.content && typeof change.content === "string") {
                                    return change.content;
                                  } else if (change.message && typeof change.message === "string") {
                                    return change.message;
                                  } else if (change.text && typeof change.text === "string") {
                                    return change.text;
                                  } else {
                                    return JSON.stringify(change);
                                  }
                                } else {
                                  return change ? String(change) : "No change details";
                                }
                              })()}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

              {/* Quick Actions */}
              {message.role === "assistant" &&
                message.files_modified &&
                message.files_modified.length > 0 && (
                  <div className="mt-4">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setInputMessage("Run migrations to apply the changes")}
                        className="text-xs"
                      >
                        Run migrations
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setInputMessage("Test the new functionality")}
                        className="text-xs"
                      >
                        Test changes
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setInputMessage("Add CSS styling to improve the appearance")}
                        className="text-xs"
                      >
                        Add styling
                      </Button>
                    </div>
                  </div>
                )}
            </div>
          </div>
        ))}

        {/* Enhanced Live Generation Section with Production UX */}
        {isGenerating && (
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6 relative overflow-hidden">
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-cyan-500/5 animate-pulse" />
            
            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-4">
                <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white animate-pulse" />
                  {/* Ripple effect */}
                  <div className="absolute inset-0 bg-blue-400 rounded-xl animate-ping opacity-20" />
                  <div className="absolute inset-0 bg-purple-400 rounded-xl animate-ping opacity-10" style={{ animationDelay: '0.5s' }} />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    {generationProgress.status === 'completed' ? '✅' : '🚀'} Live AI {generationProgress.status === 'completed' ? 'Completed' : 'Generation'}
                    <Badge variant={generationProgress.status === 'completed' ? 'success' : 'primary'} size="sm">
                      <div className={`w-2 h-2 rounded-full mr-2 ${generationProgress.status === 'completed' ? 'bg-green-400' : 'bg-white animate-pulse'}`}></div>
                      {generationProgress.status === 'completed' ? 'COMPLETE' : 'STREAMING'}
                    </Badge>
                  </h3>
                  <div className="flex items-center gap-2">
                    <p className="text-gray-400 text-sm">{currentStreamingMessage || 'Processing your request...'}</p>
                    {typingIndicator && (
                      <div className="flex space-x-1">
                        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" />
                        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">{generationProgress.progress}%</div>
                  <div className="text-xs text-gray-400">Progress</div>
                </div>
              </div>
              
              {/* Enhanced Progress Bar */}
              <div className="relative mb-4">
                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div 
                    className="h-3 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-full transition-all duration-500 ease-out relative"
                    style={{ width: `${generationProgress.progress}%` }}
                  >
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-shimmer" />
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Started</span>
                  <span className="font-medium">{generationProgress.status}</span>
                  <span>Complete</span>
                </div>
              </div>
            </div>

            {/* Generation Messages */}
            {generationMessages.length > 0 && (
              <Card className="mb-4 bg-gray-800/30 border-gray-600/50" padding="sm">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="w-4 h-4 text-blue-400" />
                  <span className="text-sm font-medium text-blue-300">Generation Log</span>
                </div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {generationMessages.map((msg, index) => (
                    <div key={index} className="text-xs text-gray-300 font-mono">
                      {msg}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Live Files Preview */}
            {Object.keys(liveFiles).length > 0 && (
              <Card className="bg-gray-800/30 border-gray-600/50" padding="sm">
                <div className="flex items-center gap-2 mb-3">
                  <Code2 className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-medium text-green-300">
                    Live Files ({Object.keys(liveFiles).length})
                  </span>
                </div>
                <div className="grid gap-2 max-h-60 overflow-y-auto">
                  {Object.entries(liveFiles).map(([filename, content]) => (
                    <div key={filename} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-3 h-3 text-blue-400" />
                        <span className="text-xs font-mono text-blue-300">{filename}</span>
                        <Badge variant="success" size="sm">
                          {content.length} chars
                        </Badge>
                      </div>
                      <div className="text-xs font-mono text-gray-400 bg-black/30 rounded p-2 max-h-32 overflow-y-auto">
                        {content.slice(0, 500)}{content.length > 500 ? '...' : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Streaming Connection Status */}
            <div className="flex items-center gap-2 mt-4 text-xs">
              <div className={`w-2 h-2 rounded-full ${streamingConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className={streamingConnected ? 'text-green-400' : 'text-red-400'}>
                {streamingConnected ? 'Connected to AI stream' : 'Disconnected from AI stream'}
              </span>
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && !isGenerating && (
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-sm font-semibold text-primary">AI Assistant</span>
                <Badge variant="primary" size="sm">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  thinking...
                </Badge>
              </div>
              <div className="text-gray-300">
                Processing your request...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Section */}
      <div className="border-t border-gray-700/50 bg-gray-900/50 backdrop-blur-sm p-4 sm:p-6">
        {/* Streaming Status Indicator */}
        {streamingConnected && (
          <div className="mb-3 text-center">
            <Badge variant="success" size="sm">
              <Zap className="w-3 h-3 mr-1" />
              Live Streaming Available
            </Badge>
            <p className="text-xs text-gray-400 mt-1">
              Generation requests will stream live as files are created
            </p>
          </div>
        )}

        {/* Quick Suggestions */}
        <div className="mb-4 hidden sm:block">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInputMessage("Create a user authentication system with login and registration")}
              className="text-xs"
            >
              🔐 Add authentication
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInputMessage("Generate a contact form with email sending functionality")}
              className="text-xs"
            >
              📝 Contact form
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInputMessage("Implement file upload functionality with image preview")}
              className="text-xs"
            >
              📎 File upload
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInputMessage("Build an admin dashboard with user management")}
              className="text-xs"
            >
              🏠 Admin dashboard
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInputMessage("Create a blog system with posts and comments")}
              className="text-xs"
            >
              📰 Blog system
            </Button>
          </div>
        </div>

        {/* Message Input */}
        <div className="flex gap-2 sm:gap-3">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me to add features, fix bugs, or modify your code..."
              className="w-full px-4 py-3 bg-gray-800/50 backdrop-blur-sm border border-gray-600/50 rounded-xl text-white placeholder-gray-400 font-medium transition-all duration-300 focus:outline-none focus:border-blue-500 focus:shadow-lg focus:shadow-blue-500/25 focus:bg-gray-800/80 hover:border-gray-500/70 resize-none text-sm sm:text-base"
              rows={window.innerWidth < 640 ? 2 : 3}
              disabled={isLoading}
            />
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading || isGenerating}
            loading={isLoading || isGenerating}
            icon={!isLoading && !isGenerating ? 
              (streamingConnected ? <Zap className="w-4 h-4" /> : <Send className="w-4 h-4" />) : 
              undefined
            }
            className="self-end"
            size="sm"
            variant={streamingConnected ? "primary" : "secondary"}
          >
            <span className="hidden sm:inline">
              {isGenerating ? 'Generating...' : streamingConnected ? 'Stream' : 'Send'}
            </span>
            <span className="sm:hidden">
              {isGenerating ? '...' : streamingConnected ? 'Stream' : 'Send'}
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
