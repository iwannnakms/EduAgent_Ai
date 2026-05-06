import React, { createContext, useContext, useState, ReactNode } from 'react';
import { RAGSource } from '../api/client';

export interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: RAGSource[];
  timestamp: Date;
  isComplete?: boolean; // Track if typing animation is finished
}

interface ChatContextType {
  activeContextId: string;
  setActiveContextId: (id: string) => void;
  contexts: string[];
  addContext: (id: string) => void;
  // Messages are stored as { [contextId]: Message[] }
  messageHistory: Record<string, Message[]>;
  addMessage: (contextId: string, message: Message) => void;
  markMessageComplete: (contextId: string, messageId: string) => void;
  markAllComplete: (contextId: string) => void;
  clearHistory: (contextId: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [activeContextId, setActiveContextId] = useState<string>(''); // '' means "All Documents"
  const [contexts, setContexts] = useState<string[]>(['General', 'Research', 'Lectures']);
  const [messageHistory, setMessageHistory] = useState<Record<string, Message[]>>({
    '': [],
    'General': [],
    'Research': [],
    'Lectures': []
  });

  const addContext = (id: string) => {
    if (!contexts.includes(id)) {
      setContexts(prev => [...prev, id]);
      setMessageHistory(prev => ({ ...prev, [id]: [] }));
    }
  };

  const addMessage = (contextId: string, message: Message) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: [...(prev[contextId] || []), message]
    }));
  };

  const markMessageComplete = (contextId: string, messageId: string) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: (prev[contextId] || []).map(msg => 
        msg.id === messageId ? { ...msg, isComplete: true } : msg
      )
    }));
  };

  const markAllComplete = (contextId: string) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: (prev[contextId] || []).map(msg => ({ ...msg, isComplete: true }))
    }));
  };

  const clearHistory = (contextId: string) => {
    setMessageHistory(prev => ({ ...prev, [contextId]: [] }));
  };

  return (
    <ChatContext.Provider value={{ 
      activeContextId, 
      setActiveContextId, 
      contexts, 
      addContext, 
      messageHistory, 
      addMessage,
      markMessageComplete,
      markAllComplete,
      clearHistory
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
