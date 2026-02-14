import React from 'react';

const ThinkingBubble: React.FC = () => {
  return (
    <div className="flex gap-4 max-w-[90%] animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex-shrink-0 mt-1">
        <div className="w-10 h-10 rounded-xl bg-black/40 flex items-center justify-center border border-white/10 shadow-lg overflow-hidden relative">
          <div className="w-2 h-2 bg-purple-500 rounded-full animate-ping absolute opacity-75"></div>
          <div className="w-2 h-2 bg-purple-400 rounded-full relative"></div>
        </div>
      </div>
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
           <span className="text-xs font-bold text-purple-300 uppercase tracking-wider">Heidi</span>
        </div>
        <div className="p-4 rounded-2xl rounded-tl-sm border border-white/5 bg-[#1a162e]/80 backdrop-blur-sm">
           <div className="flex flex-col gap-2 w-full max-w-[200px]">
              <div className="h-2 bg-white/10 rounded w-full animate-pulse"></div>
              <div className="h-2 bg-white/10 rounded w-2/3 animate-pulse delay-75"></div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default ThinkingBubble;
