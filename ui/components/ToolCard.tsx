import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { ToolEvent } from '../types';

interface ToolCardProps {
  tool: ToolEvent;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool }) => {
  const [isExpanded, setIsExpanded] = useState(tool.status === 'running');

  // Auto-expand if running
  useEffect(() => {
    if (tool.status === 'running') setIsExpanded(true);
  }, [tool.status]);

  let icon = <Loader2 size={16} className="animate-spin text-purple-400" />;
  let borderColor = "border-purple-500/20";
  let bgColor = "bg-purple-500/5";

  if (tool.status === 'done') {
    icon = <CheckCircle size={16} className="text-green-400" />;
    borderColor = "border-green-500/20";
    bgColor = "bg-green-500/5";
  } else if (tool.status === 'error') {
    icon = <AlertCircle size={16} className="text-red-400" />;
    borderColor = "border-red-500/20";
    bgColor = "bg-red-500/5";
  }

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} overflow-hidden transition-all duration-300 mt-2 max-w-2xl`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {icon}
          <span className="text-sm font-medium text-slate-200">{tool.title}</span>
        </div>
        {isExpanded ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 pt-0 animate-in slide-in-from-top-1">
          <div className="bg-black/20 rounded border border-white/5 p-3 font-mono text-xs text-slate-400 max-h-60 overflow-y-auto custom-scrollbar">
            {tool.lines.length === 0 ? (
               <span className="italic opacity-50">Waiting for output...</span>
            ) : (
               tool.lines.map((line, i) => (
                 <div key={i} className="whitespace-pre-wrap break-words border-l-2 border-transparent hover:border-white/10 pl-1">{line}</div>
               ))
            )}
            {tool.status === 'running' && (
               <div className="w-1.5 h-3 bg-purple-500/50 animate-pulse mt-1 inline-block"></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolCard;
