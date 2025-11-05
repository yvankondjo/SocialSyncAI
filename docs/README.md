# 🤖 SocialSync AI - Open Source Edition

> AI-Powered Social Media Management & Automation Platform

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green)](https://supabase.com/)

**SocialSync AI** is a production-ready, open-source platform that automates social media management using advanced AI. Connect your Instagram and WhatsApp accounts, automate DM responses with RAG-powered conversations, moderate comments intelligently, schedule posts, and analyze performance—all powered by state-of-the-art Large Language Models.

---

## ✨ Key Features

### 🤖 **AI-Powered Automation**
- **RAG-Based Conversations** - Vector search + LLM for context-aware responses
- **Multi-Model Support** - GPT-4o, Claude, Gemini, Llama via OpenRouter
- **Smart Escalation** - Automatic handoff to humans when needed
- **Safety Guardrails** - OpenAI Moderation + custom filtering rules
- **Conversation Memory** - LangGraph checkpoints for context retention

### 💬 **Unified Inbox**
- **Instagram DMs + WhatsApp** - Single interface for all conversations
- **Real-time Polling** - Celery workers check for new messages every 0.5s
- **Per-Conversation AI Toggle** - Enable/disable automation per chat
- **Manual Override** - Respond manually when needed
- **Escalation System** - Email notifications for complex requests

### 📅 **Scheduled Publishing**
- **Visual Calendar** - Drag-and-drop interface for post scheduling
- **Multi-Platform** - Instagram (posts/reels) + WhatsApp broadcasts
- **Recurring Posts** - RRULE support for repeated schedules
- **Media Upload** - Images, videos with preview
- **Retry Logic** - 3 attempts with exponential backoff

### 💭 **Comment Moderation**
- **Auto-Reply** - AI generates contextual comment responses
- **Adaptive Polling** - Smart intervals (5-30 min) based on post age
- **Multimodal Context** - Includes post image + caption for LLM
- **Triage System** - RESPOND / IGNORE / ESCALATE classification
- **Owner Detection** - Prevents infinite loops on self-comments

### 🎨 **AI Studio**
- **Content Creation Assistant** - Interactive chat for generating posts
- **Multi-Turn Conversations** - LangGraph maintains context
- **Temperature Control** - Creativity slider (0.0-1.0)
- **Direct Scheduling** - Create and schedule in one flow
- **Preview System** - See generated content before publishing

### 📊 **Analytics & Insights**
- **Performance Dashboards** - Conversations, messages, AI decisions
- **Topic Modeling** - BERTopic analysis of message trends
- **AI Performance** - Decision accuracy, confidence tracking
- **Timeline Views** - Daily breakdowns of activity

### 📚 **Knowledge Base**
- **Document Upload** - PDF, TXT, MD, DOCX support
- **Vector Embeddings** - Google Gemini text-embedding-004
- **Hybrid Search** - BM25 + vector similarity
- **FAQ Management** - Structured Q&A pairs
- **Multilingual** - French, English, Spanish

---

## 🏗️ Tech Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) 0.100+ (Python 3.10+)
- **AI/ML:** [LangChain](https://www.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/) + pg_vector
- **LLM Gateway:** [OpenRouter](https://openrouter.ai/) (GPT-4o, Claude, Gemini, Llama, etc.)
- **Moderation:** [OpenAI Moderation API](https://platform.openai.com/docs/guides/moderation)
- **Topic Modeling:** [BERTopic](https://maartengr.github.io/BERTopic/)
- **Workers:** [Celery](https://docs.celeryq.dev/) + Redis

### Frontend
- **Framework:** [Next.js 14](https://nextjs.org/) (App Router)
- **Language:** TypeScript 5.0+
- **UI:** [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)
- **State:** [Zustand](https://github.com/pmndrs/zustand)

### Database & Infrastructure
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL 15+)
- **Auth:** Supabase Auth (JWT)
- **Storage:** Supabase Storage (S3-compatible)
- **Cache:** Redis 7.0+
- **Email:** [Resend](https://resend.com/)
- **Containers:** Docker + Docker Compose

---

## ⚡ Quick Start

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Supabase account** ([free tier](https://supabase.com/))
- **OpenRouter API key** ([get one here](https://openrouter.ai/keys)) OR **OpenAI API key**
- **Meta Developer account** (for Instagram/WhatsApp)

### Installation (5 steps)

```bash
# 1. Clone repository
git clone https://github.com/yvankondjo/socialsync-ai.git
cd socialsync-ai

# 2. Copy environment template
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys (see INSTALLATION.md)

# 3. Start services
docker-compose up -d

# 4. Run database migrations
docker-compose exec backend python -m app.db.migrate

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Full setup guide:** See [INSTALLATION.md](./INSTALLATION.md) for detailed instructions with Meta Developer setup, Supabase configuration, and troubleshooting.

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [INSTALLATION.md](./INSTALLATION.md) | Complete setup guide (30-45 min) |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design + diagrams |
| [DATABASE.md](./DATABASE.md) | Schema reference (33 tables) |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Developer guide + roadmap |

### Feature Guides
| Feature | Documentation |
|---------|---------------|
| DM Automation | [features/DM_AUTOMATION.md](./features/DM_AUTOMATION.md) |
| Comment Moderation | [features/COMMENT_MODERATION.md](./features/COMMENT_MODERATION.md) |
| Scheduled Posts | [features/SCHEDULED_POSTS.md](./features/SCHEDULED_POSTS.md) |
| Knowledge Base | [features/KNOWLEDGE_BASE.md](./features/KNOWLEDGE_BASE.md) |

### Technical Deep Dives
| Topic | Documentation |
|-------|---------------|
| RAG System | [technical/RAG_SYSTEM.md](./technical/RAG_SYSTEM.md) |
| Celery Workers | [technical/CELERY_WORKERS.md](./technical/CELERY_WORKERS.md) |

---

## 🎯 Use Cases

### For Businesses
- **Customer Support Automation** - Handle repetitive DMs 24/7
- **Community Engagement** - Auto-reply to comments at scale
- **Content Scheduling** - Plan social media calendar weeks ahead
- **Lead Qualification** - RAG agent asks qualifying questions

### For Creators
- **Audience Interaction** - Never miss a comment or DM
- **Content Ideas** - AI Studio generates posts based on your knowledge base
- **Growth Analytics** - Track engagement patterns and topics

### For Agencies
- **Multi-Account Management** - Each user manages multiple social accounts
- **White-Label Ready** - Deploy for your clients
- **Performance Reporting** - Built-in analytics dashboards

---

## 🚀 Features Demo

### Unified Inbox
```
📥 Inbox (Instagram + WhatsApp)
├── Customer A (Instagram) - AI: ON ✅
│   └── "What are your business hours?"
│       └── 🤖 AI: "We're open Mon-Fri 9am-6pm EST..."
├── Customer B (WhatsApp) - AI: OFF ❌
│   └── "I need a refund"
│       └── 🚨 Escalated to human
└── Customer C (Instagram) - AI: ON ✅
    └── "Do you ship internationally?"
        └── 🤖 AI: "Yes, we ship worldwide..."
```

### Comment Moderation
```
📸 Post: New Product Launch
├── @user1: "Looks amazing!"
│   └── ✅ Auto-reply: "Thank you! 🎉"
├── @user2: "What's the price?"
│   └── ✅ Auto-reply: "It's $99. Link in bio!"
├── @user3: "You suck"
│   └── 🚫 Flagged by OpenAI Moderation
└── @youraccount: "Thanks everyone!"
    └── ⏭️ Skipped (owner comment)
```

### Scheduled Posts
```
📅 Calendar View
Mon Jan 15  ✅ Published: Product teaser
Tue Jan 16  🕒 Queued: Behind-the-scenes
Wed Jan 17  📝 Draft: Launch announcement
Thu Jan 18  🔁 Recurring: Weekly tip #4
```

---

## 🛠️ Configuration

### Environment Variables
Key variables (see `backend/.env.example` for complete list):

```bash
# Supabase (5 vars)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=xxx
SUPABASE_DB_URL=postgresql://...

# AI/LLM (2 vars)
OPENROUTER_API_KEY=sk-or-...
# OR
OPENAI_API_KEY=sk-...

# Meta Platform (4 vars)
INSTAGRAM_CLIENT_ID=xxx
INSTAGRAM_CLIENT_SECRET=xxx
INSTAGRAM_WEBHOOK_SECRET=xxx
WHATSAPP_VERIFY_TOKEN=xxx

# Redis
REDIS_URL=redis://redis:6379/0

# Email
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@yourdomain.com
```

### AI Settings
Configure via API or database:

```python
{
  "ai_control_enabled": true,           # Master switch
  "ai_enabled_for_chats": true,         # DM automation
  "ai_enabled_for_comments": true,      # Comment auto-reply
  "default_model": "gpt-4o",            # LLM model
  "temperature": 0.7,                   # Creativity (0.0-1.0)
  "flagged_keywords": [                 # Block list
    "spam", "viagra", "casino"
  ],
  "flagged_phrases": [                  # Phrase block list
    "worst product ever"
  ]
}
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Run specific test
pytest tests/test_services/test_rag_escalation_tool.py -v

# With coverage
pytest --cov=app tests/
```

**Test Coverage:**
- ✅ Comment automation (10/10 tests)
- ✅ Escalation system (3/3 tests)
- ⚠️ Frontend tests (TBD)

---

## 📊 Project Status

**Current Version:** 1.0.0 (Open Source Release)

**Tested Features:**
- ✅ Instagram DM automation
- ✅ WhatsApp message automation
- ✅ Comment moderation + auto-reply
- ✅ Scheduled post publishing
- ✅ RAG-based conversations
- ✅ Knowledge base (vector search)
- ✅ AI Studio (content creation)
- ✅ Analytics dashboards
- ✅ Escalation system
- ✅ Multi-model LLM support

**Production Ready:** Yes (all features tested with real Supabase data)

---

## 🗺️ Roadmap

### Q1 2025
- [ ] Twitter/X integration
- [ ] LinkedIn integration
- [ ] Enhanced analytics (predictive insights)
- [ ] Team collaboration (multi-user workspaces)

### Q2 2025
- [ ] TikTok integration
- [ ] Mobile app (React Native)
- [ ] API webhooks (custom integrations)
- [ ] Advanced scheduling (A/B testing)

### Q3 2025
- [ ] White-label deployment
- [ ] Custom model fine-tuning
- [ ] Voice message support
- [ ] Image generation (DALL-E, Midjourney)

**Vote on features:** [GitHub Discussions](https://github.com/yvankondjo/socialsync-ai/discussions)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Development setup
- Code style guide
- PR guidelines
- Issue templates

**Quick start:**
```bash
# Fork repository
git clone https://github.com/yvankondjo/socialsync-ai.git
cd socialsync-ai

# Create feature branch
git checkout -b feat/your-feature

# Make changes, test, commit
git commit -m "feat: add Twitter integration"

# Push and create PR
git push origin feat/your-feature
```

---

## 📄 License

This project is licensed under the **AGPL-3.0 License** - see the [LICENSE](../LICENSE) file for details.

**What this means:**
- ✅ Free to use, modify, and distribute
- ✅ Can use commercially
- ⚠️ **Must share source code** if you run it as a service (network use = distribution)
- ⚠️ Modifications must be released under AGPL-3.0

**Not suitable for:** Proprietary SaaS without sharing code. Consider a commercial license for closed-source deployments.

---

## 🙏 Acknowledgments

Built with amazing open-source tools:
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework
- [Next.js](https://nextjs.org/) - React framework for production
- [LangChain](https://www.langchain.com/) - LLM application framework
- [Supabase](https://supabase.com/) - Open-source Firebase alternative (PostgreSQL + pg_vector)
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [Celery](https://docs.celeryq.dev/) - Distributed task queue

---

## 🆘 Support

### Community Support
- **GitHub Issues** - [Report bugs](https://github.com/yvankondjo/socialsync-ai/issues)
- **Discussions** - [Ask questions](https://github.com/yvankondjo/socialsync-ai/discussions)
- **Discord** - [Join community](https://discord.gg/socialsync-ai) (Coming soon)

### Documentation
- **Quick Start** - [INSTALLATION.md](./INSTALLATION.md)
- **FAQ** - [See Discussions](https://github.com/yvankondjo/socialsync-ai/discussions/categories/q-a)
- **API Docs** - http://localhost:8000/docs (when running locally)

### Commercial Support
For enterprise deployments, custom features, or training:
- Email: support@yourdomain.com
- Commercial licenses available

---

## 📈 Analytics & Telemetry

**SocialSync AI collects NO usage data by default.** All analytics shown in the dashboard are YOUR data stored in YOUR Supabase instance.

**We do NOT:**
- ❌ Send data to external services
- ❌ Track user behavior
- ❌ Collect telemetry
- ❌ Phone home

**Your data stays with you.**

---

## 🔒 Security

**Reporting vulnerabilities:** security@yourdomain.com (private disclosure)

**Security features:**
- ✅ JWT authentication (Supabase Auth)
- ✅ Row Level Security (RLS) on all tables
- ✅ OpenAI Moderation API for content safety
- ✅ Webhook signature verification
- ✅ Environment variable secrets
- ✅ HTTPS enforced in production

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yvankondjo/socialsync-ai&type=Date)](https://star-history.com/#yvankondjo/socialsync-ai&Date)

---

<div align="center">

**Made with ❤️ by the open-source community**

[Documentation](./INSTALLATION.md) · [Report Bug](https://github.com/yvankondjo/socialsync-ai/issues) · [Request Feature](https://github.com/yvankondjo/socialsync-ai/discussions)

</div>
