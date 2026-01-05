# Prerequisites

**Required accounts and tools before installing SocialSync AI.**

This page lists everything you need to set up before running SocialSync AI.

---

## Table of Contents

- [Software requirements](#software-requirements)
- [External accounts](#external-accounts)
- [Development tools (optional)](#development-tools-optional)
- [Estimated costs](#estimated-costs)

---

## Software requirements

**Install these tools on your local machine.**

### Docker and Docker Compose

**Docker containerizes the application** for consistent deployment across environments.

| Platform | Installation |
|----------|--------------|
| **macOS** | [Download Docker Desktop](https://www.docker.com/products/docker-desktop) |
| **Windows** | [Download Docker Desktop](https://www.docker.com/products/docker-desktop) (requires WSL 2) |
| **Linux** | [Install Docker Engine](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/) |

**Verify installation:**
```bash
docker --version  # Should show 20.10+
docker-compose --version  # Should show 2.0+
```

**Minimum system requirements:**
- 4GB RAM available for Docker
- 20GB free disk space
- 64-bit processor

### Git

**Git downloads the source code** from GitHub.

[Download Git](https://git-scm.com/downloads) for your platform.

**Verify installation:**
```bash
git --version
```

### Optional: Node.js and Python

**You don't need these if using Docker.** Docker containers include Node.js and Python.

**If you want to run without Docker:**

| Tool | Version | Download |
|------|---------|----------|
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |

---

## External accounts

**Create these free accounts to enable features.**

### Required accounts

#### 1. Supabase (Database + Auth)

**Supabase provides PostgreSQL database and authentication.**

- **Create account:** [supabase.com](https://supabase.com)
- **Pricing:** Free tier includes 500MB database, 50MB file storage, 50,000 monthly active users
- **What you'll need:** Project URL, anon key, service role key, JWT secret
- **Setup guide:** [Supabase Configuration](../configuration/supabase.md)

#### 2. Meta Developer Account (Instagram, WhatsApp, Messenger)

**Meta Developer account enables social media integrations.**

- **Create account:** [developers.facebook.com](https://developers.facebook.com)
- **Requirements:** Valid Facebook account
- **What you'll need:** App ID, App Secret, Config ID (for WhatsApp)
- **Setup guide:** [Meta Platforms Configuration](../configuration/meta-platforms.md)

### Optional accounts

#### 3. AI Provider (Choose one)

**AI provider powers automated responses.**

| Provider | Free Tier | Pricing | Recommended For |
|----------|-----------|---------|-----------------|
| **OpenRouter** | $0 (pay-as-you-go) | $0.10-$20 per million tokens | Access to multiple models |
| **OpenAI** | $5 free credit | $0.50-$60 per million tokens | GPT-4, GPT-3.5 |
| **Anthropic** | No free tier | $3-$15 per million tokens | Claude models |
| **Google** | Free tier available | $0.125-$7 per million tokens | Gemini models |

**Setup guide:** [AI Providers Configuration](../configuration/ai-providers.md)

#### 4. Stripe (Payments)

**Stripe enables user billing and subscriptions.**

- **Create account:** [stripe.com](https://stripe.com)
- **Pricing:** 2.9% + 30¢ per transaction
- **When needed:** Only if charging users for your service
- **Setup guide:** [Stripe Configuration](../configuration/stripe.md)

---

## Development tools (optional)

**These tools improve development experience but aren't required.**

### Code editor

**Recommended:** [Visual Studio Code](https://code.visualstudio.com/)

**Useful VS Code extensions:**
- Python (Microsoft)
- ESLint
- Prettier
- Docker
- Tailwind CSS IntelliSense

### API testing

**Test API endpoints during development:**

- **Postman** - [postman.com](https://www.postman.com/)
- **Insomnia** - [insomnia.rest](https://insomnia.rest/)
- **cURL** - Command-line tool (included with macOS/Linux, available for Windows)

### ngrok (Local webhook testing)

**ngrok creates public URLs for local development.**

- **Website:** [ngrok.com](https://ngrok.com)
- **Free tier:** 1 process, 40 connections/min
- **When needed:** Testing webhooks locally
- **Usage:** `ngrok http 8000`

See [Webhooks Configuration](../configuration/webhooks.md#test-locally-with-ngrok) for setup.

---

## Estimated costs

**Monthly cost breakdown for running SocialSync AI:**

| Service | Free Tier | Paid Tier | Needed For |
|---------|-----------|-----------|------------|
| **Supabase** | 500MB DB | $25/month (8GB) | Database, auth |
| **AI Provider** | Varies | $10-100/month | AI responses |
| **Meta APIs** | Free | Free | Instagram, WhatsApp, Messenger |
| **Stripe** | Free | 2.9% + 30¢ per txn | User billing (optional) |
| **Hosting** | $0 (local) | $20-50/month | Production deployment |

**Total for small deployment:** $0-35/month (free tiers sufficient for testing and low-volume usage)

**Total for production:** $50-200/month depending on:
- Number of AI-generated messages
- Database size
- Number of users

---

## Ready to install?

**You have everything you need if you've:**
- ✅ Installed Docker and Docker Compose
- ✅ Installed Git
- ✅ Created Supabase account
- ✅ Created Meta Developer account
- ✅ Chosen an AI provider

**Next step:** [Quick Start Guide](quick-start.md) to install and run SocialSync AI.
