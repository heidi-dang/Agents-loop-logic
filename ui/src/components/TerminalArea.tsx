import React from 'react';
import { Terminal, Construction, ArrowRight } from 'lucide-react';

interface TerminalAreaProps {
  onOpenMobileMenu?: () => void;
}

export const TerminalArea: React.FC<TerminalAreaProps> = ({ onOpenMobileMenu }) => {
  return (
    <div className="flex flex-col h-full bg-transparent overflow-hidden">
      {/* Header */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-4 md:px-8 bg-black/40 backdrop-blur-xl shrink-0 z-10 sticky top-0">
        <div className="flex items-center gap-3">
          <button 
            onClick={onOpenMobileMenu} 
            className="md:hidden p-2.5 text-[#71717a] hover:text-white transition-all active:scale-90"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <div className="flex items-center gap-3">
            <Terminal size={20} className="text-[#1d9bf0] hidden xs:block" />
            <h2 className="font-black text-xs tracking-[0.2em] text-white uppercase">Terminal</h2>
          </div>
        </div>
      </header>

      {/* Content - Placeholder */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-24 h-24 bg-[#1d9bf0]/10 border border-[#1d9bf0]/20 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-2xl">
          <Construction size={48} className="text-[#1d9bf0]" />
        </div>
        
        <h3 className="text-2xl md:text-3xl font-black tracking-tighter text-white mb-4">
          Coming Soon
        </h3>
        
        <p className="text-[#71717a] text-sm max-w-md mx-auto mb-8 leading-relaxed">
          Heidi Terminal Connector is currently in development. 
          This feature will provide secure SSH access to your infrastructure 
          directly from the browser.
        </p>

        <div className="flex flex-col gap-3 max-w-sm w-full">
          <div className="flex items-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-left">
            <div className="w-2 h-2 rounded-full bg-[#10b981]" />
            <span className="text-sm text-slate-300">Secure SSH connections</span>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-left">
            <div className="w-2 h-2 rounded-full bg-[#10b981]" />
            <span className="text-sm text-slate-300">Multiple session support</span>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-left">
            <div className="w-2 h-2 rounded-full bg-[#10b981]" />
            <span className="text-sm text-slate-300">Agent-integrated commands</span>
          </div>
        </div>

        <div className="mt-8 text-xs text-[#71717a] font-mono">
          No SSH credentials are stored in the browser for this MVP release.
        </div>
      </div>

      {/* Footer */}
      <footer className="h-10 bg-black/40 backdrop-blur-xl border-t border-white/5 flex justify-between items-center text-[9px] text-[#71717a] font-black uppercase tracking-[0.3em] px-6 md:px-10 shrink-0">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-white/10" />
            Standby
          </span>
        </div>
        <div className="opacity-40 font-mono lowercase tracking-tighter">
          heidi_terminal_v0.1.0
        </div>
      </footer>
    </div>
  );
};

export default TerminalArea;
