# Activity & Chat Structure Documentation

## app/activity/page.tsx
**Purpose**: Redirect page to main chat interface
**Components Used**:
- `redirect` from "next/navigation"

**Structure**:
- Simple redirect to `/activity/chat`
- No UI components

## app/activity/chat/page.tsx
**Purpose**: Main chat management interface with conversation list and message editing
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Button`, `Card`, `CardContent`, `Input`, `Textarea`, `Badge`, `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `Switch`, `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`
- **Icons**: `MessageSquare`, `Search`, `Filter`, `MoreHorizontal`, `Edit3`, `Trash2`, `User`, `Bot`, `Clock`, `CheckCircle`, `XCircle`, `AlertTriangle`, `Plus`, `Save`, `X` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, New Chat button
- **Filters Row**: 
  - Search input with magnifying glass icon
  - Status filter dropdown (All, Active, Resolved, Escalated)
  - Source filter dropdown (All, Web Widget, Instagram, WhatsApp, etc.)
  - Date range picker
- **Conversations List**: Cards with conversation details
  - User info and timestamp
  - Message preview
  - Status badges
  - Action buttons (Edit, Delete, Toggle Auto-Response)
- **Edit Dialog**: Modal for editing AI responses

**State Management**:
- `searchQuery`: Search filter text
- `statusFilter`: Selected status filter
- `sourceFilter`: Selected source filter
- `editingMessage`: Currently editing message object
- `conversations`: Array of conversation objects

**Conversation Object Structure**:
\`\`\`typescript
{
  id: string
  user: { name: string, avatar?: string }
  lastMessage: string
  timestamp: string
  status: "active" | "resolved" | "escalated"
  source: "web" | "instagram" | "whatsapp" | "facebook"
  messageCount: number
  isAutoResponseEnabled: boolean
  messages: Array<{
    id: string
    role: "user" | "assistant"
    content: string
    timestamp: string
    isEdited?: boolean
  }>
}
\`\`\`

**Key Features**:
- Conversation filtering and search
- AI response editing with save/cancel
- Auto-response toggle per conversation
- Status management (Active, Resolved, Escalated)
- Multi-source support (Web, Instagram, WhatsApp, Facebook)
- Message history with edit indicators
- Real-time conversation updates

**Removed Features** (as per requirements):
- Close conversation functionality
- Bulk actions
- Export options

**Added Features** (as per requirements):
- Auto-response toggle per conversation
- Enhanced message editing
- Improved filtering system
