import clsx from 'clsx'

export function ChatBubble({ role, message, meta }: { role: 'seller_agent'|'client_agent'|'system', message: string, meta?: any }) {
  if (role === 'system') {
    return (
      <div className="flex justify-center my-4">
        <span className="bg-emerald-100 text-emerald-700 text-xs font-semibold px-4 py-1.5 rounded-full border border-emerald-200 shadow-sm">
          {message}
        </span>
      </div>
    )
  }

  const isSeller = role === 'seller_agent'

  return (
    <div className={clsx("flex gap-3 my-4", isSeller ? "justify-start slide-in-left" : "justify-end slide-in-right")}>
      {isSeller && (
        <div className="w-8 h-8 rounded-full bg-pink-400 text-white flex items-center justify-center font-bold font-display shadow-sm flex-shrink-0">S</div>
      )}
      
      <div className="flex flex-col gap-1 max-w-[80%]">
        <div className={clsx(
          "px-4 py-3 shadow-sm",
          isSeller 
            ? "bg-pink-100 border border-pink-200 rounded-2xl rounded-tl-sm text-charcoal" 
            : "bg-white border border-pink-200 rounded-2xl rounded-tr-sm text-charcoal"
        )}>
          <p className="text-sm leading-relaxed font-medium">{message}</p>
          {meta?.proposed_text && (
            <div className="mt-3 bg-white/70 border-l-4 border-pink-400 pl-3 py-2 rounded-r-lg">
              <p className="text-[10px] font-bold uppercase tracking-wider text-pink-500 mb-1">📝 Proposed Redline</p>
              <p className="text-sm italic text-slate leading-relaxed font-medium">"{meta.proposed_text}"</p>
            </div>
          )}
        </div>
        
        {meta && (
          <div className={clsx("flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted px-1", isSeller ? "justify-start" : "justify-end")}>
            <span>Clause {meta.clause_id}</span>
            <span>•</span>
            <span>{meta.action_type}</span>
            <span>•</span>
            <span>Turn {meta.turn_number}</span>
          </div>
        )}
      </div>

      {!isSeller && (
        <div className="w-8 h-8 rounded-full bg-slate text-white flex items-center justify-center font-bold font-display shadow-sm flex-shrink-0">C</div>
      )}
    </div>
  )
}
