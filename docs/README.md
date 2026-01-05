# SocialSync AI Documentation

Welcome to the complete documentation for SocialSync AI.

This documentation helps you install, configure, and deploy a self-hosted social media automation platform powered by AI agents.

---

## Table of Contents

### 🚀 Getting Started

Start here if you're new to SocialSync AI.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [Quick Start](getting-started/quick-start.md) | Get running in 15 minutes with Docker | 🟢 Beginner |
| [Prerequisites](getting-started/prerequisites.md) | Required accounts and tools | 🟢 Beginner |
| [Environment Variables](getting-started/environment-variables.md) | Complete configuration reference | 🟡 Intermediate |

### ⚙️ Configuration

Connect external services to enable features.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [Supabase Setup](configuration/supabase.md) | Database and authentication | 🟢 Beginner |
| [Meta Platforms](configuration/meta-platforms.md) | Instagram, WhatsApp, Messenger OAuth | 🟡 Intermediate |
| [Webhooks](configuration/webhooks.md) | Real-time event delivery | 🟡 Intermediate |
| [AI Providers](configuration/ai-providers.md) | OpenAI, Anthropic, Google, OpenRouter | 🟢 Beginner |
| [Stripe](configuration/stripe.md) | Payment processing (optional) | 🟡 Intermediate |

### 🏗️ Architecture

Understand how SocialSync AI works under the hood.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [System Overview](architecture/overview.md) | High-level architecture and data flow | 🟡 Intermediate |
| [Database Schema](architecture/database-schema.md) | PostgreSQL tables and relationships | 🟡 Intermediate |
| [API Reference](architecture/api-reference.md) | REST endpoints documentation | 🔴 Advanced |

### 🎯 Features

Deep dives into specific features.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [Unified Inbox](features/inbox.md) | Cross-platform message management | 🟢 Beginner |
| [AI Automation](features/ai-automation.md) | RAG-based response system | 🟡 Intermediate |
| [Knowledge Base](features/knowledge-base.md) | Document ingestion and vector search | 🟡 Intermediate |
| [Analytics](features/analytics.md) | Performance tracking and insights | 🟢 Beginner |

### 🚢 Deployment

Deploy to production environments.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [Docker Deployment](deployment/docker.md) | Docker Compose for production | 🟡 Intermediate |
| [Google Cloud Run](deployment/gcp.md) | Deploy to Cloud Run + Compute Engine | 🔴 Advanced |
| [Railway](deployment/railway.md) | One-click Railway deployment | 🟢 Beginner |

### 🛠️ Development

Contribute to the project.

| Guide | Description | Difficulty |
|-------|-------------|------------|
| [Local Setup](development/local-setup.md) | Development environment configuration | 🟡 Intermediate |
| [Contributing](development/contributing.md) | Contribution guidelines | 🟢 Beginner |
| [Testing](development/testing.md) | Running tests | 🟡 Intermediate |

---

## Quick Navigation

**Most common tasks:**
- [Install from scratch](getting-started/quick-start.md) → Complete setup guide
- [Get Supabase credentials](configuration/supabase.md#get-credentials) → Database connection
- [Configure Instagram](configuration/meta-platforms.md#instagram) → OAuth setup
- [Test webhooks locally](configuration/webhooks.md#test-locally-with-ngrok) → ngrok tunnel
- [Add knowledge base documents](features/knowledge-base.md#upload-documents) → AI training

**Troubleshooting:**
- Webhook errors → [Webhooks troubleshooting](configuration/webhooks.md#troubleshooting)
- OAuth callback failures → [Meta platforms troubleshooting](configuration/meta-platforms.md#troubleshooting)
- Database connection issues → [Supabase troubleshooting](configuration/supabase.md#troubleshooting)

---

## Getting Help

**Can't find what you're looking for?**

1. **Search this documentation** using your browser's find feature (Ctrl+F / Cmd+F)
2. **Check GitHub Issues** for similar problems and solutions
3. **Open a new issue** with details about your problem

**Contributing to docs:**

Found an error or want to improve documentation? Edit files directly in the `docs/` directory and submit a pull request.

---

**Ready to start?** → [Quick Start Guide](getting-started/quick-start.md)
