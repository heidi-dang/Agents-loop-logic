
import React, { useRef } from 'react';
import { History, FolderOpen, FileText, X, Upload, Database, PanelRight } from 'lucide-react';
import { ChatSession, ProjectFile } from '../types';

interface RightSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  projectFiles: ProjectFile[];
  onSelectSession: (id: string) => void;
  onUploadFile: (file: File) => void;
  onRemoveFile: (id: string) => void;
  isOpen: boolean;
  onToggle: (open: boolean) => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  sessions, activeSessionId, projectFiles, onSelectSession, onUploadFile, onRemoveFile, isOpen, onToggle
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sidebarClasses = `
    fixed inset-y-0 right-0 z-[100] glass-panel transition-transform duration-500 ease-in-out
    md:static md:translate-x-0 ${isOpen ? 'translate-x-0 w-[85%] sm:w-80 shadow-[0_0_120px_rgba(0,0,0,1)]' : 'translate-x-full md:w-0 md:border-none'}
    flex flex-col h-full glow-frame md:m-3 md:rounded-[2.5rem]
  `;

  return (
    <>
      <div 
        className={`fixed inset-0 bg-black/50 backdrop-blur-md z-[95] md:hidden transition-opacity duration-500 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => onToggle(false)}
      />

      <aside className={sidebarClasses}>
        <div className="w-full flex flex-col h-full overflow-hidden">
          <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 shrink-0 relative">
            <h3 className="text-[9px] font-black uppercase tracking-[0.25em] text-[#71717a]">Session Panel</h3>
            <button onClick={() => onToggle(false)} className="p-2 text-grok-muted hover:text-white transition-all active:scale-95">
              <PanelRight size={20} className="md:rotate-180" />
            </button>
          </header>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-12">
            <section>
              <h4 className="text-[9px] font-black text-[#71717a] uppercase tracking-[0.3em] mb-5 flex items-center gap-2">
                <History size={12} className="text-grok-accent" /> CHAT HISTORY
              </h4>
              <div className="space-y-2">
                {sessions.map((s) => (
                  <button
                    key={s.id} onClick={() => onSelectSession(s.id)}
                    className={`group w-full text-left p-4 rounded-2xl transition-all border ${activeSessionId === s.id ? 'bg-white/10 border-white/5 text-white shadow-xl shadow-black/40' : 'border-transparent text-[#71717a] hover:bg-white/5 hover:text-white'}`}
                  >
                    <p className="text-[13px] font-bold truncate tracking-tight">{s.title}</p>
                    <p className="text-[8px] font-black uppercase tracking-[0.2em] mt-1.5 opacity-40 group-hover:opacity-70 transition-opacity">ID: {s.id.substr(-6)}</p>
                  </button>
                ))}
                {sessions.length === 0 && (
                  <div className="text-center py-6 opacity-30">
                    <p className="text-[10px] font-black uppercase tracking-widest italic">History Empty</p>
                  </div>
                )}
              </div>
            </section>

            <section>
              <div className="flex items-center justify-between mb-5">
                <h4 className="text-[9px] font-black text-[#71717a] uppercase tracking-[0.3em] flex items-center gap-2">
                  <Database size={12} className="text-grok-accent" /> ASSET VAULT
                </h4>
                <button 
                  onClick={() => fileInputRef.current?.click()} 
                  className="p-2.5 bg-grok-accent/10 text-grok-accent hover:bg-grok-accent/20 rounded-xl transition-all active:scale-90 shadow-lg shadow-grok-accent/5"
                >
                  <Upload size={16} />
                </button>
                <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => e.target.files?.[0] && onUploadFile(e.target.files[0])} />
              </div>
              <div className="space-y-2.5">
                {projectFiles.map((f) => (
                  <div key={f.id} className="flex items-center justify-between p-4 glass-card rounded-2xl group/file relative overflow-hidden">
                    <div className="absolute inset-0 bg-grok-accent/5 opacity-0 group-hover/file:opacity-100 transition-opacity"></div>
                    <div className="flex items-center gap-3 min-w-0 relative z-10">
                      <div className="w-8 h-8 rounded-lg bg-grok-accent/10 flex items-center justify-center text-grok-accent">
                        <FileText size={16} />
                      </div>
                      <div className="min-w-0">
                        <p className="text-[12px] text-white truncate font-bold tracking-tight mb-0.5">{f.name}</p>
                        <p className="text-[8px] text-[#71717a] font-black uppercase tracking-[0.1em]">{f.size}</p>
                      </div>
                    </div>
                    <button onClick={() => onRemoveFile(f.id)} className="p-2 text-[#71717a] hover:text-grok-error transition-colors relative z-10">
                      <X size={16} />
                    </button>
                  </div>
                ))}
                {projectFiles.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 opacity-20">
                    <FolderOpen size={40} strokeWidth={1} className="mb-3" />
                    <p className="text-[9px] font-black uppercase tracking-widest">No Active Assets</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </aside>
    </>
  );
};
