
import React, { useState, useRef, useEffect, memo } from 'react';
import { Message, ProviderInfo, ToolCall } from '../types';
// Heidi Chat Area - Simplified for Heidi backend integration
import { User, Bot, Loader2, Terminal, Check, X, PanelRight, ArrowUp, Menu } from 'lucide-react';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';

interface ChatAreaProps {
  provider: ProviderInfo;
  messages: Message[];
  onSendMessage: (text: string) => void;
  isTyping: boolean;
  isAgentMode: boolean;
  onToggleRightSidebar: () => void;
  isRightSidebarOpen: boolean;
  onApproveTool?: (messageId: string, toolCallId: string) => void;
  onRejectTool?: (messageId: string, toolCallId: string) => void;
  onOpenMobileMenu: () => void;
  backendStatus?: 'checking' | 'connected' | 'disconnected';
}

const ToolCallCard: React.FC<{ tool: ToolCall, onApprove?: () => void, onReject?: () => void }> = ({ tool, onApprove, onReject }) => {
  return (
    <div className="mt-4 border rounded-[1.5rem] overflow-hidden bg-black/40 backdrop-blur-md border-white/10 animate-slide-up shadow-lg">
      <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between bg-white/[0.03]">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-grok-muted" />
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#71717a]">Action Protocol</p>
        </div>
        {tool.status === 'executing' && <Loader2 size={14} className="animate-spin text-white" />}
      </div>
      <div className="p-5 space-y-4">
        <pre className="text-[12px] font-mono p-4 bg-black/60 rounded-xl border border-white/5 overflow-x-auto text-[#d4d4d8] custom-scrollbar">
          {tool.name === 'ssh_exec' ? tool.args.command : `${tool.name}(${JSON.stringify(tool.args)})`}
        </pre>
        {tool.status === 'pending' && (
          <div className="flex gap-2">
            <button onClick={onApprove} className="flex-1 py-3 bg-white text-black rounded-xl text-xs font-black uppercase tracking-widest hover:brightness-110 transition-all flex items-center justify-center gap-2 shadow-lg shadow-white/5">
              <Check size={16} /> Execute
            </button>
            <button onClick={onReject} className="px-5 py-3 bg-white/5 text-[#71717a] border border-white/5 rounded-xl hover:text-white transition-all">
              <X size={16} />
            </button>
          </div>
        )}
        {tool.result && (
          <div className="mt-4 animate-fade-in pt-4 border-t border-white/5">
            <p className="text-[9px] font-black text-[#71717a] uppercase tracking-widest mb-2">Response Buffer</p>
            <pre className="text-[11px] font-mono p-4 bg-black/60 rounded-xl border border-white/5 max-h-40 overflow-y-auto text-grok-success custom-scrollbar">
              {tool.result}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

const MessageItem = memo(({ msg, onApprove, onReject }: { msg: Message, onApprove?: (id: string) => void, onReject?: (id: string) => void }) => (
  <div className={`flex gap-4 md:gap-6 py-8 md:py-10 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
    <div className={`flex gap-4 md:gap-5 max-w-[94%] md:max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-9 h-9 rounded-full shrink-0 flex items-center justify-center shadow-lg transition-transform duration-300 hover:scale-110 ${msg.role === 'user' ? 'bg-white shadow-white/10' : 'glass-card'}`}>
        {msg.role === 'user' ? <User size={18} className="text-black" /> : <Bot size={18} className="text-white" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className={`p-4 md:p-5 rounded-[2rem] leading-relaxed transition-all duration-300 cursor-default shadow-lg group-hover:shadow-2xl ${
          msg.role === 'user' 
            ? 'bg-white/10 border border-white/10 text-white hover:bg-white/[0.14] hover:scale-[1.01] hover:border-white/20' 
            : 'text-[#e4e4e7] hover:bg-white/[0.03] hover:scale-[1.01] border border-transparent hover:border-white/5'
        }`}>
           <p className="text-[15px] md:text-[16px] whitespace-pre-wrap break-words">{msg.content}</p>
        </div>
        {msg.toolCalls?.map(tool => (
          <ToolCallCard key={tool.id} tool={tool} onApprove={() => onApprove?.(tool.id)} onReject={() => onReject?.(tool.id)} />
        ))}
      </div>
    </div>
  </div>
));

export const ChatArea: React.FC<ChatAreaProps> = ({
  provider, messages, onSendMessage, isTyping, isAgentMode, onToggleRightSidebar, isRightSidebarOpen, onApproveTool, onRejectTool, onOpenMobileMenu, backendStatus = 'checking'
}) => {
  const [input, setInput] = useState('');
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  useEffect(() => { if (!isTyping) textareaRef.current?.focus(); }, [isTyping]);

  return (
    <div className="flex flex-col h-full bg-transparent relative overflow-hidden">
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-4 md:px-8 bg-black/40 backdrop-blur-xl shrink-0 z-30">
        <div className="flex items-center gap-2 md:gap-4">
          <button onClick={onOpenMobileMenu} className="md:hidden p-2.5 text-grok-muted hover:text-white transition-all active:scale-90">
            <Menu size={22} />
          </button>
          <div className="flex flex-col md:flex-row md:items-center md:gap-4">
            <h2 className="font-black text-sm text-white tracking-tight truncate max-w-[140px] md:max-w-none">
              {isAgentMode ? 'HEIDI Agent' : provider.name.toUpperCase()}
            </h2>
            <div className="flex items-center gap-1.5">
               <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                 backendStatus === 'connected' 
                   ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]' 
                   : backendStatus === 'disconnected'
                   ? 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.4)]'
                   : 'bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.4)]'
               }`}></div>
               <span className={`text-[9px] font-black uppercase tracking-[0.2em] ${
                 backendStatus === 'connected' 
                   ? 'text-green-400' 
                   : backendStatus === 'disconnected'
                   ? 'text-red-400'
                   : 'text-yellow-400'
               }`}>
                 {backendStatus === 'connected' ? 'Online' : backendStatus === 'disconnected' ? 'Offline' : 'Checking...'}
               </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 md:gap-4">
          <button onClick={onToggleRightSidebar} className={`p-2.5 rounded-full transition-all active:scale-90 ${isRightSidebarOpen ? 'text-white bg-white/5' : 'text-[#71717a] hover:text-white'}`}>
            <PanelRight size={22} />
          </button>
        </div>
      </header>

      <div className="flex-1 min-h-0 relative">
        <Virtuoso
          ref={virtuosoRef}
          data={messages}
          className="h-full custom-scrollbar"
          initialTopMostItemIndex={messages.length > 0 ? messages.length - 1 : 0}
          followOutput="auto"
          alignToBottom={true}
          itemContent={(index, msg) => (
            <div className="px-4 md:px-8 max-w-4xl mx-auto group">
              <MessageItem msg={msg} onApprove={(toolId) => onApproveTool?.(msg.id, toolId)} onReject={(toolId) => onRejectTool?.(msg.id, toolId)} />
            </div>
          )}
          components={{
            Header: () => <div className="h-4 md:h-12" />,
            Footer: () => (
              <div className="px-4 md:px-8 pb-36 md:pb-32 max-w-4xl mx-auto">
                {isTyping && (
                  <div className="flex gap-4 py-8 animate-fade-in">
                    <div className="w-9 h-9 rounded-full glass-card flex items-center justify-center">
                        <Loader2 size={16} className="animate-spin text-white" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                )}
              </div>
            )
          }}
        />
      </div>

      <div className="absolute bottom-0 left-0 w-full p-5 md:p-8 bg-gradient-to-t from-black via-black/90 to-transparent pt-16 z-20 pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <div className="glass-panel rounded-[2rem] md:rounded-[3rem] p-1.5 md:p-2 flex items-center gap-3 shadow-2xl transition-all focus-within:ring-2 focus-within:ring-white/10 focus-within:border-white/20 relative group">
            <div className="absolute inset-0 bg-white/5 rounded-[inherit] opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
            <textarea
              ref={textareaRef} rows={1} value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
              placeholder={backendStatus === 'connected' ? "Ask Heidi anything..." : "Backend disconnected..."}
              className="flex-1 bg-transparent border-none py-4 md:py-5 px-5 md:px-7 text-[16px] text-white focus:outline-none placeholder:text-[#71717a]/60 resize-none min-h-[58px] md:min-h-[68px] max-h-40 md:max-h-52 relative z-10"
            />
            <button
              onClick={() => handleSubmit()} disabled={!input.trim() || backendStatus !== 'connected'}
              className="w-11 h-11 md:w-12 md:h-12 bg-white rounded-full flex items-center justify-center hover:bg-white/90 transition-all disabled:opacity-20 disabled:grayscale shrink-0 mr-1 relative z-10 active:scale-95 shadow-lg"
            >
              <ArrowUp size={22} className="text-black" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
