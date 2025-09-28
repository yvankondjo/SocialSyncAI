# Connect Integrations Structure Documentation

## app/connect/page.tsx
**Purpose**: Social media integrations and web widget management
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Badge`, `Switch`, `Input`, `Textarea`, `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `Label`
- **Icons**: `Globe`, `MessageCircle`, `Instagram`, `Twitter`, `CheckCircle`, `AlertCircle`, `Settings`, `Copy`, `Eye`, `Palette` from "lucide-react"

**Structure**:
- **Header Section**: Title and description
- **Integrations Grid**: 2x2 grid of integration cards
  - Meta (Instagram & Facebook)
  - X (Twitter)
  - WhatsApp Business
  - Web Widget
- **Web Widget Section**: Installation and preview
  - Installation code snippet
  - Live widget preview
  - Customization buttons

**Integration Object Structure**:
\`\`\`typescript
{
  id: string
  name: string
  description: string
  icon: LucideIcon
  status: "connected" | "disconnected" | "needs_setup"
  accounts: string[]
  scopes: string[]
  lastSync: string | null
}
\`\`\`

**Widget Configuration Structure**:
\`\`\`typescript
{
  theme: string
  position: "bottom-right" | "bottom-left" | "top-right" | "top-left"
  welcomeMessage: string
  placeholder: string
  showAvatar: boolean
  showBranding: boolean
}
\`\`\`

**Key Features**:
- **Integration Management**:
  - Connection status indicators
  - Account linking
  - Permission scopes display
  - Last sync timestamps
  - Connect/Disconnect functionality

- **Web Widget**:
  - Installation code generation
  - Live preview with theme
  - Customization dialog
  - Theme selection (4 predefined themes)
  - Position configuration
  - Message customization
  - Branding toggle

- **Widget Themes**:
  - Default (Purple)
  - Ocean Blue
  - Forest Green
  - Sunset Orange

**Integration Status System**:
- **Connected**: Green checkmark, functional integration
- **Needs Setup**: Yellow warning, requires configuration
- **Disconnected**: Gray circle, not connected

**Widget Installation**:
- JavaScript snippet generation
- Dynamic configuration injection
- Copy-to-clipboard functionality
- Preview with real-time updates

## Widget Customization Dialog
**Components Used**:
- Theme selector with color previews
- Position grid selector
- Welcome message textarea
- Placeholder input
- Avatar toggle switch
- Branding toggle switch

**Features**:
- Real-time preview updates
- Theme color visualization
- Position selection grid
- Message customization
- Toggle controls for features
- Save/Cancel actions

## Social Media Integrations
**Supported Platforms**:
1. **Meta (Instagram & Facebook)**
   - Direct message responses
   - Comment management
   - Page messaging

2. **X (Twitter)**
   - Mention responses
   - Direct message handling
   - Tweet interactions

3. **WhatsApp Business**
   - Business API integration
   - Customer support messaging
   - Automated responses

**Permission Scopes**:
- Message reading/writing
- Profile access
- Business profile management
- Direct message handling

## Technical Implementation
- OAuth integration flows
- API key management
- Webhook configuration
- Real-time sync status
- Error handling and retry logic
