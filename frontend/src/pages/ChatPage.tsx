import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, Paperclip, Mic, Bot, User, Trash2, Sidebar as SidebarIcon, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type RAGQueryResponse, type RAGSource } from '../api/client';
import { cn } from '../layout/AppLayout';

interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: RAGSource[];
  timestamp: Date;
}

export const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [documentId, setDocumentId] = useState('doc-001');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.queryRag(input, documentId);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: "Sorry, I encountered an error processing your request. Please check your connection and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full relative overflow-hidden bg-transparent">
      
      {/* Collapsible History Sidebar */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-r border-slate-800/40 bg-midnight-900/30 backdrop-blur-md flex flex-col hidden lg:flex"
          >
            <div className="p-4 border-b border-slate-800/40">
              <button className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl border border-slate-700 bg-slate-800/40 hover:bg-slate-800/60 transition-colors text-sm font-medium">
                <Plus className="w-4 h-4" />
                New Chat
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              <div className="px-2 py-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Recent Documents</div>
              <div 
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm",
                  documentId === 'doc-001' ? "bg-electric-600/20 text-electric-400 ring-1 ring-electric-500/30" : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200"
                )}
                onClick={() => setDocumentId('doc-001')}
              >
                <Search className="w-4 h-4" />
                doc-001
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Window */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        
        {/* Chat Header */}
        <header className="h-16 flex items-center px-6 border-b border-slate-800/40 bg-midnight-950/20 backdrop-blur-sm z-10">
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 -ml-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 rounded-lg transition-all"
          >
            <SidebarIcon className="w-5 h-5" />
          </button>
          <div className="ml-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-electric-500/10 flex items-center justify-center border border-electric-500/20">
              <Bot className="w-4 h-4 text-electric-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">RAG Assistant</h2>
              <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                Active Context: <span className="text-electric-400/80 font-medium">{documentId}</span>
              </p>
            </div>
          </div>
          <button className="ml-auto p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-all">
            <Trash2 className="w-5 h-5" />
          </button>
        </header>

        {/* Messages Container */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 space-y-8"
        >
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40 py-20">
              <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mb-6">
                <MessageSquare className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-xl font-medium text-slate-200 mb-2">How can I help you today?</h3>
              <p className="max-w-sm text-sm">Ask me anything about your ingested documents. Switch contexts in the sidebar.</p>
            </div>
          ) : (
            messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex items-start gap-4 max-w-4xl mx-auto",
                  msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg",
                  msg.role === 'user' ? "bg-electric-600 shadow-electric-500/20" : "bg-slate-800 border border-slate-700 shadow-black/20"
                )}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-electric-400" />}
                </div>
                
                <div className="flex flex-col gap-2 group">
                  <div className={cn(
                    "px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm",
                    msg.role === 'user' 
                      ? "bg-electric-600 text-white rounded-tr-none" 
                      : "glass-card text-slate-200 rounded-tl-none border-slate-700/50"
                  )}>
                    {msg.content}
                  </div>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 space-y-2 max-w-lg">
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest pl-1">Sources</p>
                      <div className="grid grid-cols-1 gap-2">
                        {msg.sources.slice(0, 3).map((source, i) => (
                          <div key={i} className="text-[11px] bg-slate-900/40 border border-slate-800/60 p-2 rounded-lg text-slate-400 line-clamp-2 italic">
                            "{source.text}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <span className="text-[10px] text-slate-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity px-1">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </motion.div>
            ))
          )}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-start gap-4 max-w-4xl mx-auto"
            >
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-electric-400" />
              </div>
              <div className="glass-card px-5 py-4 rounded-2xl rounded-tl-none border-slate-700/50">
                <div className="flex gap-1.5">
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60"></motion.span>
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60"></motion.span>
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60"></motion.span>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-6 pt-0 bg-transparent">
          <div className="max-w-4xl mx-auto relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-electric-600/30 to-electric-400/30 rounded-2xl blur opacity-30 group-focus-within:opacity-60 transition-opacity"></div>
            <div className="relative glass-panel rounded-2xl border-slate-700/50 overflow-hidden">
              <div className="flex items-center px-4 py-3">
                <button className="p-2 text-slate-500 hover:text-slate-200 transition-colors">
                  <Paperclip className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder={`Ask doc-agent about ${documentId}...`}
                  className="flex-1 bg-transparent border-none focus:ring-0 text-slate-200 text-sm py-2 px-3"
                />
                <button className="p-2 text-slate-500 hover:text-slate-200 transition-colors">
                  <Mic className="w-5 h-5" />
                </button>
                <button 
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className={cn(
                    "p-2.5 rounded-xl transition-all ml-2",
                    input.trim() && !isLoading 
                      ? "bg-electric-600 text-white shadow-lg shadow-electric-500/20 scale-100 hover:scale-105" 
                      : "bg-slate-800 text-slate-600 scale-95 cursor-not-allowed"
                  )}
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
            <p className="text-[10px] text-center text-slate-600 mt-3 font-medium">
              EduAgent AI can make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const MessageSquare = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);
