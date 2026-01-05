# Supabase Configuration

**Supabase provides PostgreSQL database and JWT authentication for SocialSync AI.**

This guide walks you through creating a Supabase project and connecting it to your application.

---

## Table of Contents

- [What is Supabase?](#what-is-supabase)
- [Create a Supabase project](#create-a-supabase-project)
- [Get your credentials](#get-your-credentials)
- [Run database migrations](#run-database-migrations)
- [Configure authentication](#configure-authentication)
- [Update environment variables](#update-environment-variables)
- [Test the connection](#test-the-connection)
- [Troubleshooting](#troubleshooting)

---

## What is Supabase?

**Supabase is an open-source Firebase alternative** that provides:
- **PostgreSQL database** - Stores users, messages, conversations, and knowledge base documents
- **Authentication** - JWT-based user authentication with social login support
- **Row Level Security (RLS)** - Database-level access control
- **Real-time subscriptions** - Live updates when data changes
- **Storage** - File storage for document uploads

**SocialSync AI uses Supabase for:**
- User accounts and authentication
- Storing social media messages and conversations
- Knowledge base document storage
- AI settings and configurations
- Analytics data

---

## Create a Supabase project

**Step 1: Sign up for Supabase**

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign in with GitHub, Google, or email

**Step 2: Create a new project**

1. Click "New Project"
2. **Organization:** Select or create an organization
3. **Project name:** Choose any name (e.g., "socialsync-production")
4. **Database password:** Generate a strong password and **save it securely**
5. **Region:** Choose closest to your users (e.g., "West EU (Ireland)" for Europe)
6. **Pricing plan:** Free tier is sufficient for development

![Create Project Screenshot - showing form fields]

**Step 3: Wait for project creation**

Project setup takes **2-3 minutes**. You'll see a progress indicator.

---

## Get your credentials

**Once your project is ready, collect these four credentials:**

### 1. Project URL

**Location:** Project Settings → API → Project URL

**Example:** `https://abcdefgh.supabase.co`

**Copy this value to:**
- Backend: `SUPABASE_URL`
- Frontend: `NEXT_PUBLIC_SUPABASE_URL`

### 2. Anon Key (Public)

**Location:** Project Settings → API → Project API keys → `anon` `public`

**Starts with:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**What it does:** Public key for client-side requests. Safe to expose in frontend code.

**Copy this value to:**
- Backend: `SUPABASE_ANON_KEY`
- Frontend: `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 3. Service Role Key (Secret)

**Location:** Project Settings → API → Project API keys → `service_role` `secret`

**Click "Reveal"** to show the key.

**Starts with:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**What it does:** Server-side key with admin privileges. **Keep this secret.** Never expose in frontend code.

**Copy this value to:**
- Backend: `SUPABASE_SERVICE_ROLE_KEY`

### 4. JWT Secret

**Location:** Project Settings → API → JWT Settings → JWT Secret

**Click "Reveal"** to show the secret.

**What it does:** Used to verify JWT tokens. **Keep this secret.**

**Copy this value to:**
- Backend: `SUPABASE_JWT_SECRET`

---

## Run database migrations

**SocialSync AI needs specific database tables to function.**

### Option 1: Using Supabase SQL Editor (Recommended)

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy the SQL from one of these files:
   - `supabase/migrations/initial_schema.sql` (if it exists)
   - Or see [Database Schema](../architecture/database-schema.md) for complete SQL
4. Paste into the editor
5. Click "Run"

**Tables created:**
- `users` - User accounts
- `social_accounts` - Connected Instagram/WhatsApp accounts
- `conversations` - Message conversations
- `messages` - Individual messages
- `knowledge_documents` - Uploaded documents
- `faq_qa` - Frequently asked questions
- `user_credits` - AI usage credits
- And more...

### Option 2: Using CLI (Advanced)

**Install Supabase CLI:**

```bash
# macOS
brew install supabase/tap/supabase

# Windows (with Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Linux
curl -o- https://raw.githubusercontent.com/supabase/cli/main/install.sh | bash
```

**Run migrations:**

```bash
supabase link --project-ref your-project-id
supabase db push
```

---

## Configure authentication

**Enable authentication providers for user sign-up and login.**

### Enable Email authentication

1. Go to **Authentication** → **Providers**
2. **Email** should be enabled by default
3. **Enable email confirmations:** Toggle "Confirm email" (optional but recommended)

### Enable Google OAuth (Optional)

**Google OAuth allows users to sign in with their Google account.**

1. Go to **Authentication** → **Providers** → **Google**
2. Toggle "Enable Sign in with Google"
3. You'll need:
   - **Client ID** from Google Cloud Console
   - **Client Secret** from Google Cloud Console

**Get Google OAuth credentials:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: Add `https://your-project.supabase.co/auth/v1/callback`
7. Copy Client ID and Client Secret to Supabase

### Configure email templates (Optional)

**Customize confirmation and reset password emails:**

1. Go to **Authentication** → **Email Templates**
2. Edit templates:
   - Confirm signup
   - Invite user
   - Reset password

---

## Update environment variables

**Add Supabase credentials to your `.env` files.**

### Backend (.env)

Open `backend/.env` and add:

```bash
# Supabase Configuration
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_actual_key...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_actual_key...
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long
```

### Frontend (.env)

Open `frontend/.env` and add:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_actual_key...
```

**Important:** Use the same URL and anon key in both files.

---

## Test the connection

**Verify SocialSync AI can connect to Supabase.**

### Test from backend

**Start the backend:**

```bash
cd backend
docker-compose up backend
```

**Check logs for:**
```
✅ Successfully connected to Supabase
✅ Database tables found
```

**Test API health:**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Test from frontend

**Start the frontend:**

```bash
cd frontend
npm run dev
```

**Open browser:**
```
http://localhost:3000
```

**Try to sign up:**
1. Click "Sign Up"
2. Enter email and password
3. You should receive a confirmation email

**Check Supabase dashboard:**
1. Go to **Authentication** → **Users**
2. Your test user should appear in the list

---

## Troubleshooting

### Error: "Invalid API key"

**Cause:** Wrong `SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_ROLE_KEY`

**Solution:**
1. Go to Supabase → Project Settings → API
2. Copy keys again (click "Reveal" first)
3. Ensure no extra spaces or line breaks
4. Restart backend: `docker-compose restart backend`

### Error: "JWT verification failed"

**Cause:** Wrong `SUPABASE_JWT_SECRET`

**Solution:**
1. Go to Supabase → Project Settings → API → JWT Settings
2. Click "Reveal" and copy the JWT Secret
3. Update `SUPABASE_JWT_SECRET` in `backend/.env`
4. Restart backend

### Error: "relation 'users' does not exist"

**Cause:** Database migrations not run

**Solution:**
1. Go to Supabase SQL Editor
2. Run the migration SQL from `supabase/migrations/`
3. Verify tables exist: Go to **Database** → **Tables**

### Error: "Connection refused"

**Cause:** Wrong `SUPABASE_URL` or network issue

**Solution:**
1. Verify `SUPABASE_URL` format: `https://your-project.supabase.co`
2. Check project is not paused (Supabase pauses inactive free tier projects)
3. Unpause: Supabase dashboard → "Resume project"

### Project paused after inactivity

**Supabase free tier pauses projects after 7 days of inactivity.**

**Solution:**
1. Go to Supabase dashboard
2. Click "Resume project"
3. Wait 1-2 minutes for restart

**Prevent pausing:** Upgrade to Pro plan ($25/month) for always-on projects.

---

**Next:** [Configure Meta Platforms](meta-platforms.md) to connect Instagram, WhatsApp, and Messenger.
