# Component Dependencies & Architecture

## Core Dependencies

### UI Component Library (shadcn/ui)
All pages use these foundational components:
- **Form Controls**: `Button`, `Input`, `Textarea`, `Select`, `Switch`, `Slider`, `Checkbox`
- **Layout**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger`
- **Feedback**: `Badge`, `Alert`, `Progress`, `Toast`
- **Overlays**: `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `Sheet`
- **Navigation**: `Breadcrumb`, `Pagination`
- **Data Display**: `Table`, `TableBody`, `TableCell`, `TableHead`, `TableHeader`, `TableRow`

### Icon System (Lucide React)
Consistent icon usage across all pages:
- **Navigation**: `PlayCircle`, `Activity`, `MessageSquare`, `Database`, `HelpCircle`, `BarChart3`, `LinkIcon`, `Settings`
- **Actions**: `Plus`, `Edit3`, `Trash2`, `Save`, `Search`, `Filter`, `Download`, `Upload`, `Copy`, `Eye`
- **Status**: `CheckCircle`, `XCircle`, `AlertTriangle`, `Clock`, `RefreshCw`
- **Social**: `Instagram`, `Twitter`, `MessageCircle`, `Globe`
- **UI**: `Menu`, `ChevronLeft`, `ChevronRight`, `MoreHorizontal`, `X`

### Chart Library (Recharts)
Used specifically in Analytics page:
- `LineChart`, `Line` - Trend visualization
- `BarChart`, `Bar` - Comparative data
- `PieChart`, `Pie`, `Cell` - Distribution data
- `XAxis`, `YAxis`, `CartesianGrid` - Chart structure
- `Tooltip`, `Legend` - Interactive elements
- `ResponsiveContainer` - Responsive behavior

## Custom Components

### Layout Components
1. **Sidebar** (`components/sidebar.tsx`)
   - Used by: ALL pages
   - Dependencies: Navigation array, pathname detection, collapse state
   - Features: Collapsible, search, active state highlighting

2. **Header** (`components/header.tsx`)
   - Used by: ALL pages
   - Dependencies: Notification and user profile buttons
   - Features: Sticky positioning, backdrop blur

### Page-Specific Components
Each page implements its own specialized components inline:
- **Playground**: Model configuration panel, chat interface
- **Compare**: Dual model comparison panels
- **Chat**: Conversation cards, message editing dialogs
- **Analytics**: KPI cards, chart containers
- **FAQ**: Question/answer management, multi-question support
- **Connect**: Integration cards, widget preview
- **Settings**: Configuration forms, live previews

## State Management Architecture

### Local State Patterns
All pages use `useState` for:
- Form data management
- UI state (modals, filters, selections)
- Loading states
- Error handling

### Common State Structures
\`\`\`typescript
// Search and filtering
const [searchQuery, setSearchQuery] = useState("")
const [statusFilter, setStatusFilter] = useState("all")

// Modal management
const [isEditing, setIsEditing] = useState(false)
const [selectedItem, setSelectedItem] = useState(null)

// Form handling
const [formData, setFormData] = useState({})
const [hasChanges, setHasChanges] = useState(false)
\`\`\`

## Data Flow Patterns

### Mock Data Structure
All pages use consistent mock data patterns:
- Unique IDs for all entities
- Timestamp fields (ISO format)
- Status enums with consistent values
- Nested objects for complex data
- Array structures for lists

### API Integration Points
Ready for backend integration:
- CRUD operations for all entities
- Search and filtering endpoints
- File upload handling
- Real-time updates via WebSocket
- Authentication and authorization

## Styling Architecture

### Theme System
- CSS custom properties for colors
- Dark theme by default
- Consistent spacing scale
- Typography hierarchy
- Component variants

### Responsive Design
- Mobile-first approach
- Breakpoint consistency
- Flexible grid systems
- Collapsible navigation
- Adaptive layouts

## Performance Considerations

### Optimization Patterns
- Component lazy loading where applicable
- Efficient re-rendering with proper key props
- Debounced search inputs
- Virtualization for large lists (ready to implement)
- Image optimization for uploads

### Bundle Size Management
- Tree-shaking friendly imports
- Selective icon imports
- Code splitting at route level
- Minimal external dependencies

## Accessibility Features

### ARIA Implementation
- Proper semantic HTML
- Screen reader support
- Keyboard navigation
- Focus management
- Color contrast compliance

### Interactive Elements
- Button states and feedback
- Form validation messages
- Loading indicators
- Error handling
- Success confirmations

## Testing Architecture

### Component Testing
- Unit tests for utility functions
- Component rendering tests
- User interaction testing
- Form validation testing
- API integration testing

### E2E Testing
- User workflow testing
- Cross-browser compatibility
- Mobile responsiveness
- Performance testing
- Accessibility testing

This architecture provides a solid foundation for scaling the application while maintaining consistency and performance.
