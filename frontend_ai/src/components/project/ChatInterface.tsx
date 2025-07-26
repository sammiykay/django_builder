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
import { apiService } from "../../services/api";
import { aiStreamingService } from "../../services/aiStreamingService";
import { ChatMessage } from "../../types/api";
import Button from "../ui/Button";
import Badge from "../ui/Badge";
import Card from "../ui/Card";
import "../../styles/design-system.css";

interface ChatInterfaceProps {
  projectId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ projectId }) => {
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
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initializeChat();
    initializeAIStreaming();
    
    // Listen for autostart events from project creation
    const handleAutostart = (event: CustomEvent) => {
      if (event.detail.projectId === projectId) {
        const welcomeMessage: ChatMessage = {
          id: Date.now(),
          role: "assistant",
          content: event.detail.message,
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
        setMessages(prev => [...prev, welcomeMessage]);
      }
    };

    window.addEventListener('project-autostart', handleAutostart as EventListener);
    
    return () => {
      window.removeEventListener('project-autostart', handleAutostart as EventListener);
    };
  }, [projectId]);

  const initializeAIStreaming = () => {
    // Connect to AI streaming service
    aiStreamingService.connect(projectId);
    
    // Subscribe to file changes
    const unsubscribeFiles = aiStreamingService.subscribeToFiles((file) => {
      console.log('📁 Live file update:', file);
      setLiveFiles(prev => ({
        ...prev,
        [file.filename]: file.content
      }));
    });

    // Subscribe to generation messages
    const unsubscribeGeneration = aiStreamingService.subscribeToGeneration((message) => {
      console.log('💬 Generation message:', message);
      setGenerationMessages(prev => [...prev, message]);
    });

    // Subscribe to status updates
    const unsubscribeStatus = aiStreamingService.subscribeToStatus((status) => {
      console.log('📊 AI Streaming status:', status);
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
    setIsLoading(true);
    setError(null);

    // Check if this is a generation request that should use streaming
    const isGenerationRequest = messageText.toLowerCase().includes('create') || 
                               messageText.toLowerCase().includes('generate') ||
                               messageText.toLowerCase().includes('build') ||
                               messageText.toLowerCase().includes('add feature') ||
                               messageText.toLowerCase().includes('implement');

    if (isGenerationRequest && streamingConnected) {
      // Use AI streaming for real-time file generation
      console.log('🎯 Using AI streaming for generation request');
      
      const success = aiStreamingService.startGeneration(messageText);
      if (success) {
        setIsLoading(false);
        return; // Let the streaming service handle the response
      } else {
        console.warn('⚠️ AI streaming not available, falling back to regular chat');
      }
    }

    // Fallback to regular chat API
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
                  {formatTimestamp(message.timestamp)}
                </span>
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

        {/* Live Generation Section */}
        {isGenerating && (
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-white animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  🚀 Live AI Generation
                  <Badge variant="primary" size="sm">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse mr-2"></div>
                    STREAMING
                  </Badge>
                </h3>
                <p className="text-gray-400 text-sm">Generating files in real-time...</p>
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
