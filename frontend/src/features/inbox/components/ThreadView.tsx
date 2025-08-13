import React, { useEffect, useRef } from 'react';
import { Message, Participant } from '../types/inbox';

export interface ThreadViewProps {
  messages: Message[];
  participants: Record<string, Participant>;
  currentUserId: string;
}

export function ThreadView({ messages, participants, currentUserId }: ThreadViewProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 bg-white">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        {messages.map((m) => {
          const isMine = m.authorId === currentUserId;
          const author = participants[m.authorId];
          return (
            <div key={m.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
              <div className={`rounded-2xl px-3 py-2 text-sm ${isMine ? 'bg-[#EEF2FF] text-gray-900' : 'bg-[#F3F4F6] text-gray-900'}`}>
                <div className="text-[12px] text-gray-500 mb-0.5">{author?.displayName ?? 'Utilisateur'}</div>
                <div>{m.text}</div>
                <div className="text-[10px] text-gray-400 mt-1 text-right">
                  {new Date(m.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}