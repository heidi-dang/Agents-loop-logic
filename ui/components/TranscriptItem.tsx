import React, { useState } from 'react';
import { RunEvent } from '../types';
import { AlertCircle, Sparkles, Copy, Check } from 'lucide-react';

interface TranscriptItemProps {
  event: RunEvent;
}

const TranscriptItem = React.memo(({ event }: TranscriptItemProps) => {
  const [copied, setCopied] = useState(false);

  if (!event.message) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(event.message || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="flex gap-4 max-w-[90%] animate-in fade-in slide-in-from-bottom-2 duration-300 group">
      <div className="flex-shrink-0 mt-1">
        <div className="w-10 h-10 rounded-xl bg-black/40 flex items-center justify-center border border-white/10 shadow-lg overflow-hidden">
          {event.type === 'error'
            ? <AlertCircle size={20} className="text-red-400"/>
            : <Sparkles size={20} className="text-purple-400" />
          }
        </div>
      </div>
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-purple-300 uppercase tracking-wider">{event.type || 'System'}</span>
          <span className="text-[10px] text-slate-500 font-mono">{event.ts ? new Date(event.ts).toLocaleTimeString() : ''}</span>
        </div>

        <div className={`text-sm leading-relaxed p-4 rounded-2xl rounded-tl-sm border shadow-sm backdrop-blur-sm relative group/message ${
            event.type === 'error' ? 'bg-red-950/30 border-red-500/30 text-red-200' :
            'bg-[#1a162e]/80 border-white/5 text-slate-200 group-hover:bg-[#1f1b35] transition-colors'
        }`}>
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/40 hover:bg-black/60 text-slate-400 hover:text-white transition-all opacity-0 group-hover/message:opacity-100 focus:opacity-100"
              aria-label={copied ? "Copied" : "Copy message"}
              title="Copy message"
            >
              {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
            </button>
            <pre className="whitespace-pre-wrap font-sans">{event.message}</pre>
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  return prevProps.event.ts === nextProps.event.ts &&
         prevProps.event.message === nextProps.event.message &&
         prevProps.event.type === nextProps.event.type;
});

export default TranscriptItem;
