import React from 'react';
import { Channel } from '../types/inbox';

const channels: Channel[] = ['instagram', 'whatsapp'];

function getIcon(channel: Channel): string {
  return `/logos/${channel}.svg`;
}

export interface InboxSidebarProps {
  availableChannels?: Channel[];
  selectedChannel: Channel | 'all';
  onSelectChannel: (channel: Channel | 'all') => void;
  autoReplyEnabled?: boolean;
  onToggleAutoReply?: (value: boolean) => void;
}

export function InboxSidebar({
  availableChannels = [],
  selectedChannel,
  onSelectChannel,
  autoReplyEnabled = false,
  onToggleAutoReply,
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

      <div>
        <div className="text-sm font-medium text-gray-900 mb-2 px-2">Réponse automatique</div>
        <label className="flex items-center justify-between px-2 py-1.5 text-sm">
          <span>IA On/Off</span>
          <button
            onClick={() => onToggleAutoReply && onToggleAutoReply(!autoReplyEnabled)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${autoReplyEnabled ? 'bg-[#6366F1]' : 'bg-gray-300'}`}
            aria-pressed={autoReplyEnabled}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${autoReplyEnabled ? 'translate-x-4' : 'translate-x-1'}`}
            />
          </button>
        </label>
      </div>
    </aside>
  );
}