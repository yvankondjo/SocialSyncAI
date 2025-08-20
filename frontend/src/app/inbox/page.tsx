"use client";

import React, { useMemo, useState } from 'react';
import { Conversation, Channel, Message, Participant } from '@/features/inbox/types/inbox';
import { ConversationList } from '@/features/inbox/components/ConversationList';
import { InboxSidebar } from '@/features/inbox/components/InboxSidebar';
import { ThreadView } from '@/features/inbox/components/ThreadView';
import { MessageComposer } from '@/features/inbox/components/MessageComposer';

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
      lastMessageSnippet: 'Bonjour, avez-vous reçu mon message ?',
      unreadCount: 2,
    },
    {
      id: 'c2',
      participants: [{ id: 'u2', displayName: 'Bob Dupont' }],
      channel: 'linkedin',
      lastMessageAt: new Date().toISOString(),
      lastMessageSnippet: 'Merci pour votre retour !',
      unreadCount: 0,
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
  const [selectedChannels, setSelectedChannels] = useState<Channel[]>(['instagram', 'linkedin']);
  const currentUserId = 'me';

  const availableChannels = useMemo<Channel[]>(() => {
    const all = new Set<Channel>();
    conversations.forEach((c) => all.add(c.channel));
    return Array.from(all);
  }, [conversations]);

  const filteredConversations = useMemo(() => {
    return conversations.filter((c) => selectedChannels.includes(c.channel));
  }, [conversations, selectedChannels]);

  const messages = useMemo(() => makeMessages(selectedConversationId), [selectedConversationId]);

  const onToggleChannel = (channel: Channel) => {
    setSelectedChannels((prev) => (prev.includes(channel) ? prev.filter((c) => c !== channel) : [...prev, channel]));
  };

  const onSend = (text: string) => {
    const newMessage: Message = {
      id: `m-${Date.now()}`,
      conversationId: selectedConversationId,
      authorId: currentUserId,
      text,
      createdAt: new Date().toISOString(),
      attachments: [],
    };
    // Pour la démo, on ne persiste pas, on mettrait à jour le thread côté API en prod
    // et on rafraîchirait la liste des conversations (snippet/unread)
    console.log('SEND', newMessage);
  };

  return (
    <div className="h-[100dvh] flex bg-white">
      <InboxSidebar
        availableChannels={availableChannels}
        selectedChannels={selectedChannels}
        onToggleChannel={onToggleChannel}
      />

      <ConversationList
        items={filteredConversations}
        activeId={selectedConversationId}
        onSelect={setSelectedConversationId}
      />

      <div className="flex-1 flex flex-col">
        <ThreadView
          messages={messages}
          participants={participants}
          currentUserId={currentUserId}
        />
        <MessageComposer onSend={onSend} />
      </div>
    </div>
  );
}
