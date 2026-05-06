import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TypewriterMessageProps {
  content: string;
  speed?: number;
  onComplete?: () => void;
  onHeightChange?: () => void;
  isAlreadyComplete?: boolean;
}

export const TypewriterMessage: React.FC<TypewriterMessageProps> = ({ 
  content, 
  speed = 15, 
  onComplete,
  onHeightChange,
  isAlreadyComplete = false
}) => {
  const [displayedContent, setDisplayedContent] = useState(isAlreadyComplete ? content : '');
  const [isTyping, setIsTyping] = useState(!isAlreadyComplete);
  const containerRef = useRef<HTMLDivElement>(null);

  // Use a ref for the latest content to avoid effect re-runs
  const contentRef = useRef(content);
  useEffect(() => { contentRef.current = content; }, [content]);

  useEffect(() => {
    if (isAlreadyComplete) return;

    let index = 0;
    const timer = setInterval(() => {
      if (index < contentRef.current.length) {
        setDisplayedContent((prev) => prev + contentRef.current.charAt(index));
        index++;
        if (onHeightChange) onHeightChange();
      } else {
        clearInterval(timer);
        setIsTyping(false);
        if (onComplete) onComplete();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [isAlreadyComplete, speed, onComplete, onHeightChange]);

  return (
    <div ref={containerRef} className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-900/50 prose-pre:border prose-pre:border-slate-800 prose-li:my-1">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {displayedContent}
      </ReactMarkdown>
      {isTyping && (
        <span className="inline-block w-1.5 h-4 ml-1 bg-electric-500 animate-pulse align-middle" />
      )}
    </div>
  );
};
