import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Terminal, 
  Shield, 
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Copy,
  Download,
  Trash2
} from 'lucide-react';
import { useAppSelector } from '../store/hooks';
import { useGetMCPToolsQuery, useExecuteMCPToolMutation, useAnalyzeWithLLMMutation } from '../store/api';
import { Card, Container } from '../components/layout';
import { Button, LoadingSpinner } from '../components/ui';
import { Input } from '../components/forms';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import type { ChatMessage, MCPTool, LLMResponse } from '../types';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  tool?: MCPTool;
  status?: 'pending' | 'success' | 'error';
  metadata?: any;
}

const Chat: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: toolsData, isLoading: toolsLoading } = useGetMCPToolsQuery();
  const [executeTool] = useExecuteMCPToolMutation();
  const [analyzeWithLLM] = useAnalyzeWithLLMMutation();

  const tools = toolsData?.data || [];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        type: 'system',
        content: 'Welcome to the SOC Agent Chat! I can help you with security analysis, run Kali tools, and provide AI-powered insights. What would you like to do?',
        timestamp: new Date(),
      }]);
    }
  }, [messages.length]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // First, try to analyze with LLM to understand intent
      const llmResponse = await analyzeWithLLM({
        message: inputValue,
        context: messages.slice(-5).map(m => ({ role: m.type, content: m.content })),
      }).unwrap();

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: llmResponse.response,
        timestamp: new Date(),
        metadata: llmResponse,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If LLM suggests a tool, execute it
      if (llmResponse.suggested_tool) {
        const tool = tools.find(t => t.name === llmResponse.suggested_tool);
        if (tool) {
          await handleExecuteTool(tool, llmResponse.tool_parameters || {});
        }
      }
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `Error: ${error?.data?.message || 'Failed to process message'}`,
        timestamp: new Date(),
        status: 'error',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteTool = async (tool: MCPTool, parameters: any = {}) => {
    const toolMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'tool',
      content: `Executing ${tool.name}...`,
      timestamp: new Date(),
      tool,
      status: 'pending',
    };

    setMessages(prev => [...prev, toolMessage]);

    try {
      const result = await executeTool({
        tool_name: tool.name,
        parameters,
      }).unwrap();

      const successMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'tool',
        content: `Tool execution completed successfully`,
        timestamp: new Date(),
        tool,
        status: 'success',
        metadata: result,
      };

      setMessages(prev => [...prev, successMessage]);

      // If there's output, add it as a separate message
      if (result.output) {
        const outputMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          type: 'assistant',
          content: result.output,
          timestamp: new Date(),
          metadata: result,
        };
        setMessages(prev => [...prev, outputMessage]);
      }
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'tool',
        content: `Tool execution failed: ${error?.data?.message || 'Unknown error'}`,
        timestamp: new Date(),
        tool,
        status: 'error',
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const downloadOutput = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([{
      id: '1',
      type: 'system',
      content: 'Chat cleared. How can I help you today?',
      timestamp: new Date(),
    }]);
  };

  const getMessageIcon = (message: ChatMessage) => {
    switch (message.type) {
      case 'user':
        return <User className="h-5 w-5 text-blue-500" />;
      case 'assistant':
        return <Bot className="h-5 w-5 text-green-500" />;
      case 'system':
        return <Shield className="h-5 w-5 text-purple-500" />;
      case 'tool':
        return <Terminal className="h-5 w-5 text-orange-500" />;
      default:
        return <Bot className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'pending':
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <Container>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SOC Agent Chat</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              AI-powered security analysis with Kali MCP tools
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              onClick={clearChat}
              className="flex items-center space-x-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear Chat
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Chat Messages */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start space-x-3 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type !== 'user' && (
                    <div className="flex-shrink-0">
                      {getMessageIcon(message)}
                    </div>
                  )}
                  
                  <div
                    className={`max-w-3xl px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'system'
                        ? 'bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100'
                        : message.type === 'tool'
                        ? 'bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium opacity-70">
                        {message.type === 'user' ? 'You' : 
                         message.type === 'assistant' ? 'AI Assistant' :
                         message.type === 'system' ? 'System' :
                         message.tool?.name || 'Tool'}
                      </span>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(message.status)}
                        <span className="text-xs opacity-70">
                          {format(message.timestamp, 'HH:mm')}
                        </span>
                      </div>
                    </div>
                    
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {message.metadata && (
                      <div className="mt-2 pt-2 border-t border-current border-opacity-20">
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(JSON.stringify(message.metadata, null, 2))}
                            className="text-xs"
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => downloadOutput(
                              JSON.stringify(message.metadata, null, 2),
                              `output-${message.id}.json`
                            )}
                            className="text-xs"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {message.type === 'user' && (
                    <div className="flex-shrink-0">
                      {getMessageIcon(message)}
                    </div>
                  )}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <Bot className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about security analysis, or request a Kali tool..."
                    disabled={isLoading}
                    className="resize-none"
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="flex items-center space-x-2"
                >
                  <Send className="h-4 w-4" />
                  Send
                </Button>
              </div>
            </div>
          </div>

          {/* Tools Sidebar */}
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Available Tools
            </h3>
            
            {toolsLoading ? (
              <LoadingSpinner size="md" text="Loading tools..." />
            ) : (
              <div className="space-y-2">
                {tools.map((tool) => (
                  <Card
                    key={tool.name}
                    padding="sm"
                    className={`cursor-pointer transition-colors ${
                      selectedTool?.name === tool.name
                        ? 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                    onClick={() => setSelectedTool(tool)}
                  >
                    <div className="flex items-center space-x-2">
                      <Terminal className="h-4 w-4 text-orange-500" />
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {tool.name}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {tool.description}
                        </p>
                      </div>
                    </div>
                    
                    {tool.parameters && tool.parameters.length > 0 && (
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        Parameters: {tool.parameters.map(p => p.name).join(', ')}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            )}

            {/* Quick Actions */}
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Quick Actions
              </h4>
              <div className="space-y-2">
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => setInputValue('Scan for vulnerabilities on 192.168.1.1')}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Vulnerability Scan
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => setInputValue('Analyze network traffic for suspicious activity')}
                >
                  <Zap className="h-4 w-4 mr-2" />
                  Network Analysis
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => setInputValue('Check system security posture')}
                >
                  <Shield className="h-4 w-4 mr-2" />
                  Security Check
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Container>
  );
};

export default Chat;
