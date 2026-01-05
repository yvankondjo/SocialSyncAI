# AI Providers Configuration

**Configure AI models to power automated responses in SocialSync AI.**

This guide shows you how to set up OpenAI, Anthropic, Google Gemini, or OpenRouter for AI-generated message responses.

---

## Table of Contents

- [Choose an AI provider](#choose-an-ai-provider)
- [OpenRouter (Recommended)](#openrouter-recommended)
- [OpenAI](#openai)
- [Anthropic](#anthropic)
- [Google Gemini](#google-gemini)
- [Test your configuration](#test-your-configuration)
- [Model selection](#model-selection)
- [Cost estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)

---

## Choose an AI provider

**You need at least one AI provider API key for automated responses to work.**

| Provider | Best For | Free Tier | Pricing | Models Available |
|----------|----------|-----------|---------|------------------|
| **OpenRouter** | Access to 100+ models | $0 (pay-as-you-go) | $0.10-$20 per 1M tokens | GPT-4, Claude, Gemini, Llama, Mistral, and more |
| **OpenAI** | GPT-4 and GPT-3.5 | $5 free credit | $0.50-$60 per 1M tokens | GPT-4o, GPT-4, GPT-3.5-turbo |
| **Anthropic** | Claude models | None | $3-$15 per 1M tokens | Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku |
| **Google** | Gemini models | 60 requests/min free | $0.125-$7 per 1M tokens | Gemini 1.5 Pro, Gemini 1.5 Flash |

**Recommendation:** Start with **OpenRouter** for flexibility and cost-effectiveness. You can access multiple models with one API key.

---

## OpenRouter (Recommended)

**OpenRouter provides unified access to 100+ AI models from different providers.**

### Why OpenRouter?

**Benefits:**
- **Single API key** for multiple model providers
- **Pay-as-you-go** - No subscriptions, pay only for usage
- **Model flexibility** - Switch between GPT-4, Claude, Gemini without changing code
- **Competitive pricing** - Often cheaper than direct provider APIs
- **Free models available** - Some models like Llama 3 are free

### Get API key

**Step 1: Create account**

1. Go to [openrouter.ai](https://openrouter.ai)
2. Click "Sign In" → Sign in with Google, GitHub, or email
3. Complete registration

**Step 2: Add credits**

1. Go to [openrouter.ai/credits](https://openrouter.ai/credits)
2. Click "Purchase Credits"
3. Add $5-$20 (sufficient for testing)
4. Payment via credit card or crypto

**Step 3: Get API key**

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Click "Create Key"
3. **Name:** "SocialSync AI Production"
4. **Rate limit:** Optional (leave blank for no limit)
5. Click "Create"
6. **Copy the key** (starts with `sk-or-v1-`)

**Step 4: Add to environment**

Add to `backend/.env`:

```bash
# AI Provider - OpenRouter
OPENROUTER_API_KEY=sk-or-v1-abc123...
```

Restart backend:
```bash
docker-compose restart backend
```

### Recommended models

**Best models on OpenRouter for customer support:**

| Model | Speed | Quality | Cost per 1M tokens |
|-------|-------|---------|-------------------|
| `anthropic/claude-3.5-sonnet` | Fast | Excellent | $3 input / $15 output |
| `openai/gpt-4o` | Fast | Excellent | $2.50 input / $10 output |
| `google/gemini-pro-1.5` | Very Fast | Good | $0.125 input / $0.50 output |
| `meta-llama/llama-3.1-70b-instruct` | Very Fast | Good | Free |

---

## OpenAI

**OpenAI provides GPT-4 and GPT-3.5 models directly.**

### Get API key

**Step 1: Create account**

1. Go to [platform.openai.com/signup](https://platform.openai.com/signup)
2. Sign up with email or Google
3. Verify phone number

**Step 2: Add payment method**

1. Go to [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Click "Add payment method"
3. Enter credit card details
4. Set spending limit (recommended: $20/month for testing)

**New accounts get $5 free credit** (expires after 3 months).

**Step 3: Create API key**

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. **Name:** "SocialSync AI"
4. **Permissions:** All (or "Read" and "Write")
5. Click "Create secret key"
6. **Copy the key** (starts with `sk-proj-`)

**Important:** Save the key immediately. You can't view it again after closing the dialog.

**Step 4: Add to environment**

Add to `backend/.env`:

```bash
# AI Provider - OpenAI
OPENAI_API_KEY=sk-proj-abc123...
```

Restart backend:
```bash
docker-compose restart backend
```

### Recommended models

| Model | Speed | Quality | Cost per 1M tokens |
|-------|-------|---------|-------------------|
| `gpt-4o` | Fast | Excellent | $2.50 input / $10 output |
| `gpt-4o-mini` | Very Fast | Good | $0.15 input / $0.60 output |
| `gpt-3.5-turbo` | Very Fast | Good | $0.50 input / $1.50 output |

---

## Anthropic

**Anthropic provides Claude models known for long context and safety.**

### Get API key

**Step 1: Create account**

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Click "Sign Up"
3. Enter email and create password
4. Verify email

**Step 2: Add credits**

**Note:** Anthropic requires adding credits before using the API.

1. Go to **Settings** → **Billing**
2. Click "Add Credits"
3. Minimum: $5
4. Enter credit card details
5. Complete purchase

**Step 3: Create API key**

1. Go to **Settings** → **API Keys**
2. Click "Create Key"
3. **Name:** "SocialSync AI"
4. Click "Create"
5. **Copy the key** (starts with `sk-ant-`)

**Step 4: Add to environment**

Add to `backend/.env`:

```bash
# AI Provider - Anthropic
ANTHROPIC_API_KEY=sk-ant-abc123...
```

Restart backend:
```bash
docker-compose restart backend
```

### Recommended models

| Model | Speed | Quality | Cost per 1M tokens |
|-------|-------|---------|-------------------|
| `claude-3-5-sonnet-20241022` | Fast | Excellent | $3 input / $15 output |
| `claude-3-opus-20240229` | Medium | Excellent | $15 input / $75 output |
| `claude-3-haiku-20240307` | Very Fast | Good | $0.25 input / $1.25 output |

---

## Google Gemini

**Google Gemini provides fast, cost-effective models with large context windows.**

### Get API key

**Step 1: Create Google Cloud project**

1. Go to [makersuite.google.com](https://makersuite.google.com)
2. Sign in with Google account
3. Accept terms and conditions

**Step 2: Create API key**

1. Click "Get API Key" in the sidebar
2. Click "Create API Key"
3. Select or create a Google Cloud project
4. **Copy the key** (starts with `AIzaSy`)

**Step 3: Add to environment**

Add to `backend/.env`:

```bash
# AI Provider - Google Gemini
GEMINI_API_KEY=AIzaSyAbc123...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

**Note:** `GEMINI_BASE_URL` is required for OpenAI-compatible API format.

Restart backend:
```bash
docker-compose restart backend
```

### Free tier limits

**Gemini offers generous free tier:**
- 60 requests per minute
- 1,500 requests per day
- 1 million tokens per day (input + output combined)

**Sufficient for testing and small deployments.**

### Recommended models

| Model | Speed | Quality | Cost per 1M tokens |
|-------|-------|---------|-------------------|
| `gemini-1.5-pro` | Fast | Excellent | $1.25 input / $5 output |
| `gemini-1.5-flash` | Very Fast | Good | $0.075 input / $0.30 output |
| `gemini-1.0-pro` | Fast | Good | Free (with limits) |

---

## Test your configuration

**Verify AI provider is working correctly.**

### Test via API

**Send test request to backend:**

```bash
curl -X POST http://localhost:8000/api/ai/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me?"}'
```

**Expected response:**

```json
{
  "response": "Hello! I'm an AI assistant...",
  "model": "gpt-4o",
  "tokens_used": 45,
  "cost": 0.00011
}
```

### Test via frontend

**Step 1: Log in to SocialSync AI**

Open http://localhost:3000 and sign in.

**Step 2: Configure AI Settings**

Navigate to **Settings → AI** in the sidebar.

**Step 3: Send test message**

Type a test message:
```
What are your business hours?
```

**You should see:**
- AI response generated within 2-3 seconds
- Token usage displayed
- Model name shown

### Check logs

**View backend logs for AI requests:**

```bash
docker-compose logs -f backend
```

Look for:
```
INFO: AI request to model=gpt-4o tokens=45 cost=$0.00011
INFO: AI response generated in 1.2 seconds
```

---

## Model selection

**SocialSync AI automatically selects the best model based on your configured providers.**

### Priority order

**If multiple providers are configured, SocialSync AI uses this priority:**

1. **OpenRouter** (if `OPENROUTER_API_KEY` is set)
2. **OpenAI** (if `OPENAI_API_KEY` is set)
3. **Anthropic** (if `ANTHROPIC_API_KEY` is set)
4. **Google Gemini** (if `GEMINI_API_KEY` is set)

### Override model selection

**Change default model in `backend/.env`:**

```bash
# Force specific model
DEFAULT_AI_MODEL=anthropic/claude-3.5-sonnet
# or
DEFAULT_AI_MODEL=gpt-4o
# or
DEFAULT_AI_MODEL=gemini-1.5-pro
```

### Per-user model selection

**Users can choose their preferred model in UI:**

1. Go to **Settings** → **AI Configuration**
2. Select model from dropdown
3. Models available based on your configured API keys

---

## Cost estimation

**Estimate monthly costs based on usage.**

### Assumptions

- **Average message length:** 100 tokens input + 200 tokens output = 300 tokens total
- **Messages per day:** Variable by business

### Cost examples

**Using GPT-4o ($2.50 input / $10 output per 1M tokens):**

| Messages/Day | Tokens/Day | Cost/Day | Cost/Month |
|--------------|------------|----------|------------|
| 10 | 3,000 | $0.03 | $0.90 |
| 100 | 30,000 | $0.30 | $9.00 |
| 1,000 | 300,000 | $3.00 | $90.00 |
| 10,000 | 3,000,000 | $30.00 | $900.00 |

**Using GPT-3.5-turbo ($0.50 input / $1.50 output per 1M tokens):**

| Messages/Day | Cost/Day | Cost/Month |
|--------------|----------|------------|
| 100 | $0.06 | $1.80 |
| 1,000 | $0.60 | $18.00 |
| 10,000 | $6.00 | $180.00 |

**Using Gemini 1.5 Flash ($0.075 input / $0.30 output per 1M tokens):**

| Messages/Day | Cost/Day | Cost/Month |
|--------------|----------|------------|
| 100 | $0.006 | $0.18 |
| 1,000 | $0.06 | $1.80 |
| 10,000 | $0.60 | $18.00 |

**Cost optimization tips:**
- Use faster, cheaper models for simple queries (GPT-3.5, Gemini Flash)
- Reserve expensive models (GPT-4, Claude Opus) for complex questions
- Implement caching for frequently asked questions
- Set confidence thresholds to avoid AI responses for unclear queries

---

## Troubleshooting

### Error: "Invalid API key"

**Cause:** Wrong or expired API key

**Solution:**
1. Verify key format:
   - OpenRouter: `sk-or-v1-...`
   - OpenAI: `sk-proj-...` or `sk-...`
   - Anthropic: `sk-ant-...`
   - Gemini: `AIzaSy...`
2. Check for extra spaces or line breaks in `.env` file
3. Regenerate key from provider dashboard
4. Restart backend: `docker-compose restart backend`

### Error: "Insufficient credits" or "Quota exceeded"

**Cause:** No credits remaining or exceeded rate limits

**Solution:**

**For OpenRouter:**
1. Go to [openrouter.ai/credits](https://openrouter.ai/credits)
2. Add more credits

**For OpenAI:**
1. Go to [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Add payment method or increase spending limit

**For Anthropic:**
1. Go to Console → Settings → Billing
2. Add more credits

**For Gemini:**
1. Check free tier limits (60 req/min, 1,500 req/day)
2. Wait for quota reset (resets daily at midnight Pacific Time)
3. Upgrade to paid plan for higher limits

### Error: "Model not found"

**Cause:** Model name typo or model not available with your provider

**Solution:**
1. Check model name spelling in `DEFAULT_AI_MODEL`
2. Verify model is available for your provider:
   - OpenRouter: [openrouter.ai/models](https://openrouter.ai/models)
   - OpenAI: [platform.openai.com/docs/models](https://platform.openai.com/docs/models)
   - Anthropic: [docs.anthropic.com/models](https://docs.anthropic.com/claude/docs/models-overview)
3. Use correct format:
   - OpenRouter: `anthropic/claude-3.5-sonnet`
   - Direct: `claude-3-5-sonnet-20241022`

### Slow responses (> 5 seconds)

**Cause:** Large model or high server load

**Solution:**
1. Switch to faster model:
   - Use `gpt-3.5-turbo` instead of `gpt-4`
   - Use `claude-3-haiku` instead of `claude-3-opus`
   - Use `gemini-1.5-flash` instead of `gemini-1.5-pro`
2. Reduce max tokens in system prompt
3. Check provider status page for outages

### Responses in wrong language

**Cause:** AI detected wrong language or system prompt unclear

**Solution:**
1. Add language instruction to system prompt
2. Go to **Settings** → **AI**
3. Update system prompt:
   ```
   You are a customer support assistant. 
   ALWAYS respond in English regardless of input language.
   ```
4. Or specify user's language:
   ```
   You are a customer support assistant.
   Respond in the same language as the user's message.
   ```

---

**Next:** [Configure Stripe](stripe.md) for payment processing (optional).
