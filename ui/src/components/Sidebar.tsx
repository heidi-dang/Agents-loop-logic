
import React from 'react';
import { AppView, User } from '../types';
import { MessageSquare, Terminal as TerminalIcon, Settings, Plus, Bot, PanelLeft, X, Activity } from 'lucide-react';

interface SidebarProps {
  currentView: AppView;
  isAgentMode: boolean;
  onToggleAgentMode: () => void;
  onSelectView: (view: AppView) => void;
  onOpenSettings: () => void;
  onNewChat: () => void;
  isCollapsed: boolean;
  onToggleCollapse: (collapsed: boolean) => void;
  user?: User;
  isMobileOpen: boolean;
  onMobileClose: () => void;
  backendStatus?: 'checking' | 'connected' | 'disconnected';
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  isAgentMode,
  onToggleAgentMode,
  onSelectView,
  onOpenSettings,
  onNewChat,
  isCollapsed,
  onToggleCollapse,
  user,
  isMobileOpen,
  onMobileClose,
  backendStatus = 'checking'
}) => {
  const sidebarClasses = `
    fixed inset-y-0 left-0 z-[100] glass-panel transition-all duration-500 ease-in-out
    md:static md:translate-x-0 ${isCollapsed ? 'md:w-20' : 'md:w-64'}
    ${isMobileOpen ? 'translate-x-0 w-[85%] sm:w-72 shadow-[0_0_120px_rgba(0,0,0,1)]' : '-translate-x-full md:translate-x-0'}
    flex flex-col h-full glow-frame border-r border-white/5 md:m-3 md:rounded-[2.5rem]
  `;

  const NavButton = ({ 
    active, 
    onClick, 
    icon: Icon, 
    label, 
    colorClass = "text-white", 
    activeBg = "bg-white/10 border-white/10 shadow-lg shadow-black/40",
    idleText = "text-grok-muted"
  }: { 
    active: boolean, 
    onClick: () => void, 
    icon: any, 
    label: string, 
    colorClass?: string,
    activeBg?: string,
    idleText?: string
  }) => (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-4 p-2 rounded-2xl transition-all group/btn ${isCollapsed && !isMobileOpen ? 'justify-center' : ''}`}
    >
      <div className={`w-11 h-11 flex items-center justify-center rounded-xl border transition-all shrink-0 ${active ? `${activeBg} ${colorClass}` : `border-transparent ${idleText} group-hover/btn:bg-white/5 group-hover/btn:text-white`}`}>
        <Icon size={20} />
      </div>
      {(!isCollapsed || isMobileOpen) && (
        <span className={`text-[14px] font-bold tracking-tight transition-colors ${active ? colorClass : `${idleText} group-hover/btn:text-white`}`}>
          {label}
        </span>
      )}
    </button>
  );

  return (
    <>
      <div 
        className={`fixed inset-0 bg-black/50 backdrop-blur-md z-[95] md:hidden transition-opacity duration-500 ${isMobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onMobileClose}
      />

      <aside className={sidebarClasses}>
        <div className="flex items-center justify-between p-6 mb-2 shrink-0 relative">
          <div className={`flex items-center gap-3 ${isCollapsed && !isMobileOpen ? 'md:justify-center' : ''}`}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center transition-transform hover:scale-105 active:scale-95 cursor-pointer shadow-lg shadow-purple-500/20">
              <Activity size={20} className="text-white" />
            </div>
            {(!isCollapsed || isMobileOpen) && (
              <div className="flex flex-col">
                <h1 className="font-bold text-lg text-white leading-none tracking-tight">HEIDI</h1>
                <span className="text-[8px] text-white/40 font-black tracking-[0.2em] uppercase mt-1">AI Interface</span>
              </div>
            )}
          </div>
          <button onClick={onMobileClose} className="md:hidden p-2 text-grok-muted hover:text-white transition-colors">
            <X size={20} />
          </button>
          <button 
            onClick={() => onToggleCollapse(!isCollapsed)}
            className="hidden md:flex absolute -right-3.5 top-8 p-1.5 bg-black/80 backdrop-blur-xl border border-white/10 rounded-full text-grok-muted hover:text-white transition-all z-50 hover:border-white/20 group shadow-lg"
          >
            <PanelLeft size={14} className={`${isCollapsed ? 'rotate-180' : ''} transition-transform duration-500`} />
          </button>
        </div>

        {/* Backend Status Indicator */}
        <div className={`px-4 mb-2 ${isCollapsed && !isMobileOpen ? 'md:hidden' : ''}`}>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
            backendStatus === 'connected' 
              ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
              : backendStatus === 'disconnected'
              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
              : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
          }`}>
            <div className={`w-1.5 h-1.5 rounded-full ${
              backendStatus === 'connected' 
                ? 'bg-green-400 animate-pulse' 
                : backendStatus === 'disconnected'
                ? 'bg-red-400'
                : 'bg-yellow-400 animate-pulse'
            }`} />
            {backendStatus === 'connected' ? 'Connected' : backendStatus === 'disconnected' ? 'Offline' : 'Checking...'}
          </div>
        </div>

        <div className="px-4 py-2 mb-4 shrink-0">
          <button
            onClick={onNewChat}
            disabled={backendStatus !== 'connected'}
            className={`w-full flex items-center gap-3 bg-white text-black rounded-full font-black text-[13px] tracking-tight transition-all hover:bg-white/90 active:scale-95 shadow-[0_8px_30px_rgba(255,255,255,0.15)] disabled:opacity-50 disabled:cursor-not-allowed ${isCollapsed && !isMobileOpen ? 'md:justify-center md:h-12 md:w-12 md:p-0' : 'px-5 py-3.5'}`}
          >
            <Plus size={20} />
            {(!isCollapsed || isMobileOpen) && <span>New Session</span>}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-4 space-y-1.5 custom-scrollbar">
          <NavButton 
            active={currentView === AppView.CHAT}
            onClick={() => onSelectView(AppView.CHAT)}
            icon={MessageSquare}
            label="Chat"
          />
          <NavButton 
            active={currentView === AppView.TERMINAL}
            onClick={() => onSelectView(AppView.TERMINAL)}
            icon={TerminalIcon}
            label="Terminal"
          />
          <NavButton 
            active={currentView === AppView.AGENT}
            onClick={() => onSelectView(AppView.AGENT)}
            icon={Bot}
            label="Agent"
            colorClass="text-grok-success"
            activeBg="bg-grok-success/10 border-grok-success/20 shadow-lg shadow-black/40"
          />
        </nav>

        <div className="p-4 border-t border-white/5 space-y-3 shrink-0 mt-auto">
          {user && (
            <div className={`p-2.5 bg-white/[0.03] rounded-[1.5rem] border border-white/5 group/user hover:border-white/20 transition-all cursor-default overflow-hidden relative ${isCollapsed && !isMobileOpen ? 'flex justify-center' : ''}`}>
              <div className="absolute top-0 right-0 w-16 h-16 bg-white/5 blur-xl opacity-0 group-hover/user:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-3 relative z-10">
                <img src={user.image || ''} alt={user.name || ''} className="w-9 h-9 rounded-full border border-white/10 transition-transform group-hover/user:scale-105" />
                {(!isCollapsed || isMobileOpen) && (
                  <div className="min-w-0">
                    <p className="text-[8px] text-[#71717a] font-black uppercase tracking-[0.2em] mb-0.5">Operator</p>
                    <p className="text-[13px] font-bold text-white truncate leading-none">{user.name}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <button 
            onClick={onOpenSettings}
            className={`w-full flex items-center gap-4 p-2 text-grok-muted hover:text-white transition-all rounded-2xl group/settings ${isCollapsed && !isMobileOpen ? 'justify-center' : ''}`}
          >
            <div className="w-11 h-11 flex items-center justify-center rounded-xl border border-transparent transition-all group-hover/settings:bg-white/5">
              <Settings size={20} />
            </div>
            {(!isCollapsed || isMobileOpen) && <span className="text-[14px] font-bold">Settings</span>}
          </button>
        </div>
      </aside>
    </>
  );
};
