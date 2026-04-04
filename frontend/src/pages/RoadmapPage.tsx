import React, { useState } from 'react';
import { Map as MapIcon, GraduationCap, Clock, ChevronDown, ChevronUp, ExternalLink, Target, Loader2, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type RoadmapResponse, type RoadmapStep } from '../api/client';
import { cn } from '../layout/AppLayout';

export const RoadmapPage = () => {
  const [topic, setTopic] = useState('');
  const [level, setLevel] = useState('beginner');
  const [duration, setDuration] = useState(12);
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedStep, setExpandedStep] = useState<number | null>(1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsLoading(true);
    setError(null);
    setRoadmap(null);

    try {
      const data = await api.generateRoadmap(topic, level, duration);
      setRoadmap(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-10 relative">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-100 mb-2">Roadmap Builder</h1>
            <p className="text-slate-400">Generate a personalized learning path for any skill or topic.</p>
          </div>
          {roadmap && (
            <div className="flex items-center gap-4 text-sm bg-slate-900/50 p-2 px-4 rounded-xl border border-slate-800">
              <div className="flex items-center gap-1.5 text-slate-300">
                <Target className="w-4 h-4 text-electric-400" />
                {roadmap.learner_level}
              </div>
              <div className="w-1 h-1 rounded-full bg-slate-700"></div>
              <div className="flex items-center gap-1.5 text-slate-300">
                <Clock className="w-4 h-4 text-electric-400" />
                {roadmap.total_weeks} Weeks
              </div>
            </div>
          )}
        </div>

        {!roadmap ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-8"
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">What do you want to learn?</label>
                <div className="relative">
                  <MapIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input 
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Fullstack Web Development with React"
                    className="w-full bg-slate-900/50 border-slate-700/50 pl-12 py-3 rounded-xl focus:ring-electric-500/50 focus:border-electric-500 transition-all"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">Current Experience</label>
                  <div className="grid grid-cols-3 gap-2">
                    {['beginner', 'intermediate', 'advanced'].map((l) => (
                      <button
                        key={l}
                        type="button"
                        onClick={() => setLevel(l)}
                        className={cn(
                          "py-2 px-3 rounded-lg text-xs font-semibold capitalize transition-all border",
                          level === l 
                            ? "bg-electric-600 border-electric-500 text-white" 
                            : "bg-slate-900/50 border-slate-800 text-slate-500 hover:text-slate-300"
                        )}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">Target Duration (Weeks)</label>
                  <input 
                    type="range"
                    min="1"
                    max="52"
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    className="w-full accent-electric-500"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                    <span>1 Week</span>
                    <span className="text-electric-400">{duration} Weeks</span>
                    <span>1 Year</span>
                  </div>
                </div>
              </div>

              <button 
                type="submit"
                disabled={!topic.trim() || isLoading}
                className="w-full py-4 rounded-xl bg-electric-600 hover:bg-electric-500 text-white font-bold transition-all shadow-lg shadow-electric-500/20 flex items-center justify-center gap-3 group disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Build My Path
                    <Play className="w-4 h-4 group-hover:translate-x-1 transition-transform fill-current" />
                  </>
                )}
              </button>
            </form>
          </motion.div>
        ) : (
          <div className="relative pl-8 space-y-8">
            {/* The vertical connector line */}
            <div className="absolute left-4 top-4 bottom-4 w-0.5 bg-gradient-to-b from-electric-500 via-electric-500/40 to-transparent"></div>

            {roadmap.steps.map((step, index) => (
              <motion.div 
                key={step.step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {/* Step Marker */}
                <div className={cn(
                  "absolute -left-8 top-1 w-8 h-8 rounded-full border-4 border-midnight-950 flex items-center justify-center text-xs font-bold z-10 transition-colors",
                  expandedStep === step.step ? "bg-electric-500 text-white" : "bg-slate-800 text-slate-400"
                )}>
                  {step.step}
                </div>

                <div className={cn(
                  "glass-card overflow-hidden transition-all duration-300 group hover:border-slate-700",
                  expandedStep === step.step ? "ring-1 ring-electric-500/30" : "cursor-pointer"
                )}
                onClick={() => setExpandedStep(expandedStep === step.step ? null : step.step)}
                >
                  <div className="p-5 flex items-center justify-between">
                    <h3 className="font-bold text-slate-100 group-hover:text-electric-400 transition-colors">{step.title}</h3>
                    <div className="flex items-center gap-4">
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
                        {step.estimated_hours} Hours
                      </span>
                      {expandedStep === step.step ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                    </div>
                  </div>

                  <AnimatePresence>
                    {expandedStep === step.step && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="px-5 pb-6 border-t border-slate-800/50 pt-5 space-y-6"
                      >
                        <div className="grid md:grid-cols-2 gap-6">
                          <div>
                            <div className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">
                              <Target className="w-3 h-3" />
                              Learning Outcomes
                            </div>
                            <ul className="space-y-2">
                              {step.outcomes.map((outcome, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                                  <div className="w-1.5 h-1.5 rounded-full bg-electric-500/40 mt-1.5 flex-shrink-0" />
                                  {outcome}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">
                              <GraduationCap className="w-3 h-3" />
                              Recommended Resources
                            </div>
                            <div className="space-y-2">
                              {step.resources.map((resource, i) => (
                                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800 text-xs text-slate-300 group/res hover:border-slate-700 transition-colors">
                                  {resource}
                                  <ExternalLink className="w-3 h-3 text-slate-600 group-hover/res:text-electric-400 transition-colors" />
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}

            <button 
              onClick={() => setRoadmap(null)}
              className="mt-8 text-sm font-medium text-slate-500 hover:text-electric-400 transition-colors flex items-center gap-2"
            >
              ← Generate another roadmap
            </button>
          </div>
        )}

        {error && (
          <div className="glass-card border-rose-500/20 p-6 flex flex-col items-center text-center">
             <AlertCircle className="w-10 h-10 text-rose-500 mb-4" />
             <h3 className="text-lg font-bold text-slate-200 mb-1">Failed to build roadmap</h3>
             <p className="text-slate-400 text-sm max-w-xs">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

const AlertCircle = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);
