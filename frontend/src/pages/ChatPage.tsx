import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Plus, Paperclip, Mic, Bot, User, Trash2, Sidebar as SidebarIcon, Search, Database, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type RAGSource } from '../api/client';
import { cn } from '../layout/AppLayout';
import { useChat, type Message } from '../context/ChatContext';
import { TypewriterMessage } from '../components/TypewriterMessage';

export const ChatPage = () => {
  const { 
    activeContextId, 
    setActiveContextId, 
    contexts, 
    addContext, 
    messageHistory, 
    addMessage,
    markMessageComplete,
    markAllComplete,
    clearHistory 
  } = useChat();

  const [input, setInput] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingContext, setIsCreatingContext] = useState(false);
  const [newContextName, setNewContextName] = useState('');
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isAutoScrolling = useRef(false);

  const [isAtBottom, setIsAtBottom] = useState(true);
  const messages = messageHistory[activeContextId] || [];

  const handleScroll = useCallback(() => {
    if (!scrollRef.current || isAutoScrolling.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setIsAtBottom(scrollHeight - scrollTop - clientHeight < 25);
  }, []);

  const scrollToBottom = useCallback((force = false) => {
    if (scrollRef.current && (isAtBottom || force)) {
      isAutoScrolling.current = true;
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setTimeout(() => { isAutoScrolling.current = false; }, 50);
    }
  }, [isAtBottom]);

  // Handle auto-scroll on new messages
  useEffect(() => {
    scrollToBottom(true);
  }, [activeContextId, messages.length, scrollToBottom]);

  const handleAddContext = () => {
    if (newContextName.trim()) {
      addContext(newContextName.trim());
      setActiveContextId(newContextName.trim());
      setNewContextName('');
      setIsCreatingContext(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const targetContext = activeContextId || 'General';
    addMessage(activeContextId, {
      id: `up-${Date.now()}`,
      role: 'bot',
      content: `Uploading ${file.name}...`,
      timestamp: new Date(),
      isComplete: true
    });

    try {
      const task = await api.submitRagFileIngest(targetContext, file);
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.pollRagTask(task.task_id);
          if (status.status === 'SUCCESS') {
            clearInterval(pollInterval);
            addMessage(activeContextId, {
              id: `success-${Date.now()}`,
              role: 'bot',
              content: `Ready! ${file.name} is indexed.`,
              timestamp: new Date(),
              isComplete: true
            });
          } else if (status.status === 'FAILURE') {
            clearInterval(pollInterval);
            addMessage(activeContextId, {
              id: `fail-${Date.now()}`,
              role: 'bot',
              content: `Error indexing ${file.name}.`,
              timestamp: new Date(),
              isComplete: true
            });
          }
        } catch { clearInterval(pollInterval); }
      }, 2000);
    } catch {
      addMessage(activeContextId, { id: `err-${Date.now()}`, role: 'bot', content: "Upload failed.", timestamp: new Date(), isComplete: true });
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    addMessage(activeContextId, { id: Date.now().toString(), role: 'user', content: input, timestamp: new Date(), isComplete: true });
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.queryRag(input, activeContextId || undefined);
      addMessage(activeContextId, {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
        isComplete: false
      });
    } catch {
      addMessage(activeContextId, { id: `err-${Date.now()}`, role: 'bot', content: "Brain disconnected. Try again.", timestamp: new Date(), isComplete: true });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full relative overflow-hidden bg-transparent">
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 280, opacity: 1 }} exit={{ width: 0, opacity: 0 }} className="border-r border-slate-800/40 bg-midnight-900/30 backdrop-blur-md flex flex-col hidden lg:flex">
            <div className="p-4 border-b border-slate-800/40 space-y-2">
              {isCreatingContext ? (
                <div className="space-y-2">
                  <input autoFocus value={newContextName} onChange={(e) => setNewContextName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleAddContext()} placeholder="Context name..." className="w-full bg-slate-900/50 border-slate-700/50 px-3 py-2 rounded-lg text-xs text-slate-200 focus:ring-electric-500/50" />
                  <div className="flex gap-2">
                    <button onClick={handleAddContext} className="flex-1 py-1.5 bg-electric-600 rounded-lg text-[10px] font-bold uppercase tracking-wider text-white">Save</button>
                    <button onClick={() => setIsCreatingContext(false)} className="flex-1 py-1.5 bg-slate-800 rounded-lg text-[10px] font-bold uppercase tracking-wider text-slate-400">Cancel</button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setIsCreatingContext(true)} className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl border border-slate-700 bg-slate-800/40 hover:bg-slate-800/60 transition-colors text-sm font-medium text-slate-200">
                  <Plus className="w-4 h-4" /> New Context
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              <div className="px-2 py-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Contexts</div>
              <div className={cn("flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm group", activeContextId === '' ? "bg-electric-600/20 text-electric-400 ring-1 ring-electric-500/30" : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200")} onClick={() => setActiveContextId('')}>
                <Database className="w-4 h-4 group-hover:scale-110 transition-transform" /> All Documents
              </div>
              {contexts.map((ctx) => (
                <div key={ctx} className={cn("flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm group", activeContextId === ctx ? "bg-electric-600/20 text-electric-400 ring-1 ring-electric-500/30" : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200")} onClick={() => setActiveContextId(ctx)}>
                  <Search className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  <span className="truncate">{ctx}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-16 flex items-center px-6 border-b border-slate-800/40 bg-midnight-950/20 backdrop-blur-sm z-10">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 -ml-2 text-slate-400 hover:text-slate-200 rounded-lg"><SidebarIcon className="w-5 h-5" /></button>
          <div className="ml-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-electric-500/10 flex items-center justify-center border border-electric-500/20"><Bot className="w-4 h-4 text-electric-400" /></div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">RAG Assistant</h2>
              <p className="text-[11px] text-slate-500 flex items-center gap-1.5">Context: <span className="text-electric-400/80 font-medium">{activeContextId || 'All Documents'}</span></p>
            </div>
          </div>
        </header>

        <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-6 space-y-8">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40 py-20">
              <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mb-6"><MessageSquare className="w-8 h-8 text-slate-400" /></div>
              <h3 className="text-xl font-medium text-slate-200 mb-2">How can I help you today?</h3>
              <p className="max-w-sm text-sm">Context: "{activeContextId || 'All Documents'}"</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={cn("flex items-start gap-4 max-w-4xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "flex-row")}>
                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg", msg.role === 'user' ? "bg-electric-600" : "bg-slate-800 border border-slate-700")}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-electric-400" />}
                </div>
                <div className="flex flex-col gap-2 group max-w-[85%]">
                  <div className={cn("px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm min-w-[50px]", msg.role === 'user' ? "bg-electric-600 text-white rounded-tr-none" : "glass-card text-slate-200 rounded-tl-none border-slate-700/50")}>
                    {msg.role === 'bot' ? (
                      <TypewriterMessage content={msg.content} isAlreadyComplete={msg.isComplete} onComplete={() => markMessageComplete(activeContextId, msg.id)} onHeightChange={scrollToBottom} />
                    ) : ( msg.content )}
                  </div>
                  {msg.isComplete && msg.sources && msg.sources.length > 0 && (
                    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.12 } } }} className="mt-6 space-y-3 max-w-2xl">
                      <motion.div variants={{ hidden: { opacity: 0, x: -5 }, show: { opacity: 1, x: 0 } }} className="flex items-center gap-2 px-1 mb-2">
                        <Database className="w-3 h-3 text-slate-500" />
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Referenced Sources</p>
                      </motion.div>
                      {msg.sources.slice(0, 3).map((source, i) => (
                        <motion.div key={i} variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }} className="group/source relative glass-card p-3.5 border-slate-800/40 hover:border-electric-500/30 transition-all duration-300">
                          <div className="absolute -left-2 top-3.5 w-1 h-6 bg-slate-800 group-hover/source:bg-electric-500 rounded-full transition-colors" />
                          <p className="text-[11px] leading-relaxed text-slate-400 italic group-hover/source:text-slate-300 transition-colors">"{String(source.text)}"</p>
                          {!!source.metadata?.filename && <div className="mt-2.5 flex items-center gap-1.5 opacity-60"><Search className="w-2.5 h-2.5 text-electric-400" /><span className="text-[9px] font-semibold text-slate-500 truncate italic">Source: {typeof source.metadata.filename === 'string' ? source.metadata.filename : 'Document'}</span></div>}
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex items-start gap-4 max-w-4xl mx-auto">
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0"><Bot className="w-5 h-5 text-electric-400" /></div>
              <div className="glass-card px-5 py-4 rounded-2xl rounded-tl-none border-slate-700/50">
                <div className="flex gap-1.5">
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60" />
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60" />
                  <motion.span animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-1.5 h-1.5 rounded-full bg-electric-500/60" />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 pt-0 bg-transparent">
          <div className="max-w-4xl mx-auto relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-electric-600/30 to-electric-400/30 rounded-2xl blur opacity-30 group-focus-within:opacity-60 transition-opacity" />
            <div className="relative glass-panel rounded-2xl border-slate-700/50 overflow-hidden">
              <div className="flex items-center px-4 py-3">
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".txt,.pdf" />
                <button onClick={() => fileInputRef.current?.click()} className="p-2 text-slate-500 hover:text-slate-200 transition-colors" title="Upload Document"><Paperclip className="w-5 h-5" /></button>
                <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder={`Ask about ${activeContextId || 'All Documents'}...`} className="flex-1 bg-transparent border-none focus:ring-0 text-slate-200 text-sm py-2 px-3" />
                <button onClick={handleSend} disabled={!input.trim() || isLoading} className={cn("p-2.5 rounded-xl transition-all ml-2", input.trim() && !isLoading ? "bg-electric-600 text-white shadow-lg shadow-electric-500/20 scale-100 hover:scale-105" : "bg-slate-800 text-slate-600 cursor-not-allowed")}><Send className="w-4 h-4" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
