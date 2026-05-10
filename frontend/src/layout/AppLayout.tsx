import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, Youtube, Map as MapIcon, ChevronRight } from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Utility for merging tailwind classes safely
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { icon: LayoutDashboard, label: 'Home', path: '/' },
  { icon: MessageSquare, label: 'Chat Assistant', path: '/chat' },
  { icon: MapIcon, label: 'Roadmap Builder', path: '/roadmap' },
];

export const AppLayout = () => {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-midnight-950 text-slate-200 overflow-hidden relative">
      
      {/* Sidebar */}
      <aside className="relative w-64 border-r border-slate-800/50 bg-midnight-900/60 backdrop-blur-xl flex flex-col z-20">
        <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
          <div className="flex items-center gap-3">
            <h1 className="font-semibold tracking-tight text-lg text-slate-100">EduAgent</h1>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group",
                  isActive 
                    ? "bg-electric-500/10 text-electric-400 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] ring-1 ring-electric-500/20" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                )}
              >
                <Icon className={cn("w-4 h-4", isActive ? "text-electric-400" : "text-slate-400 group-hover:text-slate-300")} />
                {item.label}
                {isActive && (
                  <ChevronRight className="w-4 h-4 ml-auto text-electric-500/50" />
                )}
              </NavLink>
            )
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative h-screen overflow-hidden bg-transparent">
        {/* Background Effects Container - Isolated to prevent overflow into sidebar */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-20%] left-[-10%] w-[140%] h-[50%] bg-mesh opacity-40 -z-10" />
          <div className="absolute bottom-0 right-0 w-[50vw] h-[50vh] bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-electric-900/20 via-midnight-950/0 to-transparent -z-10" />
        </div>
        
        {/* Page Content */}
        <div className="relative z-10 flex-1 flex flex-col overflow-hidden">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
