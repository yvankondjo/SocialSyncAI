# Sources (Data & FAQ) Structure Documentation

## app/sources/data/page.tsx
**Purpose**: File upload and data source management (simplified version)
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Button`, `Card`, `CardContent`, `Badge`, `Input`
- **Icons**: `Database`, `RefreshCw`, `Settings`, `FileText`, `Upload`, `CheckCircle`, `AlertCircle`, `Clock`, `Search` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, Upload Files button
- **Search Bar**: File search functionality
- **Uploaded Files Section**: Single card with file list
  - File name, size, type, upload date
  - Status badges (indexed, processing)
  - Settings button per file

**Removed Features** (as per requirements):
- Connected Sources section
- Database integrations (Supabase, Google Drive, S3)
- Sync functionality
- Import/Export options

**Remaining Features**:
- File upload interface
- File management
- Search functionality
- Status tracking

## app/sources/faq/page.tsx
**Purpose**: FAQ management with multiple questions per answer
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Button`, `Card`, `CardContent`, `Input`, `Textarea`, `Badge`, `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `Label`, `Switch`
- **Icons**: `HelpCircle`, `Plus`, `Search`, `Edit3`, `Trash2`, `Tag`, `CheckCircle`, `XCircle` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, Add FAQ button
- **Filters Row**: 
  - Search input (questions, answers, tags)
  - Status filter dropdown (All, Active, Inactive)
- **FAQ List**: Cards with FAQ details
  - Multiple questions per FAQ (new feature)
  - Single answer
  - Tags with badges
  - Source indicator (manual, chat_edit, import)
  - Status indicator (active/inactive)
  - Edit and Delete buttons
- **Edit/Add Dialogs**: Modals for FAQ management

**FAQ Object Structure**:
\`\`\`typescript
{
  id: string
  questions: string[] // Multiple questions per answer
  answer: string
  tags: string[]
  isActive: boolean
  updatedAt: string
  source: "manual" | "chat_edit" | "import"
}
\`\`\`

**Key Features Added** (as per requirements):
- Multiple questions per single answer
- Add/Remove question functionality in dialogs
- Dynamic question management

**Removed Features** (as per requirements):
- Language selection/management
- CSV Import/Export functionality
- Multi-language support

**Enhanced Features**:
- Improved question management
- Better tag system
- Source tracking
- Status management
- Search across questions, answers, and tags

## Shared Patterns
Both source pages use:
- Consistent layout with Sidebar + Header
- Search functionality
- Card-based item display
- Status badges with color coding
- Modal dialogs for editing
- Responsive grid layouts
- Dark theme compatibility
