import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { RAGSource } from '../api/client';

export interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: RAGSource[];
  timestamp: Date;
  isComplete?: boolean;
}

interface ChatContextType {
  activeContextId: string;
  setActiveContextId: (id: string) => void;
  contexts: string[];
  addContext: (id: string) => void;
  messageHistory: Record<string, Message[]>;
  addMessage: (contextId: string, message: Message) => void;
  markMessageComplete: (contextId: string, messageId: string) => void;
  markAllComplete: (contextId: string) => void;
  clearHistory: (contextId: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [activeContextId, setActiveContextId] = useState<string>('');
  const [contexts, setContexts] = useState<string[]>(['General', 'Research', 'Lectures']);
  const [messageHistory, setMessageHistory] = useState<Record<string, Message[]>>({
    '': [],
    'General': [],
    'Research': [],
    'Lectures': []
  });

  const addContext = useCallback((id: string) => {
    setContexts(prev => {
      if (prev.includes(id)) return prev;
      return [...prev, id];
    });
    setMessageHistory(prev => {
      if (prev[id]) return prev;
      return { ...prev, [id]: [] };
    });
  }, []);

  const addMessage = useCallback((contextId: string, message: Message) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: [...(prev[contextId] || []), message]
    }));
  }, []);

  const markMessageComplete = useCallback((contextId: string, messageId: string) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: (prev[contextId] || []).map(msg => 
        msg.id === messageId ? { ...msg, isComplete: true } : msg
      )
    }));
  }, []);

  const markAllComplete = useCallback((contextId: string) => {
    setMessageHistory(prev => ({
      ...prev,
      [contextId]: (prev[contextId] || []).map(msg => ({ ...msg, isComplete: true }))
    }));
  }, []);

  const clearHistory = useCallback((contextId: string) => {
    setMessageHistory(prev => ({ ...prev, [contextId]: [] }));
  }, []);

  const value = React.useMemo(() => ({
    activeContextId, 
    setActiveContextId, 
    contexts, 
    addContext, 
    messageHistory, 
    addMessage,
    markMessageComplete,
    markAllComplete,
    clearHistory
  }), [activeContextId, contexts, messageHistory, addContext, addMessage, markMessageComplete, markAllComplete, clearHistory]);

  return (
    <ChatContext.Provider value={value}>
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
