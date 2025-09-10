'use client';

import React, { useMemo, useState } from 'react';
import { ConversationList } from '../components/ConversationList';
import { ThreadView } from '../components/ThreadView';
import { InboxSidebar } from '../components/InboxSidebar';
import { MessageComposer } from '../components/MessageComposer';
import { Channel, Conversation, Message, Participant } from '../types/inbox';

// Mock data pour la démo
function makeParticipants(): Record<string, Participant> {
  const p: Participant[] = [
    { id: 'u1', displayName: 'Alice Martin' },
    { id: 'u2', displayName: 'Bob Dupont' },
    { id: 'me', displayName: 'Moi' },
  ];
  return Object.fromEntries(p.map((x) => [x.id, x]));
}

function makeConversations(): Conversation[] {
  return [
    {
      id: 'c1',
      participants: [{ id: 'u1', displayName: 'Alice Martin' }],
      channel: 'instagram',
      lastMessageAt: new Date().toISOString(),
      lastMessageSnippet: 'Super, merci pour la photo !',
      unreadCount: 2,
    },
    {
      id: 'c2',
      participants: [{ id: 'u2', displayName: 'Support Technique' }],
      channel: 'whatsapp',
      lastMessageAt: new Date(Date.now() - 3600000).toISOString(),
      lastMessageSnippet: 'Votre ticket #A4B2 a été mis à jour.',
      unreadCount: 0,
    },
     {
      id: 'c3',
      participants: [{ id: 'u3', displayName: 'r/reactjs Mod' }],
      channel: 'reddit',
      lastMessageAt: new Date(Date.now() - 86400000).toISOString(),
      lastMessageSnippet: 'Votre post a été approuvé.',
      unreadCount: 1,
    },
  ];
}

function makeMessages(conversationId: string): Message[] {
  const now = Date.now();
  if (conversationId === 'c1') {
    return [
      { id: 'm1', conversationId: 'c1', authorId: 'u1', text: 'Salut !', createdAt: new Date(now - 600000).toISOString() },
      { id: 'm2', conversationId: 'c1', authorId: 'me', text: 'Bonjour Alice, oui bien reçu.', createdAt: new Date(now - 300000).toISOString() },
    ];
  }
  return [
    { id: 'm3', conversationId: 'c2', authorId: 'u2', text: 'On se parle demain ?', createdAt: new Date(now - 400000).toISOString() },
    { id: 'm4', conversationId: 'c2', authorId: 'me', text: 'Parfait, à demain.', createdAt: new Date(now - 200000).toISOString() },
  ];
}

export default function InboxPage() {
  const participants = useMemo(makeParticipants, []);
  const [conversations] = useState<Conversation[]>(makeConversations());
  const [selectedConversationId, setSelectedConversationId] = useState<string>('c1');
  const [selectedChannel, setSelectedChannel] = useState<Channel | 'all'>('all');
  const currentUserId = 'me';

  const availableChannels = useMemo<Channel[]>(() => {
    const all = new Set<Channel>();
    conversations.forEach((c) => all.add(c.channel));
    return Array.from(all);
  }, [conversations]);

  const filteredConversations = useMemo(() => {
    const sorted = conversations
      .slice()
      .sort((a, b) => new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime());
    if (selectedChannel === 'all') return sorted;
    return sorted.filter((c) => c.channel === selectedChannel);
  }, [conversations, selectedChannel]);

  const messages = useMemo(() => {
    if (!selectedConversationId) return [];
    return makeMessages(selectedConversationId);
  }, [selectedConversationId]);

  const onSend = (text: string) => {
    const newMessage: Message = {
      id: `m-${Date.now()}`,
      conversationId: selectedConversationId,
      authorId: currentUserId,
      text,
      createdAt: new Date().toISOString(),
      attachments: [],
    };
    console.log('SEND', newMessage);
  };

  return (
    <main className="flex-1 overflow-hidden bg-white">
      <div className="h-full flex">
        <InboxSidebar
          availableChannels={availableChannels}
          selectedChannel={selectedChannel}
          onSelectChannel={setSelectedChannel}
        />
        <ConversationList
          items={filteredConversations}
          activeId={selectedConversationId}
          onSelect={setSelectedConversationId}
        />
        <div className="flex-1 flex flex-col">
          {selectedConversationId ? (
            <>
              <ThreadView
                messages={messages}
                participants={participants}
                currentUserId={currentUserId}
              />
              <MessageComposer onSend={onSend} />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              Sélectionnez une conversation pour commencer
            </div>
          )}
        </div>
      </div>
    </main>
  );
}



