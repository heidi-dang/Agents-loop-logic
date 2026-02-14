import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api/heidi';
import { Agent, AppMode, RunEvent, RunStatus, Message, MessageStatus, ToolEvent } from '../types';
import { 
  Send, Repeat, StopCircle, CheckCircle, AlertCircle, Loader2, PlayCircle, PanelLeft,
  Sparkles, Cpu, Map, Terminal, Eye, Shield, MessageSquare, ArrowDown
} from 'lucide-react';
import ThinkingBubble from '../components/ThinkingBubble';
import ToolCard from '../components/ToolCard';

interface ChatProps {
  initialRunId?: string | null;
  onRunCreated?: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const Chat: React.FC<ChatProps> = ({ initialRunId, onRunCreated, isSidebarOpen, onToggleSidebar }) => {
  // Config State
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState<AppMode>(AppMode.CHAT); // Default to CHAT
  const [executor, setExecutor] = useState('copilot');
  const [maxRetries, setMaxRetries] = useState(2);
  const [dryRun, setDryRun] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Runtime State
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('idle');
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  // Scroll State
  const [isAtBottom, setIsAtBottom] = useState(true);

  // Refs for streaming management
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingRef = useRef<any>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // --- Initialization ---

  useEffect(() => {
    api.getAgents().then(setAgents).catch(() => {
      setAgents([{ name: 'copilot', description: 'Default executor' }]);
    });
  }, []);

  useEffect(() => {
    if (initialRunId && initialRunId !== runId) {
      loadRun(initialRunId);
    } else if (!initialRunId) {
      resetChat();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialRunId]);

  useEffect(() => {
    if (isAtBottom && chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, status]); // Removed isAtBottom to prevent loop, added it implicitly via condition

  useEffect(() => {
    return () => stopStreaming();
  }, []);

  // --- Core Logic ---

  const resetChat = () => {
    stopStreaming();
    setRunId(null);
    setMessages([]);
    setStatus('idle');
    setResult(null);
    setError(null);
    setPrompt('');
    setIsCancelling(false);
    setIsAtBottom(true);
  };

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const processEvents = (events: RunEvent[], currentMessages: Message[], currentRunId: string): Message[] => {
      // Deep clone to ensure immutability
      let newMessages = JSON.parse(JSON.stringify(currentMessages)) as Message[];

      let assistantMsg = newMessages.find(m => m.role === 'assistant' && m.id.startsWith(`asst-${currentRunId}`));

      if (!assistantMsg && events.length > 0) {
          assistantMsg = {
              id: `asst-${currentRunId}`,
              role: 'assistant',
              status: 'thinking',
              content: '',
              createdAt: Date.now(),
              toolEvents: []
          };
          newMessages.push(assistantMsg);
      }

      for (const event of events) {
          if (event.type === 'user_prompt') {
              const existingUserMsg = newMessages.find(m => m.role === 'user');
              if (!existingUserMsg) {
                  newMessages.unshift({
                      id: `user-${event.ts}`,
                      role: 'user',
                      status: 'done',
                      content: event.message || '',
                      createdAt: new Date(event.ts).getTime()
                  });
              }
              continue;
          }

          if (!assistantMsg) continue;

          if (event.type === 'tool_start') {
               const data = event.data || {};
               const toolId = data.tool_id || `tool-${event.ts}`;

               if (!assistantMsg.toolEvents?.find(t => t.id === toolId)) {
                   if (!assistantMsg.toolEvents) assistantMsg.toolEvents = [];
                   assistantMsg.toolEvents.push({
                       id: toolId,
                       title: data.title || 'Processing...',
                       status: 'running',
                       lines: [],
                       updatedAt: new Date(event.ts).getTime()
                   });
                   assistantMsg.status = 'streaming';
               }
          } else if (event.type === 'tool_log') {
               const data = event.data || {};
               const tool = assistantMsg.toolEvents?.find(t => t.id === data.tool_id);
               if (tool) {
                   tool.lines.push(data.line || '');
                   tool.updatedAt = new Date(event.ts).getTime();
               }
          } else if (event.type === 'tool_done') {
               const data = event.data || {};
               const tool = assistantMsg.toolEvents?.find(t => t.id === data.tool_id);
               if (tool) {
                   tool.status = 'done';
                   tool.updatedAt = new Date(event.ts).getTime();
               }
          } else if (event.type === 'tool_error') {
               const data = event.data || {};
               const tool = assistantMsg.toolEvents?.find(t => t.id === data.tool_id);
               if (tool) {
                   tool.status = 'error';
                   tool.lines.push(`Error: ${data.error}`);
                   tool.updatedAt = new Date(event.ts).getTime();
               }
          } else if (event.type === 'message_delta') {
               const data = event.data || {};
               assistantMsg.content += (data.deltaText || '');
               assistantMsg.status = 'streaming';
          }
      }

      return newMessages;
  };

  const loadRun = async (id: string) => {
    stopStreaming();
    setRunId(id);
    setMessages([]);
    setError(null);
    setResult(null);
    setIsAtBottom(true);

    try {
      const details = await api.getRun(id);

      if (details.events) {
          const reconstructed = processEvents(details.events, [], id);
          setMessages(reconstructed);
      }

      setStatus(details.meta?.status || 'unknown');
      setMode(details.meta?.task ? AppMode.LOOP : AppMode.RUN);
      setExecutor(details.meta?.executor || 'copilot');
      if (details.result) setResult(details.result);
      if (details.error) setError(details.error);

      if (
        details.meta?.status !== RunStatus.COMPLETED &&
        details.meta?.status !== RunStatus.FAILED
      ) {
        startStreaming(id);
      } else {
         setMessages(prev => {
             // Use functional update with deep clone for consistency
             const newMsgs = JSON.parse(JSON.stringify(prev)) as Message[];
             const asst = newMsgs.find(m => m.role === 'assistant');
             if (asst) asst.status = 'done';
             return newMsgs;
         });
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load run details');
    }
  };

  const handleStart = async () => {
    if (!prompt.trim()) return;

    resetChat();
    setIsSending(true);
    setStatus('initiating');

    const userMsg: Message = {
        id: `user-temp-${Date.now()}`,
        role: 'user',
        status: 'done',
        content: prompt,
        createdAt: Date.now()
    };

    const assistantMsg: Message = {
        id: `asst-temp-${Date.now()}`,
        role: 'assistant',
        status: 'thinking',
        content: '',
        createdAt: Date.now(),
        toolEvents: []
    };

    setMessages([userMsg, assistantMsg]);

    try {
      let response;
      
      if (mode === AppMode.CHAT) {
        const chatRes = await api.chat(prompt, executor);
        setMessages(prev => {
            const newMsgs = JSON.parse(JSON.stringify(prev)) as Message[];
            const asst = newMsgs.find(m => m.role === 'assistant');
            if (asst) {
                asst.status = 'done';
                asst.content = chatRes.response;
            }
            return newMsgs;
        });
        setStatus(RunStatus.COMPLETED);
        setResult(chatRes.response);
        setIsSending(false);
        return;
      }
      
      if (mode === AppMode.RUN) {
        response = await api.startRun({
          prompt,
          executor,
          workdir: null,
          dry_run: dryRun
        });
      } else {
        response = await api.startLoop({
          task: prompt,
          executor,
          max_retries: maxRetries,
          workdir: null,
          dry_run: dryRun
        });
      }

      const newRunId = response.run_id;
      setRunId(newRunId);
      setStatus(RunStatus.RUNNING);
      
      setMessages(prev => prev.map(m => {
          if (m.id.startsWith('asst-temp')) return { ...m, id: `asst-${newRunId}` };
          return m;
      }));

      if (onRunCreated) onRunCreated();
      startStreaming(newRunId);
    } catch (err: any) {
      setError(err.message || 'Failed to start run');
      setStatus(RunStatus.FAILED);
      setMessages(prev => prev.map(m => {
          if (m.role === 'assistant') return { ...m, status: 'error', content: 'Failed to start.' };
          return m;
      }));
    } finally {
      setIsSending(false);
    }
  };

  const handleStop = async () => {
      if (!runId) return;
      setIsCancelling(true);
      try {
          await api.cancelRun(runId);
          setStatus('cancelling');
      } catch (e) {
          console.error("Cancel failed", e);
      }
  };

  const startStreaming = (id: string) => {
    stopStreaming(); 
    const streamUrl = api.getStreamUrl(id);
    
    try {
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => console.log("SSE Connected");

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'run_state') {
              setStatus(data.data?.state || 'running');
          } else if (data.type === 'status') {
              setStatus(data.message);
          }

          setMessages(prev => processEvents([data], prev, id));

        } catch (e) {
          console.warn("Error parsing SSE data", event.data);
        }
      };

      es.onerror = (err) => {
        console.warn("SSE Error, switching to polling", err);
        es.close();
        eventSourceRef.current = null;
        startPolling(id);
      };

    } catch (e) {
      console.error("Failed to setup SSE", e);
      startPolling(id);
    }
  };

  const startPolling = (id: string) => {
    if (pollingRef.current) return;
    
    const check = async () => {
      try {
        const details = await api.getRun(id);
        
        if (details.events) {
            const reconstructed = processEvents(details.events, [], id);
            const localUser = messages.find(m => m.role === 'user');
            if (localUser && !reconstructed.find(m => m.role === 'user')) {
                reconstructed.unshift(localUser);
            }
            setMessages(reconstructed);
        }
        
        const currentStatus = details.meta?.status || 'unknown';
        setStatus(currentStatus);
        
        if (details.result) setResult(details.result);
        if (details.error) setError(details.error);

        const s = currentStatus.toLowerCase();
        if (s === 'completed' || s === 'failed' || s === 'cancelled') {
          stopStreaming();
          setIsCancelling(false);
           setMessages(prev => {
             const newMsgs = JSON.parse(JSON.stringify(prev)) as Message[];
             const asst = newMsgs.find(m => m.role === 'assistant');
             if (asst && asst.status !== 'done' && asst.status !== 'error') asst.status = s === 'failed' ? 'error' : 'done';
             return newMsgs;
         });
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    };
    
    check();
    pollingRef.current = setInterval(check, 1000);
  };

  const handleScroll = () => {
      if (scrollContainerRef.current) {
          const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
          const isBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 50;
          setIsAtBottom(isBottom);
      }
  };

  const scrollToBottom = () => {
      if (chatBottomRef.current) {
          chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
          setIsAtBottom(true); // Manually set to true to resume auto-scroll
      }
  };

  // --- Rendering Helpers ---

  const renderStatusBadge = () => {
    const rawStatus = status || 'idle';
    const s = rawStatus.toLowerCase();
    
    let color = "bg-white/5 text-slate-400 border border-white/10";
    let icon = <Loader2 size={14} className="animate-spin text-purple-400" />;
    let label = rawStatus;

    if (s === 'completed') {
      color = "bg-green-500/10 text-green-300 border border-green-500/20";
      icon = <CheckCircle size={14} />;
    } else if (s === 'failed' || s === 'error') {
      color = "bg-red-500/10 text-red-300 border border-red-500/20";
      icon = <AlertCircle size={14} />;
    } else if (s === 'idle') {
      color = "bg-white/5 text-slate-400 border border-white/10";
      icon = <div className="w-2 h-2 rounded-full bg-slate-600" />;
      label = "Idle";
    } else if (s.includes('cancelling') || s.includes('cancelled')) {
      color = "bg-orange-500/10 text-orange-300 border border-orange-500/20";
      icon = <StopCircle size={14} />;
    } else if (s.includes('initiating')) {
      color = "bg-blue-500/10 text-blue-300 border border-blue-500/20";
      icon = <Loader2 size={14} className="animate-spin" />;
      label = "Initiating...";
    } else {
      color = "bg-purple-500/10 text-purple-300 border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.15)]";
      if (s.includes('planning')) { label = "Planning..."; icon = <Map size={14} />; }
      else if (s.includes('executing')) { label = "Executing..."; icon = <Terminal size={14} />; }
      else if (s.includes('reviewing')) { label = "Reviewing..."; icon = <Eye size={14} />; }
      else if (s.includes('auditing')) { label = "Auditing..."; icon = <Shield size={14} />; }
      else { label = "Running..."; icon = <Cpu size={14} className="animate-pulse" />; }
    }

    return (
      <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider backdrop-blur-md transition-all duration-300 ${color}`}>
        {icon}
        <span className="truncate max-w-[180px]">{label}</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-transparent relative">
      
      {/* 1. Header Area */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/20 backdrop-blur-md z-10">
        <div className="flex items-center gap-4">
           {!isSidebarOpen && (
               <button 
                onClick={onToggleSidebar} 
                className="text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-white/5"
                title="Open Sidebar"
               >
                   <PanelLeft size={20} />
               </button>
           )}
           {renderStatusBadge()}
           {runId && <span className="text-xs font-mono text-purple-200/50">ID: {runId}</span>}
        </div>
      </div>

      {/* 2. Main Chat Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth custom-scrollbar relative"
      >
        
        {/* Empty State */}
        {!runId && messages.length === 0 && !isSending && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-80 pb-20">
             <div className="w-32 h-32 mb-6 relative">
                 <div className="absolute inset-0 bg-purple-500/20 blur-3xl rounded-full"></div>
                  <div className="relative w-full h-full flex items-center justify-center">
                    <Sparkles className="w-16 h-16 text-purple-400" />
                  </div>
             </div>
            <h2 className="mt-4 text-3xl font-bold text-white tracking-tight">How can I help you?</h2>
            <p className="text-slate-400 mt-2">Configure your agent below and start a new run.</p>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
            <div key={msg.id} className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {msg.role === 'user' ? (
                    <div className="flex justify-end">
                        <div className="max-w-[80%] bg-gradient-to-br from-pink-600 to-purple-700 text-white px-5 py-4 rounded-2xl rounded-tr-sm shadow-xl shadow-purple-900/20 border border-white/10">
                            <div className="text-xs text-pink-200 mb-1 font-bold uppercase opacity-80 tracking-wide">
                                You
                            </div>
                            <div className="whitespace-pre-wrap leading-relaxed">
                                {msg.content}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex gap-4 max-w-[90%]">
                        <div className="flex-shrink-0 mt-1">
                             <div className="w-10 h-10 rounded-xl bg-black/40 flex items-center justify-center border border-white/10 shadow-lg overflow-hidden">
                                  <Sparkles size={20} className="text-purple-400" />
                             </div>
                        </div>
                        <div className="flex-1 space-y-4">
                             {/* Thinking Bubble */}
                             {msg.status === 'thinking' && <ThinkingBubble />}
                             
                             {/* Content */}
                             {msg.content && (
                                 <div className="text-sm leading-relaxed p-4 rounded-2xl rounded-tl-sm border shadow-sm backdrop-blur-sm bg-[#1a162e]/80 border-white/5 text-slate-200">
                                     <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                                 </div>
                             )}

                             {/* Tool Cards */}
                             {msg.toolEvents?.map(tool => (
                                 <ToolCard key={tool.id} tool={tool} />
                             ))}
                        </div>
                    </div>
                )}
            </div>
        ))}

        {/* Final Result Block */}
        {result && (
            <div className="mt-8 border-t border-white/10 pt-8 animate-in fade-in zoom-in-95 duration-500">
                <h3 className="text-green-400 font-bold mb-3 flex items-center gap-2 text-sm uppercase tracking-wider">
                    <CheckCircle size={16} />
                    Final Output
                </h3>
                <div className="bg-black/30 border border-green-500/20 rounded-xl p-5 font-mono text-sm text-green-100/90 overflow-x-auto shadow-inner relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-green-500/50 rounded-l-xl"></div>
                    <pre>{result}</pre>
                </div>
            </div>
        )}

        {error && (
            <div className="mt-8 border-t border-white/10 pt-8">
                 <h3 className="text-red-400 font-bold mb-3 flex items-center gap-2 text-sm uppercase tracking-wider">
                    <AlertCircle size={16} />
                    Execution Failed
                </h3>
                <div className="bg-red-950/20 border border-red-500/20 rounded-xl p-5 font-mono text-sm text-red-200">
                    {error}
                </div>
            </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Jump to Bottom Button */}
      {!isAtBottom && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-32 right-8 z-30 p-2 rounded-full bg-purple-600/80 hover:bg-purple-600 text-white shadow-lg backdrop-blur-sm transition-all animate-in fade-in zoom-in-95"
            title="Jump to latest"
          >
              <ArrowDown size={20} />
          </button>
      )}

      {/* 3. Input Area */}
      <div className="p-6 z-20">
        <div className="max-w-4xl mx-auto space-y-4 bg-black/40 backdrop-blur-xl border border-white/10 p-4 rounded-2xl shadow-2xl">
            
            {/* Input Controls */}
            {!runId && (
                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400 p-1">
                    {/* Mode Toggle */}
                    <div className="flex bg-black/40 rounded-lg p-1 border border-white/5">
                        <button 
                            onClick={() => setMode(AppMode.CHAT)}
                            className={`px-4 py-1.5 rounded-md transition-all font-medium ${mode === AppMode.CHAT ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50' : 'hover:text-white hover:bg-white/5'}`}
                        >
                            <span className="flex items-center gap-1.5"><MessageSquare size={14} /> Chat</span>
                        </button>
                        <button 
                            onClick={() => setMode(AppMode.RUN)}
                            className={`px-4 py-1.5 rounded-md transition-all font-medium ${mode === AppMode.RUN ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/50' : 'hover:text-white hover:bg-white/5'}`}
                        >
                            <span className="flex items-center gap-1.5"><PlayCircle size={14} /> Run</span>
                        </button>
                        <button 
                            onClick={() => setMode(AppMode.LOOP)}
                            className={`px-4 py-1.5 rounded-md transition-all font-medium ${mode === AppMode.LOOP ? 'bg-pink-600 text-white shadow-lg shadow-pink-900/50' : 'hover:text-white hover:bg-white/5'}`}
                        >
                            <span className="flex items-center gap-1.5"><Repeat size={14} /> Loop</span>
                        </button>
                    </div>

                    <div className="w-px h-5 bg-white/10 mx-1"></div>

                    {/* Executor Select */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs uppercase font-bold tracking-wider text-slate-500">Agent</span>
                        <select 
                            value={executor} 
                            onChange={(e) => setExecutor(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-slate-200 text-xs focus:ring-1 focus:ring-purple-500 outline-none hover:bg-white/10 transition-colors"
                        >
                            {agents.map(a => (
                                <option key={a.name} value={a.name} className="bg-slate-900">{a.name}</option>
                            ))}
                        </select>
                    </div>

                    {mode === AppMode.LOOP && (
                         <div className="flex items-center gap-2 animate-in fade-in zoom-in-95">
                            <span className="text-xs uppercase font-bold tracking-wider text-slate-500">Retries</span>
                            <input 
                                type="number" 
                                min={0} 
                                max={10} 
                                value={maxRetries} 
                                onChange={(e) => setMaxRetries(parseInt(e.target.value))}
                                className="w-14 bg-white/5 border border-white/10 rounded px-2 py-1.5 text-slate-200 text-xs focus:ring-1 focus:ring-purple-500 outline-none hover:bg-white/10 transition-colors"
                            />
                        </div>
                    )}

                    <div className="flex-1"></div>

                    <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
                        <input 
                            type="checkbox" 
                            checked={dryRun} 
                            onChange={(e) => setDryRun(e.target.checked)}
                            className="rounded bg-white/10 border-white/20 text-purple-500 focus:ring-offset-black focus:ring-purple-500"
                        />
                        <span className="text-xs font-medium">Dry Run</span>
                    </label>
                </div>
            )}

            {/* Main Text Input */}
            <div className="relative group">
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey && !isRunning) {
                            e.preventDefault();
                            handleStart();
                        }
                    }}
                    placeholder={mode === AppMode.LOOP ? "Describe the task you want Heidi to complete..." : "Ask Heidi a question or give a command..."}
                    disabled={isSending || isRunning}
                    className="w-full bg-black/20 border border-white/10 text-white placeholder-slate-500/70 rounded-xl p-4 pr-16 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 outline-none resize-none min-h-[60px] max-h-[200px] shadow-inner disabled:opacity-50 disabled:cursor-not-allowed transition-all group-hover:bg-black/30"
                    rows={1}
                    style={{ minHeight: '80px' }}
                />
                
                <div className="absolute right-3 bottom-3">
                    {!isRunning ? (
                        <button
                            onClick={handleStart}
                            disabled={!prompt.trim() || isSending}
                            className={`p-2.5 rounded-lg flex items-center justify-center transition-all duration-300 ${
                                prompt.trim() && !isSending ? 'bg-gradient-to-tr from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white transform hover:scale-105' : 'bg-white/10 text-slate-500 cursor-not-allowed'
                            }`}
                        >
                            {isSending ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                        </button>
                    ) : (
                        <button
                            onClick={handleStop} 
                            disabled={isCancelling}
                            className={`p-2.5 rounded-lg border transition-colors ${
                                isCancelling 
                                ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' 
                                : 'bg-red-500/10 hover:bg-red-500/20 text-red-300 border-red-500/20 hover:border-red-500/40'
                            }`}
                            title="Stop Run"
                        >
                           {isCancelling ? <Loader2 size={20} className="animate-spin" /> : <StopCircle size={20} />}
                        </button>
                    )}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
