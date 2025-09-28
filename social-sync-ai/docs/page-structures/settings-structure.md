# Settings Pages Structure Documentation

## app/settings/page.tsx
**Purpose**: Redirect page to AI settings
**Components Used**:
- `redirect` from "next/navigation"

**Structure**:
- Simple redirect to `/settings/ai`
- No UI components

## app/settings/ai/page.tsx
**Purpose**: AI model configuration and behavior settings
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Textarea`, `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`, `Switch`, `Slider`, `Label`, `Badge`
- **Icons**: `Bot`, `Save`, `RotateCcw`, `Shield`, `Zap` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, Reset/Save buttons
- **Unsaved Changes Alert**: Yellow warning when changes exist
- **Model Configuration Card**:
  - Default model selection
  - Fallback model selection
  - Temperature slider (0-2)
  - Max tokens slider (256-4096)
  - Response timeout slider (5-120s)
- **Behavior & Safety Card**:
  - Disable AI toggle (NEW)
  - Answer mode selection (FAQ Only, Hybrid, AI Only)
  - Safe replies toggle
- **System Instructions Card**:
  - System prompt textarea
  - Custom instructions textarea

**Settings Object Structure**:
\`\`\`typescript
{
  defaultModel: string
  temperature: number[]
  maxTokens: number[]
  safeReplies: boolean
  fallbackModel: string
  responseTimeout: number[]
  answerMode: "faq_only" | "hybrid" | "llm_only"
  systemPrompt: string
  customInstructions: string
  disableAI: boolean // NEW FEATURE
}
\`\`\`

**Available Models**:
- GPT-4o (OpenAI, High cost)
- GPT-4 (OpenAI, High cost)
- GPT-3.5 Turbo (OpenAI, Medium cost)
- Gemini Pro (Google, Medium cost)
- Claude 3 (Anthropic, High cost)
- Llama 2 (Meta, Low cost)

**Removed Features** (as per requirements):
- Language support configuration
- Multi-language settings
- Localization options

**Added Features** (as per requirements):
- Disable AI toggle to prevent responses
- Enhanced model selection with cost indicators
- Improved behavior controls

## app/settings/chat-interface/page.tsx
**Purpose**: Chat widget appearance and behavior customization
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Input`, `Textarea`, `Switch`, `Select`, `Badge`, `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger`
- **Icons**: `MessageCircle`, `Palette`, `Settings`, `Eye`, `Save`, `RotateCcw`, `Upload` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, action buttons
- **Tabs Navigation**: Appearance, Messages, Behavior
- **Live Preview Panel**: Real-time widget preview
- **Configuration Sections**:
  - Theme and colors
  - Typography settings
  - Message templates
  - Behavior toggles
  - File upload settings

## app/settings/custom-domains/page.tsx
**Purpose**: Custom domain management and SSL configuration
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Input`, `Badge`, `Dialog`, `Alert`, `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger`
- **Icons**: `Globe`, `Plus`, `Settings`, `Trash2`, `CheckCircle`, `AlertTriangle`, `Copy`, `ExternalLink`, `Shield` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, Add Domain button
- **Domains List**: Cards with domain details
- **DNS Configuration**: Step-by-step setup
- **SSL Status**: Certificate management
- **Verification Process**: Domain ownership verification

## Shared Settings Patterns
All settings pages use:
- Consistent layout with Sidebar + Header
- Card-based organization
- Save/Reset button patterns
- Form validation
- Loading states
- Success/Error feedback
- Responsive design
- Dark theme compatibility

## State Management Patterns
- `useState` for form data
- `hasChanges` tracking for save/reset buttons
- Loading states for async operations
- Error handling for API calls
- Form validation before submission

## Key Features Across Settings
- **Persistence**: All settings saved to backend
- **Validation**: Form validation before save
- **Reset**: Ability to reset to defaults
- **Preview**: Live preview where applicable
- **Responsive**: Mobile-friendly interfaces
- **Accessibility**: Proper labels and ARIA attributes
