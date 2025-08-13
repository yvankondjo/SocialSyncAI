import React from 'react';
import { Channel } from '../types/inbox';

const channels: Channel[] = [
  'instagram',
  'tiktok',
  'twitter',
  'facebook',
  'youtube',
  'reddit',
  'whatsapp',
  'discord',
  'email',
  'linkedin',
];

function getIcon(channel: Channel): string {
  return `/logos/${channel}.svg`;
}

export interface InboxSidebarProps {
  availableChannels: Channel[];
  selectedChannels: Channel[];
  onToggleChannel: (channel: Channel) => void;
}

export function InboxSidebar({ availableChannels, selectedChannels, onToggleChannel }: InboxSidebarProps) {
  return (
    <aside className="w-[220px] bg-white border-r border-gray-200 h-full p-3">
      <div className="text-sm font-medium text-gray-900 mb-2">Canaux</div>
      <div className="flex flex-col gap-1">
        {channels.map((ch) => {
          const isAvailable = availableChannels.includes(ch);
          const isSelected = selectedChannels.includes(ch);
          return (
            <button
              key={ch}
              onClick={() => isAvailable && onToggleChannel(ch)}
              className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm ${
                isAvailable ? (isSelected ? 'bg-[#EEF2FF] text-gray-900' : 'hover:bg-[#F9FAFB] text-gray-800') : 'opacity-40 cursor-not-allowed'
              }`}
              aria-pressed={isSelected ? 'true' : 'false'}
            >
              <img src={getIcon(ch)} alt={ch} className="w-4 h-4" />
              <span className="capitalize">{ch}</span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}