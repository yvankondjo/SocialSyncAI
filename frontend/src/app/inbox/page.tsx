"use client";

import React, { useMemo, useState } from 'react';
import { Channel, Participant } from '@/features/inbox/types/inbox';
import { ConversationList } from '@/features/inbox/components/ConversationList';
import { InboxSidebar } from '@/features/inbox/components/InboxSidebar';
import { ThreadView } from '@/features/inbox/components/ThreadView';
import { MessageComposer } from '@/features/inbox/components/MessageComposer';
import { useConversations, useMessages } from '@/features/inbox/hooks/useInbox';
import { createClient } from '@/lib/supabase/client';

export const dynamic = 'force-dynamic';

function makeParticipants(): Record<string, Participant> {
  const p: Participant[] = [{ id: 'me', displayName: 'Moi' }];
  return Object.fromEntries(p.map((x) => [x.id, x]));
}

export default function InboxPage() {
  const participants = useMemo(makeParticipants, []);
  const [selectedChannel, setSelectedChannel] = useState<Channel | 'all'>('all');
  const { data: conversations = [] } = useConversations({ channel: selectedChannel, status: 'open' });
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>(undefined);
  const { data: messages = [] } = useMessages(selectedConversationId);
  const currentUserId = 'me';

  const availableChannels = useMemo<Channel[]>(() => {
    const all = new Set<Channel>();
    conversations.forEach((c) => all.add(c.channel));
    return Array.from(all);
  }, [conversations]);

  const onSend = async (text: string) => {
    if (!selectedConversationId) return;
    try {
      const supabase = createClient();
      await supabase.from('conversations').update({ metadata: { auto_reply_enabled: autoReply } }).eq('id', selectedConversationId);
      await supabase.from('conversation_messages').insert({
        conversation_id: selectedConversationId,
        direction: 'outbound',
        message_type: 'text',
        content: text,
        is_from_agent: true,
      });
    } catch (e) {
      console.error(e);
    }
  };

  const [autoReply, setAutoReply] = useState<boolean>(false);

  return (
    <div className="h-[100dvh] flex bg-white">
      <InboxSidebar
        availableChannels={availableChannels}
        selectedChannel={selectedChannel}
        onSelectChannel={setSelectedChannel}
        autoReplyEnabled={autoReply}
        onToggleAutoReply={setAutoReply}
      />

      <ConversationList
        items={conversations}
        activeId={selectedConversationId}
        onSelect={setSelectedConversationId as (id: string) => void}
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
