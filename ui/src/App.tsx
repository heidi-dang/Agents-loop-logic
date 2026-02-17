import React, { useState, useEffect, useMemo } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { AgentArea } from './components/AgentArea';
import { RightSidebar } from './components/RightSidebar';
import { TerminalArea } from './components/TerminalArea';
import { SettingsModal } from './components/SettingsModal';
import { AIProviderId, AppView, ChatSession, Message, ProjectFile, ProviderInfo, User } from './types';
import { health, getSettings, saveSettings, listAgents, runOnce, runLoop, chat, getRun } from './api/heidi';
import { subscribeRunStream } from './api/stream';
import { Mail, Lock, ArrowRight, Loader2, Activity } from 'lucide-react';

const App: React.FC = () => {
  const [session, setSession] = useState<{ user: User } | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');

  const [currentView, setCurrentView] = useState<AppView>(AppView.CHAT);
  const [activeProvider, setActiveProvider] = useState<AIProviderId>(AIProviderId.HEIDI);
  const [isAgentMode, setIsAgentMode] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Heidi Backend State
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [agents, setAgents] = useState([{ name: 'copilot', description: 'Default executor' }]);
  const [selectedAgent, setSelectedAgent] = useState('copilot');

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [projectFiles, setProjectFiles] = useState<ProjectFile[]>([]);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  // Provider configuration (simplified for Heidi)
  const providers: ProviderInfo[] = useMemo(() => [
    { 
      id: AIProviderId.HEIDI, 
      name: 'Heidi Backend', 
      description: 'Heidi AI backend (default)', 
      models: ['copilot'], 
      icon: '✨', 
      isConnected: backendStatus === 'connected' 
    },
  ], [backendStatus]);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const settings = getSettings();
        await health(settings.baseUrl, settings.apiKey);
        setBackendStatus('connected');
        
        // Load available agents
        const agentList = await listAgents();
        if (agentList.length > 0) {
          setAgents(agentList);
        }
      } catch (err) {
        console.warn('Backend health check failed:', err);
        setBackendStatus('disconnected');
      } finally {
        setAuthLoading(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  // Recover session from localStorage
  useEffect(() => {
    const recoverSession = () => {
      try {
        const storedIdentity = localStorage.getItem('heidi_user');
        if (storedIdentity) {
          const user = JSON.parse(storedIdentity);
          setSession({ user });
        }
      } catch (err) {
        console.warn('Session recovery failed:', err);
      }
    };
    recoverSession();
  }, []);

  const handleAppAuthSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setTimeout(() => {
      const user: User = {
        id: 'heidi-' + Math.random().toString(36).substr(2, 9),
        name: authMode === 'signup' ? 'New User' : 'Heidi User',
        email: 'user@heidi.local',
        image: `https://api.dicebear.com/7.x/avataaars/svg?seed=${Math.random()}`
      };
      localStorage.setItem('heidi_user', JSON.stringify(user));
      setSession({ user });
      setAuthLoading(false);
    }, 500);
  };

  const handleLogout = () => {
    localStorage.removeItem('heidi_user');
    setSession(null);
    setIsSettingsOpen(false);
    setSessions([]);
    setActiveSessionId('');
  };

  const handleNewChat = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      providerId: AIProviderId.HEIDI,
      title: currentView === AppView.AGENT ? 'Agent Task' : 'Heidi Chat',
      messages: [],
      createdAt: new Date(),
      isAgentMode: currentView === AppView.AGENT || isAgentMode
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setIsMobileMenuOpen(false);
    setIsRightSidebarOpen(false);
  };

  const activeSession = useMemo(() => 
    sessions.find(s => s.id === activeSessionId) || sessions[0], 
    [sessions, activeSessionId]
  );

  // Handle sending messages - use Heidi backend
  const handleSendMessage = async (text: string) => {
    if (!activeSessionId || backendStatus !== 'connected') return;
    
    setIsTyping(true);
    
    // Add user message
    const userMessage: Message = { 
      id: Date.now().toString(), 
      role: 'user', 
      content: text, 
      timestamp: new Date() 
    };
    
    const updatedHistory = [...(activeSession?.messages || []), userMessage];
    setSessions(prev => prev.map(s => 
      s.id === activeSessionId ? { ...s, messages: updatedHistory } : s
    ));

    try {
      if (isAgentMode || currentView === AppView.AGENT) {
        // Use Loop mode for agent tasks
        const response = await runLoop({
          task: text,
          executor: selectedAgent,
          max_retries: 2,
          workdir: null,
        });

        // Start streaming the response
        const streamController = subscribeRunStream(response.run_id, {
          onEvent: (event) => {
            setSessions(prev => prev.map(s => {
              if (s.id !== activeSessionId) return s;
              const lastMsg = s.messages[s.messages.length - 1];
              if (lastMsg?.role === 'assistant') {
                // Update existing assistant message
                return {
                  ...s,
                  messages: s.messages.map((m, idx) => 
                    idx === s.messages.length - 1 
                      ? { ...m, content: m.content + '\n' + event.message }
                      : m
                  )
                };
              } else {
                // Add new assistant message
                return {
                  ...s,
                  messages: [...s.messages, {
                    id: Date.now().toString(),
                    role: 'assistant',
                    content: event.message,
                    timestamp: new Date(),
                  }]
                };
              }
            }));
          },
          onDone: () => {
            setIsTyping(false);
          },
          onError: (err) => {
            console.error('Stream error:', err);
            setIsTyping(false);
            setSessions(prev => prev.map(s => 
              s.id === activeSessionId 
                ? { ...s, messages: [...s.messages, {
                    id: Date.now().toString(),
                    role: 'assistant',
                    content: `Error: ${err.message}`,
                    timestamp: new Date(),
                  }]} 
                : s
            ));
          }
        });

        // Store controller for cleanup if needed
        return () => streamController.close();
      } else {
        // Use simple chat for regular messages
        const response = await chat(text, selectedAgent);
        
        const assistantMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
        };

        setSessions(prev => prev.map(s => 
          s.id === activeSessionId 
            ? { ...s, messages: [...s.messages, assistantMessage] } 
            : s
        ));
        setIsTyping(false);
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      setSessions(prev => prev.map(s => 
        s.id === activeSessionId 
          ? { ...s, messages: [...s.messages, {
              id: Date.now().toString(),
              role: 'assistant',
              content: `Error: ${error.message || 'Failed to get response'}`,
              timestamp: new Date(),
            }]} 
          : s
      ));
    }
  };

  const handleFileUpload = async (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      const newFile: ProjectFile = { 
        id: Math.random().toString(36).substring(2, 11), 
        name: file.name, 
        size: `${(file.size / 1024).toFixed(1)} KB`, 
        type: file.type || 'text/plain', 
        content: base64 
      };
      setProjectFiles(prev => [...prev, newFile]);
    };
    reader.readAsDataURL(file);
  };

  if (authLoading) {
    return (
      <div className="flex h-screen w-full bg-[#000000] items-center justify-center">
        <div className="flex flex-col items-center gap-8 px-6 text-center animate-pulse">
          <div className="relative">
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <Activity className="w-8 h-8 text-white" />
            </div>
          </div>
          <div>
            <p className="text-[10px] text-[#71717a] font-black uppercase tracking-[0.4em]">Connecting...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex h-screen w-full bg-[#000000] items-center justify-center p-4 md:p-6 relative overflow-hidden">
        <div className="max-w-md w-full rounded-[2.5rem] p-8 md:p-12 relative z-20 animate-in fade-in duration-700">
          <div className="flex flex-col items-center mb-12 text-center">
            <div className="mb-8">
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-2xl">
                <Activity className="w-12 h-12 text-white" />
              </div>
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white tracking-tighter mb-2">HEIDI</h2>
            <p className="text-[#71717a] text-[11px] font-black tracking-[0.3em] uppercase opacity-60">
              {backendStatus === 'connected' ? 'Backend Connected' : 'Backend Disconnected'}
            </p>
          </div>

          <form onSubmit={handleAppAuthSubmit} className="space-y-6">
            <div className="space-y-2">
              <div className="relative">
                <Mail className="absolute left-5 top-1/2 -translate-y-1/2 text-[#71717a]" size={18} />
                <input 
                  type="email" 
                  required 
                  placeholder="Email Address" 
                  className="w-full bg-[#0a0a0a] border border-[#27272a] rounded-2xl py-5 pl-14 pr-5 text-[15px] font-medium text-white focus:border-white outline-none transition-all placeholder:text-[#3f3f46]" 
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="relative">
                <Lock className="absolute left-5 top-1/2 -translate-y-1/2 text-[#71717a]" size={18} />
                <input 
                  type="password" 
                  required 
                  placeholder="Password" 
                  className="w-full bg-[#0a0a0a] border border-[#27272a] rounded-2xl py-5 pl-14 pr-5 text-[15px] font-medium text-white focus:border-white outline-none transition-all placeholder:text-[#3f3f46]" 
                />
              </div>
            </div>

            <button type="submit" className="w-full py-5 bg-white text-black font-black uppercase tracking-[0.2em] rounded-full hover:bg-[#f4f4f5] transition-all flex items-center justify-center gap-3 group mt-4 text-[13px]">
              {authMode === 'signin' ? 'Sign In' : 'Sign Up'} 
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </form>

          <div className="mt-12 text-center">
            <button 
              onClick={() => setAuthMode(authMode === 'signin' ? 'signup' : 'signin')} 
              className="text-[11px] text-[#52525b] font-black uppercase tracking-widest hover:text-white transition-colors"
            >
              {authMode === 'signin' ? "Create Account" : "Already have an account?"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-[#000000] overflow-hidden text-white flex-col md:flex-row">
      <Sidebar 
        currentView={currentView}
        isAgentMode={isAgentMode}
        onToggleAgentMode={() => {
           setIsAgentMode(!isAgentMode);
           if (currentView !== AppView.AGENT) setCurrentView(AppView.AGENT);
        }}
        onSelectView={(v) => { setCurrentView(v); setIsMobileMenuOpen(false); }}
        onOpenSettings={() => { setIsSettingsOpen(true); setIsMobileMenuOpen(false); }}
        onNewChat={handleNewChat}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={setIsSidebarCollapsed}
        user={session.user}
        isMobileOpen={isMobileMenuOpen}
        onMobileClose={() => setIsMobileMenuOpen(false)}
        backendStatus={backendStatus}
      />
      
      <main className="flex-1 flex flex-col min-w-0 bg-transparent relative z-0 h-full overflow-hidden">
        {currentView === AppView.CHAT && (
          <ChatArea 
            provider={providers[0]}
            messages={activeSession?.messages || []}
            onSendMessage={handleSendMessage}
            isTyping={isTyping}
            isAgentMode={isAgentMode}
            onToggleRightSidebar={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
            isRightSidebarOpen={isRightSidebarOpen}
            onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
            backendStatus={backendStatus}
          />
        )}
        {currentView === AppView.AGENT && (
          <AgentArea 
            messages={activeSession?.messages || []}
            onSendMessage={handleSendMessage}
            isTyping={isTyping}
            onToggleRightSidebar={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
            isRightSidebarOpen={isRightSidebarOpen}
            onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
            backendStatus={backendStatus}
          />
        )}
        {currentView === AppView.TERMINAL && (
          <TerminalArea onOpenMobileMenu={() => setIsMobileMenuOpen(true)} />
        )}
      </main>

      <RightSidebar 
        sessions={sessions}
        activeSessionId={activeSessionId}
        projectFiles={projectFiles}
        onSelectSession={(id) => { setActiveSessionId(id); setIsRightSidebarOpen(false); }}
        onUploadFile={handleFileUpload}
        onRemoveFile={(id) => setProjectFiles(prev => prev.filter(f => f.id !== id))}
        isOpen={isRightSidebarOpen}
        onToggle={setIsRightSidebarOpen}
      />

      {isSettingsOpen && (
        <SettingsModal 
          providers={providers}
          activeProviderId={activeProvider}
          agents={agents}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
          onLogout={handleLogout}
          onClose={() => setIsSettingsOpen(false)}
          backendStatus={backendStatus}
          onReconnect={async () => {
            setBackendStatus('checking');
            try {
              const settings = getSettings();
              await health(settings.baseUrl, settings.apiKey);
              setBackendStatus('connected');
              const agentList = await listAgents();
              if (agentList.length > 0) setAgents(agentList);
            } catch (err) {
              setBackendStatus('disconnected');
            }
          }}
        />
      )}
    </div>
  );
};

export default App;
