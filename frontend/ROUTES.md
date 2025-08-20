# Routes Backend nécessaires pour l’Inbox

- GET /api/inbox/conversations?channels=instagram,linkedin&search=...
  - Retourne: Conversation[] (id, participants, channel, lastMessageAt, lastMessageSnippet, unreadCount)

- GET /api/inbox/conversations/:id/messages?cursor=...
  - Retourne: { messages: Message[], nextCursor?: string }

- POST /api/inbox/conversations/:id/messages
  - Body: { text: string, attachments?: string[] }
  - Retourne: Message

- PATCH /api/inbox/conversations/:id/read
  - Body: { upToMessageId?: string }
  - Retourne: { success: true }

- GET /api/inbox/channels
  - Retourne: Channel[] auxquels l’utilisateur a accès

- WS /realtime/inbox
  - Événements: message.created, conversation.updated, typing.start, typing.stop
  - Auth: token utilisateur

Types utilisés

- Conversation: { id: string; participants: Participant[]; channel: Channel; lastMessageAt: string; lastMessageSnippet: string; unreadCount: number }
- Participant: { id: string; displayName: string; avatarUrl?: string }
- Message: { id: string; conversationId: string; authorId: string; text: string; createdAt: string; attachments?: string[] }
- Channel: 'instagram' | 'tiktok' | 'twitter' | 'facebook' | 'youtube' | 'reddit' | 'whatsapp' | 'discord' | 'email' | 'linkedin'
