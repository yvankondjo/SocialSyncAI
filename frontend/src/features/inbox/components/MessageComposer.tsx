import React, { useState } from 'react';

export interface MessageComposerProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function MessageComposer({ onSend, disabled }: MessageComposerProps) {
  const [text, setText] = useState<string>('');

  const send = () => {
    const value = text.trim();
    if (!value || disabled) return;
    onSend(value);
    setText('');
  };

  const onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="border-t border-gray-200 p-3 bg-white">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Écrire un message... (Ctrl/⌘+Entrée pour envoyer)"
            className="flex-1 resize-none min-h-[44px] max-h-40 rounded-md border border-gray-200 bg-[#F9FAFB] px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#C7D2FE]"
            rows={2}
            aria-label="Composer un message"
            disabled={!!disabled}
          />
          <button
            onClick={send}
            disabled={disabled || text.trim() === ''}
            className="inline-flex items-center gap-2 rounded-md bg-[#6366F1] text-white text-sm px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#5558e6] transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Envoyer
          </button>
        </div>
      </div>
    </div>
  );
}