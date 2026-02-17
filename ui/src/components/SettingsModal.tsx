import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { AIProviderId, ProviderInfo, Agent, SettingsState } from '../types';
import { getSettings, saveSettings } from '../api/heidi';
import { 
  X, Settings, CheckCircle2, LogOut, 
  Activity, Globe, RefreshCw, Server, Key
} from 'lucide-react';

interface SettingsModalProps {
  providers: ProviderInfo[];
  activeProviderId: AIProviderId;
  agents: Agent[];
  selectedAgent: string;
  onSelectAgent: (agent: string) => void;
  onLogout: () => void;
  onClose: () => void;
  backendStatus: 'checking' | 'connected' | 'disconnected';
  onReconnect: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  providers,
  activeProviderId,
  agents,
  selectedAgent,
  onSelectAgent,
  onLogout,
  onClose,
  backendStatus,
  onReconnect
}) => {
  const activeProvider = providers.find(p => p.id === activeProviderId) || providers[0];
  const [settings, setSettings] = useState<SettingsState>(getSettings());
  const [isReconnecting, setIsReconnecting] = useState(false);

  const handleSaveSettings = () => {
    saveSettings(settings);
  };

  const handleReconnect = async () => {
    setIsReconnecting(true);
    await onReconnect();
    setIsReconnecting(false);
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/90 backdrop-blur-2xl md:p-6 animate-in fade-in duration-300">
      <div className="w-full h-full md:w-[min(600px,calc(100vw-48px))] md:h-[85vh] md:max-h-[650px] glass-panel border-white/10 md:rounded-[2.5rem] bg-black/40 flex flex-col animate-in zoom-in-95 duration-400 overflow-hidden relative shadow-[0_0_120px_rgba(0,0,0,1)]">
        
        <div className="px-6 md:px-8 py-6 flex items-center justify-between shrink-0 border-b border-white/5 bg-white/[0.02]">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center">
              <Settings size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-black tracking-tight text-white uppercase leading-none">Settings</h2>
              <p className="text-[9px] text-[#71717a] uppercase tracking-[0.4em] font-bold mt-1.5 opacity-60">Heidi Configuration</p>
            </div>
          </div>
          <button 
              onClick={onClose} 
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 text-white transition-all active:scale-90 border border-white/10"
          >
              <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 md:px-8 py-8 custom-scrollbar space-y-8">
          
          {/* Backend Status Section */}
          <section className="bg-white/[0.01] border border-white/5 rounded-[2rem] p-6 md:p-8 relative overflow-hidden group shadow-lg transition-all hover:border-white/10">
            <div className="flex items-center gap-3 mb-6 opacity-40">
              <Activity size={14} className="text-[#1d9bf0]" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.4em]">Backend Status</h3>
            </div>
            
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${
                  backendStatus === 'connected' 
                    ? 'bg-green-400 animate-pulse' 
                    : backendStatus === 'disconnected'
                    ? 'bg-red-400'
                    : 'bg-yellow-400 animate-pulse'
                }`} />
                <span className="text-white font-bold text-lg">
                  {backendStatus === 'connected' ? 'Connected' : backendStatus === 'disconnected' ? 'Disconnected' : 'Checking...'}
                </span>
              </div>
              <button
                onClick={handleReconnect}
                disabled={isReconnecting}
                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all disabled:opacity-50"
              >
                <RefreshCw size={14} className={isReconnecting ? 'animate-spin' : ''} />
                {isReconnecting ? 'Connecting...' : 'Reconnect'}
              </button>
            </div>

            <div className="flex items-center gap-3 p-4 bg-white/[0.02] rounded-xl border border-white/5">
              <span className="text-4xl">{activeProvider.icon}</span>
              <div>
                <p className="text-white font-bold">{activeProvider.name}</p>
                <p className="text-xs text-[#71717a]">{activeProvider.description}</p>
              </div>
            </div>
          </section>

          {/* Connection Settings */}
          <section className="bg-white/[0.01] border border-white/5 rounded-[2rem] p-6 md:p-8 relative overflow-hidden group shadow-lg transition-all hover:border-white/10">
            <div className="flex items-center gap-3 mb-6 opacity-40">
              <Server size={14} className="text-[#1d9bf0]" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.4em]">Connection</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-[#71717a] mb-2">
                  Backend URL
                </label>
                <div className="relative">
                  <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-[#71717a]" size={16} />
                  <input
                    type="text"
                    value={settings.baseUrl}
                    onChange={(e) => {
                      setSettings({ ...settings, baseUrl: e.target.value });
                    }}
                    onBlur={handleSaveSettings}
                    placeholder="http://127.0.0.1:7777"
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-xl py-4 pl-12 pr-4 text-sm font-medium text-white focus:border-white outline-none transition-all placeholder:text-[#3f3f46]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-[#71717a] mb-2">
                  API Key (Optional)
                </label>
                <div className="relative">
                  <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-[#71717a]" size={16} />
                  <input
                    type="password"
                    value={settings.apiKey}
                    onChange={(e) => {
                      setSettings({ ...settings, apiKey: e.target.value });
                    }}
                    onBlur={handleSaveSettings}
                    placeholder="Enter API key if required"
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-xl py-4 pl-12 pr-4 text-sm font-medium text-white focus:border-white outline-none transition-all placeholder:text-[#3f3f46]"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Agent Selection */}
          <section className="bg-white/[0.01] border border-white/5 rounded-[2rem] p-6 md:p-8 relative overflow-hidden group shadow-lg transition-all hover:border-white/10">
            <div className="flex items-center gap-3 mb-6 opacity-40">
              <Activity size={14} className="text-[#1d9bf0]" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.4em]">Default Agent</h3>
            </div>
            
            <div className="space-y-2">
              {agents.map((agent) => (
                <button
                  key={agent.name}
                  onClick={() => onSelectAgent(agent.name)}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    selectedAgent === agent.name
                      ? 'bg-white/10 border-white/20'
                      : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04]'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    selectedAgent === agent.name ? 'border-white bg-white' : 'border-white/30'
                  }`}>
                    {selectedAgent === agent.name && <div className="w-2 h-2 rounded-full bg-black" />}
                  </div>
                  <div className="text-left flex-1">
                    <p className="text-white font-bold">{agent.name}</p>
                    <p className="text-xs text-[#71717a]">{agent.description || 'No description'}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Security Notice */}
          <section className="bg-green-500/5 border border-green-500/10 rounded-[2rem] p-6">
            <div className="flex items-start gap-4">
              <CheckCircle2 size={20} className="text-green-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-white font-bold text-sm mb-1">Secure by Design</h4>
                <p className="text-[#71717a] text-xs leading-relaxed">
                  Your API keys and settings are stored locally in your browser. 
                  No credentials are sent to third-party servers. All AI processing 
                  is handled through your Heidi backend.
                </p>
              </div>
            </div>
          </section>

        </div>

        <div className="px-6 md:px-8 py-6 border-t border-white/5 bg-white/[0.02] flex items-center justify-between shrink-0">
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 px-6 py-3 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-red-500/20 transition-all active:scale-95"
          >
            <LogOut size={16} />
            Sign Out
          </button>
          
          <button 
            onClick={onClose}
            className="px-6 py-3 bg-white text-black rounded-xl text-xs font-black uppercase tracking-widest hover:bg-white/90 transition-all active:scale-95"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
};

export default SettingsModal;
