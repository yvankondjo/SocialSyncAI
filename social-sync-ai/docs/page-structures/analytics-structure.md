# Analytics Dashboard Structure Documentation

## app/analytics/page.tsx
**Purpose**: Comprehensive analytics dashboard with KPIs, charts, and metrics
**Components Used**:
- `useState` from "react"
- `Sidebar`, `Header` from custom components
- **UI Components**: `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Select`, `SelectContent`, `SelectItem`, `SelectTrigger`, `SelectValue`, `Badge`, `Progress`
- **Chart Components**: `LineChart`, `Line`, `BarChart`, `Bar`, `PieChart`, `Pie`, `Cell`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `Legend`, `ResponsiveContainer` from "recharts"
- **Icons**: `BarChart3`, `TrendingUp`, `TrendingDown`, `Users`, `MessageSquare`, `Clock`, `ThumbsUp`, `AlertTriangle`, `Download`, `RefreshCw`, `Calendar` from "lucide-react"

**Structure**:
- **Header Section**: Title, description, date range selector, export/refresh buttons
- **KPI Cards Row**: 4 main metrics
  - Total Conversations (with trend)
  - Response Time (with trend)
  - Resolution Rate (with trend)
  - User Satisfaction (with trend)
- **Charts Section**: 2x2 grid
  - **Conversations Over Time**: Line chart with daily/weekly/monthly data
  - **Response Times**: Bar chart showing average response times
  - **Sentiment Distribution**: Pie chart (Positive, Neutral, Negative)
  - **Top Topics**: Horizontal bar chart of most discussed topics
- **Tables Section**: 2-column layout
  - **Top Questions**: List with question text and frequency
  - **Recent Activity**: Timeline of recent conversations

**State Management**:
- `dateRange`: Selected time period ("7d", "30d", "90d")
- `isLoading`: Loading state for data refresh

**Data Structures**:
\`\`\`typescript
// KPI Metrics
{
  totalConversations: { value: number, trend: number, isPositive: boolean }
  avgResponseTime: { value: string, trend: number, isPositive: boolean }
  resolutionRate: { value: string, trend: number, isPositive: boolean }
  satisfaction: { value: string, trend: number, isPositive: boolean }
}

// Chart Data
conversationData: Array<{ date: string, conversations: number }>
responseTimeData: Array<{ hour: string, avgTime: number }>
sentimentData: Array<{ name: string, value: number, color: string }>
topicsData: Array<{ topic: string, count: number }>
\`\`\`

**Key Features**:
- Real-time KPI monitoring
- Interactive charts with Recharts
- Trend indicators (up/down arrows with percentages)
- Date range filtering
- Export functionality
- Responsive chart containers
- Color-coded sentiment analysis
- Top questions tracking
- Recent activity timeline

**Chart Types Used**:
- **Line Chart**: Conversation trends over time
- **Bar Chart**: Response time analysis
- **Pie Chart**: Sentiment distribution
- **Horizontal Bar Chart**: Topic frequency

**Performance Indicators**:
- Conversation volume trends
- Response time optimization
- Resolution rate tracking
- User satisfaction scores
- Topic analysis
- Activity monitoring

## Visual Design
- Consistent card-based layout
- Color-coded trends (green for positive, red for negative)
- Professional chart styling
- Responsive grid system
- Dark theme compatible charts
- Clear typography hierarchy
