import React, { useState, useEffect, useRef } from 'react';
import { Upload, Send, FileText, Trash2, MessageSquare, File, X, AlertCircle } from 'lucide-react';


const LawyerRAGChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [chatHistory, setChatHistory] = useState([]);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const API_BASE = 'http://localhost:8000';

  // 滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取所有文档
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/documents`);
      if (response.ok) {
        const docs = await response.json();
        setDocuments(docs);
      }
    } catch (error) {
      console.error('获取文档失败:', error);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // 文件上传
  const handleFileUpload = async (file) => {
    if (!file) return;

    setIsUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', 'general');

      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setSelectedFile(null);
        await fetchDocuments();
        
        // 添加上传成功消息
        const uploadMessage = {
          id: Date.now(),
          type: 'system',
          content: `文档 "${result.filename}" 上传成功！`,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, uploadMessage]);
      } else {
        const error = await response.json();
        setError(error.detail || '上传失败');
      }
    } catch (error) {
      setError('上传失败，请检查网络连接');
    } finally {
      setIsUploading(false);
    }
  };

  // 文档查询
  const handleQuery = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsQuerying(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: inputMessage }),
      });

      if (response.ok) {
        const result = await response.json();
        const botMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: result.answer,
          sources: result.sources || [],
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, botMessage]);
        
        // 添加到聊天历史
        setChatHistory(prev => [...prev, { query: inputMessage, response: result.answer }]);
      } else {
        const error = await response.json();
        setError(error.detail || '查询失败');
      }
    } catch (error) {
      setError('查询失败，请检查网络连接');
    } finally {
      setIsQuerying(false);
      setInputMessage('');
    }
  };

  // 删除文档
  const handleDeleteDocument = async (documentId) => {
    try {
      const response = await fetch(`${API_BASE}/api/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchDocuments();
        const deleteMessage = {
          id: Date.now(),
          type: 'system',
          content: '文档删除成功',
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, deleteMessage]);
      } else {
        const error = await response.json();
        setError(error.detail || '删除失败');
      }
    } catch (error) {
      setError('删除失败，请检查网络连接');
    }
  };

  // 处理文件选择
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.name.endsWith('.pdf') || file.name.endsWith('.docx')) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('只支持 PDF 和 DOCX 文件');
      }
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
    {/* 左侧边栏（根据状态动态显示） */}
    {sidebarVisible && (
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      
        {/* 功能导航 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              对话
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'documents'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-4 h-4 mr-2" />
              文档
            </button>
          </div>
        </div>

        {/* 上半部分 - 文档管理 */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'documents' && (
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-800">文档管理</h3>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.document_id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center flex-1">
                      <File className="w-4 h-4 mr-2 text-blue-600" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-800 truncate">
                          {doc.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          ID: {doc.document_id}  {/* 显示 document_id */}
                        </p>
                        <p className="text-xs text-gray-500">
                          {doc.category} • {new Date(doc.upload_time).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.document_id)}
                      className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-800">文档对话</h3>
              <div className="space-y-2">
                <button
                  onClick={() => setMessages([])}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  新建对话
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 下半部分 - 聊天记录 */}
        <div className="border-t border-gray-200 p-4 h-48 overflow-y-auto">
          <h4 className="text-sm font-semibold mb-2 text-gray-600">聊天记录</h4>
          <div className="space-y-2">
            {chatHistory.slice(-5).map((chat, index) => (
              <div
                key={index}
                className="p-2 bg-gray-50 rounded text-xs cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={() => setInputMessage(chat.query)}
              >
                <p className="font-medium text-gray-800 truncate">{chat.query}</p>
                <p className="text-gray-500 truncate">{chat.response.substring(0, 50)}...</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    )}

    {/* 边栏切换按钮，居于边栏右侧与对话区域之间 */}
    <div className="w-5 flex items-center justify-center bg-gray-100">
      <button
        onClick={() => setSidebarVisible(!sidebarVisible)}
        className="w-4 h-20 bg-white border border-gray-300 rounded-md shadow hover:bg-gray-200 text-xs"
      >
        {sidebarVisible ? '<' : '>'}
      </button>
    </div>

      {/* 右侧对话区域 */}
      <div className="flex-1 flex flex-col">
        {/* 标题栏 */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h1 className="text-xl font-semibold text-gray-800">律师事务所RAG系统</h1>
          <p className="text-sm text-gray-600">基于文档的智能问答系统</p>
        </div>

        {/* 消息区域 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-gray-50 to-white">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-20">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>上传文档开始对话</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className="flex items-end space-x-2">
                    {/* 如果是 assistant 显示头像 */}
                    {message.type !== 'user' && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-sm font-bold shadow">
                        AI
                      </div>
                    )}

                    {/* 气泡内容 */}
                    <div
                      className={`max-w-lg px-4 py-3 rounded-2xl shadow-md whitespace-pre-wrap break-words leading-relaxed text-sm
                        ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : message.type === 'system'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800 rounded-bl-none'
                        }`}
                    >
                      <div>{message.content}</div>

                      {/* 参考来源 */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-2 text-xs opacity-80 border-t border-gray-200 pt-2">
                          <p className="font-semibold mb-1">📚 参考来源:</p>
                          {message.sources.map((source, index) => (
                            <div key={index} className="mb-1">
                              <p className="font-medium text-blue-700">📄 {source.filename}</p>
                              <p className="text-gray-600 line-clamp-3">{source.preview}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* 时间戳 */}
                      <div className="text-[11px] text-gray-400 text-right mt-1">{message.timestamp}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>


        {/* 输入区域 */}
        <div className="bg-white border-t border-gray-200 p-4">
          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
              <span className="text-red-700 text-sm">{error}</span>
              <button
                onClick={() => setError('')}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* 文件上传区域 */}
          {selectedFile && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <File className="w-4 h-4 text-blue-600 mr-2" />
                  <span className="text-sm text-blue-800">{selectedFile.name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleFileUpload(selectedFile)}
                    disabled={isUploading}
                    className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {isUploading ? '上传中...' : '上传'}
                  </button>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 输入框 */}
          <div className="flex items-center space-x-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".pdf,.docx"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <Upload className="w-5 h-5" />
            </button>
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                placeholder="输入您的问题..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isQuerying}
              />
            </div>
            <button
              onClick={handleQuery}
              disabled={isQuerying || !inputMessage.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isQuerying ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LawyerRAGChat;