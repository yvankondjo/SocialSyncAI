# Playground Pages Structure Documentation

## app/playground/page.tsx
**Purpose**: Main playground for testing AI models with configuration panel and chat interface
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Button`, `Card`, `CardContent`, `Textarea`, `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`, `Label`, `Slider`, `Badge`, `Input`
- **Icons**: `Send`, `Bot`, `User`, `RefreshCw` from "lucide-react"
- `Link` from "next/link"

**Structure**:
- **Left Panel (384px)**: Configuration sidebar
  - Agent status with trained badge
  - Save to agent button
  - Tabs: "Configure & test agents" and "Compare"
  - Model selection dropdown (GPT-4o, GPT-4, Gemini Pro, Claude 3)
  - Temperature slider (0-2, Reserved to Creative)
  - AI Actions section (empty state)
  - Instructions with system prompt textarea
- **Right Panel**: Chat interface
  - Chat header with timestamp and refresh
  - Messages area with user/assistant distinction
  - Chat input with send button
  - "Powered by Chatbase" branding

**State Management**:
- `messages`: Array of chat messages with role, content, timestamp
- `input`: Current input text
- `model`: Selected AI model
- `temperature`: Temperature slider value [0]
- `systemInstruction`: System prompt text
- `agentStatus`: Current agent status ("trained")

**Key Features**:
- Real-time chat simulation
- Model configuration
- System prompt editing
- Temperature adjustment
- Message history

## app/playground/compare/page.tsx
**Purpose**: Side-by-side comparison of two AI models
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Button`, `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Textarea`, `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`, `Badge`
- **Icons**: `MessageSquare`, `Send`, `RotateCcw`, `ArrowLeftRight`, `Download` from "lucide-react"

**Structure**:
- **Controls Row**: Title, Reset, Swap, Export buttons
- **Model Selection**: Two dropdowns for left/right models
- **Comparison Panels**: Two equal-width cards
  - Left Model (Model A)
  - Right Model (Model B)
  - Each with message history and performance metrics
- **Input Area**: Shared textarea and send button

**State Management**:
- `input`: Shared input for both models
- `leftModel`, `rightModel`: Selected models for comparison
- `conversations`: Object with left/right message arrays
- Messages include latency and token count

**Key Features**:
- Simultaneous model testing
- Performance comparison (latency, tokens)
- Model swapping functionality
- Export capability
- Reset conversations
- Shared input for fair comparison

## Shared Patterns
Both playground pages use:
- Consistent layout with Sidebar + Header
- Model selection with same options
- Message display with role-based styling
- Simulated AI responses with setTimeout
- Responsive design patterns
- Dark theme compatibility
