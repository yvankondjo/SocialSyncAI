# Layout Structure Documentation

## Core Layout Components

### app/layout.tsx
**Purpose**: Root layout with global configuration
**Components Used**:
- `GeistSans`, `GeistMono` from "geist/font/sans" and "geist/font/mono"
- `Analytics` from "@vercel/analytics/next"
- `Suspense` from "react"

**Structure**:
- HTML with dark theme by default
- Font configuration with Geist Sans and Mono
- Analytics integration
- Global CSS import

### components/sidebar.tsx
**Purpose**: Main navigation sidebar with collapsible functionality
**Components Used**:
- `useState` from "react"
- `Link` from "next/link"
- `usePathname` from "next/navigation"
- `cn` from "@/lib/utils"
- `Button` from "@/components/ui/button"
- **Icons**: `PlayCircle`, `Activity`, `MessageSquare`, `Database`, `HelpCircle`, `BarChart3`, `LinkIcon`, `Settings`, `Bot`, `MessageCircle`, `Globe`, `Menu`, `Search`, `ChevronLeft` from "lucide-react"

**Structure**:
- Collapsible sidebar (64px collapsed, 256px expanded)
- Header with logo and collapse toggle
- Search bar with keyboard shortcut hint (⌘K)
- Navigation menu with 11 main routes
- Active state highlighting
- Responsive design

**Navigation Routes**:
1. Playground → `/playground`
2. Activity → `/activity`
3. Chat → `/activity/chat`
4. Data → `/sources/data`
5. FAQ → `/sources/faq`
6. Analytics → `/analytics`
7. Connect → `/connect`
8. AI → `/settings/ai`
9. Chat Interface → `/settings/chat-interface`
10. Custom Domains → `/settings/custom-domains`
11. Settings → `/settings`

### components/header.tsx
**Purpose**: Top header with notifications and user profile
**Components Used**:
- `Button` from "@/components/ui/button"
- `Bell`, `User` from "lucide-react"

**Structure**:
- Sticky header with backdrop blur
- Dashboard title
- Notification and user profile buttons
- Responsive padding and spacing

## Layout Pattern
All pages follow this structure:
\`\`\`tsx
<div className="flex h-screen bg-background">
  <Sidebar />
  <div className="flex-1 flex flex-col">
    <Header />
    <div className="flex-1 p-6 space-y-6">
      {/* Page content */}
    </div>
  </div>
</div>
