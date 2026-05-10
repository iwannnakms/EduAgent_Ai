import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Zap, BrainCircuit, Search } from 'lucide-react';
import { motion } from 'framer-motion';

export const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Zap,
      title: 'Chat with Documents',
      description: 'Upload PDFs or text files to start an intelligent conversation with your content.',
    },
    {
      icon: BrainCircuit,
      title: 'Smart Roadmaps',
      description: 'Generate personalized learning paths with curated resources and direct study links.',
    },
    {
      icon: Search,
      title: 'Deep Research',
      description: 'Leverage AI to uncover insights and synthesize complex information from across your library.',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto relative h-full w-full">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-electric-500/10 border border-electric-500/20 text-electric-400 text-sm font-medium mb-8">
            <span className="w-2 h-2 rounded-full bg-electric-500 animate-pulse" />
            EduAgent 2.0 is live
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-slate-100 leading-tight">
            Learn smarter with <br/>
            <span className="text-gradient">Intelligent AI</span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Chat with your documents and build dynamic learning roadmaps with the most advanced AI agent.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button 
              onClick={() => navigate('/chat')}
              className="px-8 py-3.5 rounded-xl bg-electric-600 hover:bg-electric-500 text-white font-semibold transition-all shadow-[0_0_20px_rgba(124,58,237,0.3)] hover:shadow-[0_0_30px_rgba(124,58,237,0.5)] flex items-center gap-2 group w-full sm:w-auto justify-center"
            >
              Start Chatting
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>
      </div>

      {/* Features Section */}
      <div className="max-w-6xl mx-auto px-6 py-20 pb-32">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
              className="glass-card p-8 group hover:border-electric-500/30 transition-colors"
            >
              <div className="w-12 h-12 rounded-lg bg-electric-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <feature.icon className="w-6 h-6 text-electric-400" />
              </div>
              <h3 className="text-xl font-semibold text-slate-200 mb-3">{feature.title}</h3>
              <p className="text-slate-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
