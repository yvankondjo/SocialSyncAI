# SocialSync Frontend

Modern interface for social media management with Supabase authentication and backend API connection.

## 🚀 Features

- **Supabase Authentication**: Google OAuth login
- **Social Account Management**: Connect to real platforms
- **Unified Inbox**: WhatsApp and Instagram conversations
- **Dashboard**: Metrics and overview
- **Modern Interface**: Design with Tailwind CSS and shadcn/ui

## 📋 Prerequisites

- Node.js 18+
- SocialSync backend running
- Supabase project configured

## 🛠️ Installation

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Environment configuration**

Copy the example file and configure your variables:
```bash
cp env.example .env.local
```

Fill in the variables in `.env.local`:
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend URL
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

3. **Start development server**
```bash
npm run dev
```

## 🔧 Supabase Configuration

See [/docs/INSTALLATION.md](/docs/INSTALLATION.md) for complete database setup.

## 📱 Pages and Features

### Authentication
- **`/auth`**: Login page with Supabase Auth UI
- **`/auth/callback`**: OAuth callback handling

### Dashboard
- **`/dashboard`**: Overview with metrics
- **`/dashboard/accounts`**: Social account management
- **`/dashboard/inbox`**: Unified inbox for conversations

## 🔗 Backend Connection

The frontend automatically connects to the backend via API services:

### Available Services

#### SocialAccountsService
- `getSocialAccounts()`: List connected accounts
- `getConnectUrl(platform)`: OAuth authorization URL
- `deleteSocialAccount(accountId)`: Delete an account

#### ConversationsService
- `getConversations(channel?, limit?)`: List conversations
- `getMessages(conversationId, limit?)`: Messages from a conversation
- `sendMessage(conversationId, content)`: Send a message
- `markAsRead(conversationId)`: Mark as read

### Error Handling

All errors are automatically handled with:
- User error display
- Automatic retry for temporary failures
- Error logging for debugging

## 🎨 Customization

### Theme
The frontend uses Tailwind CSS with a modern theme:
- Indigo/purple colors for branding
- Glassmorphism design for cards
- Smooth animations with Framer Motion

### UI Components
Using shadcn/ui for consistent components:
- Cards, Buttons, Inputs
- Dialogs, Dropdowns, Tooltips
- Avatars, Badges, Toasts

## 🚀 Deployment

### Vercel
1. Connect your GitHub repository to Vercel
2. Configure environment variables
3. Deploy automatically

### Production environment variables
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-prod-anon-key
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_FRONTEND_URL=https://your-frontend-domain.com
```

## 🔍 Debugging

### Development tools
- **React DevTools**: Component inspection
- **Redux DevTools**: Application state
- **Network Tab**: API requests
- **Console**: Error logs

### Important logs
- Supabase authentication errors
- API connection failures
- OAuth errors
- Permission issues

## 📞 Support

For issues or questions:
1. Check console logs
2. Validate Supabase configuration
3. Verify backend is accessible
4. Consult backend API documentation

## 🎯 Roadmap

- [ ] Advanced analytics and metrics
- [ ] Post scheduling
- [ ] AI automations
- [ ] Message templates
- [ ] CRM integrations
- [ ] Push notifications
- [ ] Offline mode
