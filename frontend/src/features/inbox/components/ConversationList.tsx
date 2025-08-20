import React, { useMemo, useState } from 'react';
import { Conversation, Channel } from '../types/inbox';
import { ClientTime } from './ClientTime';

const channelLabel: Record<Channel, string> = {
  instagram: 'Instagram',
  tiktok: 'TikTok',
  twitter: 'X',
  facebook: 'Facebook',
  youtube: 'YouTube',
  reddit: 'Reddit',
  whatsapp: 'WhatsApp',
  discord: 'Discord',
  email: 'Email',
  linkedin: 'LinkedIn',
};

function getChannelIconPath(channel: Channel): string {
  return `/logos/${channel}.svg`;
}

function getInitial(text: string | undefined): string {
  if (!text || text.trim().length === 0) return '?';
  return text.trim().charAt(0).toUpperCase();
}

export function ConversationList({
  items,
  activeId,
  onSelect,
}: {
  items: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState<string>('');

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((c) => {
      const name = c.participants[0]?.displayName?.toLowerCase() ?? '';
      const snippet = c.lastMessageSnippet?.toLowerCase() ?? '';
      return name.includes(q) || snippet.includes(q);
    });
  }, [items, query]);

  const handleIconError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.onerror = null;
    e.currentTarget.src = '/logos/all.svg';
  };

  return (
    <div className="w-[340px] bg-white border-r border-gray-200 h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-200">
        <label className="relative block">
          <span className="absolute inset-y-0 left-3 flex items-center text-gray-400">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M11 19C15.4183 19 19 15.4183 19 11C19 6.58172 15.4183 3 11 3C6.58172 3 3 6.58172 3 11C3 15.4183 6.58172 19 11 19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher des conversations..."
            className="w-full pl-9 pr-3 py-2.5 rounded-md border border-gray-200 bg-[#F9FAFB] text-sm text-gray-800 placeholder:text-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#C7D2FE]"
            aria-label="Rechercher"
          />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredItems.length === 0 ? (
          <div className="px-4 py-6 text-sm text-gray-500">Aucun résultat</div>
        ) : (
          filteredItems.map((c) => {
            const name = c.participants[0]?.displayName || 'Inconnu';
            const isActive = activeId === c.id;
            return (
              <button
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`w-full text-left px-4 py-3 border-b border-[#F3F4F6] transition-colors ${
                  isActive ? 'bg-[#EEF2FF] ring-1 ring-[#6366F1]' : 'hover:bg-[#F9FAFB]'
                }`}
                aria-current={isActive ? 'true' : undefined}
                aria-label={`Ouvrir la conversation avec ${name}`}
              >
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center text-sm font-medium">
                      {getInitial(name)}
                    </div>
                    <img
                      src={getChannelIconPath(c.channel)}
                      onError={handleIconError}
                      alt={channelLabel[c.channel]}
                      className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-white border border-gray-200 p-0.5"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-[14px] text-gray-900 font-medium truncate" title={name}>
                        {name}
                      </span>
                      <span className="text-[11px] text-gray-400 ml-2 whitespace-nowrap">
                        <ClientTime
                          date={c.lastMessageAt}
                          options={{ hour: '2-digit', minute: '2-digit' }}
                        />
                      </span>
                    </div>

                    <div className="mt-0.5 text-[13px] text-gray-600 truncate" title={c.lastMessageSnippet}>
                      {c.lastMessageSnippet}
                    </div>

                    <div className="mt-1 flex items-center gap-2">
                      <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                        <img
                          src={getChannelIconPath(c.channel)}
                          onError={handleIconError}
                          alt=""
                          className="w-3 h-3"
                        />
                        {channelLabel[c.channel]}
                      </span>
                      {c.unreadCount > 0 && (
                        <span className="text-[11px] font-semibold text-white bg-[#3B82F6] rounded-[10px] px-1.5 min-w-[16px] h-4 inline-flex items-center justify-center">
                          {c.unreadCount}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}