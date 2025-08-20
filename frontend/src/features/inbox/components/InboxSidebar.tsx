import React from 'react';
import { Channel } from '../types/inbox';

const channels: Channel[] = ['instagram', 'whatsapp', 'reddit'];

function getIcon(channel: Channel): string {
  return `/logos/${channel}.svg`;
}

export interface InboxSidebarProps {
  availableChannels?: Channel[];
  selectedChannel: Channel | 'all';
  onSelectChannel: (channel: Channel | 'all') => void;
}

export function InboxSidebar({
  availableChannels = [],
  selectedChannel,
  onSelectChannel,
}: InboxSidebarProps) {
  return (
    <aside className="w-[220px] bg-white border-r border-gray-200 h-full p-3 flex flex-col gap-6">
      <div>
        <div className="text-sm font-medium text-gray-900 mb-2 px-2">Canaux</div>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => onSelectChannel('all')}
            className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm ${
              selectedChannel === 'all' ? 'bg-[#EEF2FF] text-gray-900 font-medium' : 'hover:bg-[#F9FAFB] text-gray-800'
            }`}
            aria-pressed={selectedChannel === 'all'}
          >
            Tous les canaux
          </button>
          <hr className="my-1" />
          {channels.map((ch) => {
            const isAvailable = availableChannels.includes(ch);
            const isSelected = selectedChannel === ch;
            return (
              <button
                key={ch}
                onClick={() => isAvailable && onSelectChannel(ch)}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm ${
                  isAvailable ? (isSelected ? 'bg-[#EEF2FF] text-gray-900 font-medium' : 'hover:bg-[#F9FAFB] text-gray-800') : 'opacity-40 cursor-not-allowed'
                }`}
                aria-pressed={isSelected}
                disabled={!isAvailable}
              >
                <img src={getIcon(ch)} alt={ch} className="w-4 h-4" />
                <span className="capitalize">{ch}</span>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}