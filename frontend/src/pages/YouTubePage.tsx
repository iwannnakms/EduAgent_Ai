import React, { useState } from 'react';
import { Youtube, Wand2, FileText, CheckCircle2, Loader2, AlertCircle, Database, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type TaskStatus } from '../api/client';
import { cn } from '../layout/AppLayout';

export const YouTubePage = () => {
  const [url, setUrl] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestSuccess, setIngestSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setError(null);
    setResult(null);
    setTaskId(null);
    setStatus('initializing');

    try {
      const data = await api.submitVideo(url, 'en', 500);
      setTaskId(data.task_id);
      startPolling(data.task_id);
    } catch (err: any) {
      setError(err.message);
      setStatus(null);
    }
  };

  const startPolling = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const data: TaskStatus = await api.pollVideoTask(id);
        setStatus(data.status);
        
        if (data.status === 'SUCCESS') {
          setResult(data.result);
          clearInterval(interval);
        } else if (data.status === 'FAILURE') {
          setError(data.error || 'Task failed');
          clearInterval(interval);
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 2000);
  };

  const handleIngestToRag = async () => {
    if (!url.trim()) return;
    setIsIngesting(true);
    setIngestSuccess(false);
    
    try {
      const documentId = `yt-${Date.now()}`;
      await api.submitRagYoutubeIngest(documentId, url);
      setIngestSuccess(true);
    } catch (err: any) {
      setError("RAG Ingestion failed: " + err.message);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-10 relative">
      <div className="max-w-4xl mx-auto space-y-10">
        
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-2">YouTube to Notes</h1>
          <p className="text-slate-400">Transform any educational video into structured study notes and chat-ready context.</p>
        </div>

        {/* Input Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-1 shadow-2xl shadow-electric-500/5"
        >
          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-3 p-2">
            <div className="flex-1 relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Youtube className={cn("w-5 h-5", url ? "text-red-500" : "text-slate-500")} />
              </div>
              <input 
                type="text" 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Paste YouTube URL (e.g., https://www.youtube.com/watch?v=...)"
                className="w-full bg-slate-900/50 border-slate-700/50 pl-12 py-3 rounded-xl focus:ring-electric-500/50 focus:border-electric-500 transition-all text-sm"
              />
            </div>
            <button 
              type="submit"
              disabled={!url.trim() || !!status && status !== 'SUCCESS' && status !== 'FAILURE'}
              className="px-6 py-3 rounded-xl bg-electric-600 hover:bg-electric-500 text-white font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap"
            >
              {status && status !== 'SUCCESS' && status !== 'FAILURE' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Wand2 className="w-4 h-4" />
              )}
              Generate Notes
            </button>
          </form>
        </motion.div>

        {/* Loading State */}
        <AnimatePresence>
          {status && status !== 'SUCCESS' && status !== 'FAILURE' && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card p-8 flex flex-col items-center justify-center text-center space-y-4"
            >
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-4 border-electric-500/20 border-t-electric-500 animate-spin"></div>
                <Youtube className="w-6 h-6 text-red-500 absolute inset-0 m-auto" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-200 capitalize">{status.replace('_', ' ')}...</h3>
                <p className="text-sm text-slate-500 max-w-xs mx-auto">
                  We're extracting the transcript and generating your study notes. This usually takes 30-60 seconds.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-rose-200">
              <p className="font-semibold mb-1">Processing Error</p>
              <p className="opacity-80">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700"
          >
            {/* Action Bar */}
            <div className="flex flex-wrap gap-3">
              <button 
                onClick={handleIngestToRag}
                disabled={isIngesting || ingestSuccess}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                  ingestSuccess 
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" 
                    : "bg-electric-600/10 text-electric-400 border border-electric-500/30 hover:bg-electric-600/20"
                )}
              >
                {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : (ingestSuccess ? <CheckCircle2 className="w-4 h-4" /> : <Database className="w-4 h-4" />)}
                {ingestSuccess ? "Ingested to RAG" : "Add to Chat Context"}
              </button>
              <button className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 text-sm font-medium hover:bg-slate-700 transition-all flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Export as PDF
              </button>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Summary Section */}
              <div className="glass-card p-6 space-y-4">
                <div className="flex items-center gap-2 text-electric-400 font-bold text-xs uppercase tracking-widest">
                  <Wand2 className="w-4 h-4" />
                  AI Summary
                </div>
                <div className="prose prose-invert max-w-none">
                  <p className="text-slate-200 leading-relaxed text-sm">
                    {result.summary}
                  </p>
                </div>
              </div>

              {/* Transcript Section */}
              <div className="glass-card p-6 space-y-4 max-h-[500px] flex flex-col">
                <div className="flex items-center gap-2 text-slate-400 font-bold text-xs uppercase tracking-widest">
                  <FileText className="w-4 h-4" />
                  Full Transcript
                </div>
                <div className="flex-1 overflow-y-auto pr-2">
                  <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-wrap">
                    {result.transcript}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Placeholder / Empty State */}
        {!status && !result && (
          <div className="grid md:grid-cols-2 gap-6 pt-10">
            <div className="glass-card p-6 border-dashed border-slate-700/50 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-4">
                <Youtube className="w-6 h-6 text-slate-500" />
              </div>
              <h4 className="text-slate-300 font-medium mb-1">Paste any URL</h4>
              <p className="text-xs text-slate-500">We support tutorials, lectures, and documentaries.</p>
            </div>
            <div className="glass-card p-6 border-dashed border-slate-700/50 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-4">
                <Database className="w-6 h-6 text-slate-500" />
              </div>
              <h4 className="text-slate-300 font-medium mb-1">Chat with Video</h4>
              <p className="text-xs text-slate-500">Once processed, ingest it to RAG for interactive Q&A.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
