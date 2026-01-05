# Webhooks Configuration

**Webhooks deliver real-time events from Instagram, WhatsApp, Messenger, and Stripe to your backend.**

This guide shows you how to configure webhooks for instant message and payment notifications.

---

## Table of Contents

- [What are webhooks?](#what-are-webhooks)
- [Webhook endpoints in SocialSync AI](#webhook-endpoints-in-socialsync-ai)
- [Test locally with ngrok](#test-locally-with-ngrok)
- [Configure Instagram webhooks](#configure-instagram-webhooks)
- [Configure WhatsApp webhooks](#configure-whatsapp-webhooks)
- [Configure Messenger webhooks](#configure-messenger-webhooks)
- [Configure Stripe webhooks](#configure-stripe-webhooks)
- [Production deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## What are webhooks?

**Webhooks push notifications to your server when events occur.**

Instead of polling APIs every few seconds to check for new messages, webhooks deliver events instantly:
- New Instagram DM received → Webhook fires → Your backend processes it
- WhatsApp message sent → Webhook fires → Message saved to database
- Stripe payment completed → Webhook fires → User credits updated

**Benefits:**
- **Real-time:** Events delivered in under 1 second
- **Efficient:** No constant polling required
- **Reliable:** Meta and Stripe retry failed deliveries

---

## Webhook endpoints in SocialSync AI

**SocialSync AI exposes four webhook endpoints:**

| Platform | Endpoint | Handles |
|----------|----------|---------|
| **Instagram** | `/api/instagram/webhook` | Direct messages, comments, mentions |
| **WhatsApp** | `/api/whatsapp/webhook` | Business messages, status updates |
| **Messenger** | `/api/messenger/webhook` | Page messages, postbacks |
| **Stripe** | `/api/stripe/webhook` | Payment events, subscription changes |

**Each endpoint handles two types of requests:**

1. **GET request (Verification)** - Meta/Stripe verifies you own the endpoint
2. **POST request (Event delivery)** - Actual event data sent to your server

---

## Test locally with ngrok

**ngrok creates a public HTTPS URL that tunnels to your local machine.**

This lets you test webhooks during development without deploying to production.

### Install ngrok

**Step 1: Download ngrok**

- Go to [ngrok.com](https://ngrok.com)
- Sign up for free account
- Download ngrok for your platform

**Step 2: Authenticate**

```bash
ngrok authtoken YOUR_AUTH_TOKEN
```

Replace `YOUR_AUTH_TOKEN` with the token from your ngrok dashboard.

### Start ngrok tunnel

**Step 3: Start your backend**

```bash
docker-compose up backend
```

Backend should be running on `http://localhost:8000`

**Step 4: Create tunnel**

Open a new terminal and run:

```bash
ngrok http 8000
```

**You'll see output like:**

```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`) - this is your public webhook URL.

### Use ngrok URL in webhooks

**When configuring webhooks in Meta/Stripe dashboards, use:**

- Instagram: `https://abc123.ngrok.io/api/instagram/webhook`
- WhatsApp: `https://abc123.ngrok.io/api/whatsapp/webhook`
- Messenger: `https://abc123.ngrok.io/api/messenger/webhook`
- Stripe: `https://abc123.ngrok.io/api/stripe/webhook`

**Note:** ngrok free tier URLs change every time you restart. Paid plans ($8/month) provide persistent URLs.

---

## Configure Instagram webhooks

**Instagram webhooks deliver DMs, comments, and mentions in real-time.**

### Prerequisites

- ✅ Meta app created with Instagram product added
- ✅ Backend running (locally with ngrok or production)
- ✅ `INSTAGRAM_VERIFY_TOKEN` set in `backend/.env`

### Setup steps

**Step 1: Go to webhook settings**

1. Open [Meta Developer dashboard](https://developers.facebook.com/apps)
2. Select your app
3. Go to **Instagram** → **Configuration** → **Webhooks**

**Step 2: Add webhook subscription**

1. Click "Add Subscription"
2. **Callback URL:** Enter your webhook URL
   - Local: `https://your-ngrok-url.ngrok.io/api/instagram/webhook`
   - Production: `https://yourdomain.com/api/instagram/webhook`
3. **Verify Token:** Enter the same value as `INSTAGRAM_VERIFY_TOKEN` in your `.env`
4. Click "Verify and Save"

**What happens during verification:**
- Meta sends GET request to your webhook URL
- Your backend checks if `hub.verify_token` matches `INSTAGRAM_VERIFY_TOKEN`
- If match, backend returns `hub.challenge` value
- Meta confirms webhook is valid

**Step 3: Subscribe to events**

After verification succeeds, select which events to receive:

- ✅ **messages** - Direct messages (required)
- ✅ **messaging_postbacks** - Button clicks in messages
- ✅ **comments** - Comments on posts (optional)
- ✅ **mentions** - When account is mentioned (optional)

Click "Subscribe"

**Step 4: Test webhook**

Send a DM to your Instagram Business account from another account.

**Check backend logs:**

```bash
docker-compose logs -f backend
```

You should see:
```
INFO: Received Instagram webhook event
INFO: Processing message from user_id=123456
```

---

## Configure WhatsApp webhooks

**WhatsApp webhooks deliver business messages and status updates.**

### Prerequisites

- ✅ Meta app with WhatsApp product added
- ✅ WhatsApp Business Account connected
- ✅ `WHATSAPP_VERIFY_TOKEN` set in `backend/.env`

### Setup steps

**Step 1: Go to webhook settings**

1. Open Meta Developer dashboard
2. Select your app
3. Go to **WhatsApp** → **Configuration** → **Webhook**

**Step 2: Configure webhook**

1. **Callback URL:** 
   - Local: `https://your-ngrok-url.ngrok.io/api/whatsapp/webhook`
   - Production: `https://yourdomain.com/api/whatsapp/webhook`
2. **Verify Token:** Same as `WHATSAPP_VERIFY_TOKEN` in `.env`
3. Click "Verify and Save"

**Step 3: Subscribe to message events**

After verification, WhatsApp automatically subscribes to:
- ✅ **messages** - Incoming messages
- ✅ **message_status** - Delivery/read receipts

No manual subscription needed for WhatsApp.

**Step 4: Test webhook**

Send a WhatsApp message to your business number.

Check backend logs for:
```
INFO: Received WhatsApp webhook event
INFO: Processing message from phone=+1234567890
```

---

## Configure Messenger webhooks

**Messenger webhooks deliver Facebook Page messages.**

### Prerequisites

- ✅ Meta app with Messenger product added
- ✅ Facebook Page connected
- ✅ `MESSENGER_VERIFY_TOKEN` set in `backend/.env`

### Setup steps

**Step 1: Go to webhook settings**

1. Open Meta Developer dashboard
2. Select your app
3. Go to **Messenger** → **Configuration** → **Webhooks**

**Step 2: Add webhook subscription**

1. **Callback URL:**
   - Local: `https://your-ngrok-url.ngrok.io/api/messenger/webhook`
   - Production: `https://yourdomain.com/api/messenger/webhook`
2. **Verify Token:** Same as `MESSENGER_VERIFY_TOKEN` in `.env`
3. Click "Verify and Save"

**Step 3: Subscribe to page events**

Select events to receive:
- ✅ **messages** - Page messages (required)
- ✅ **messaging_postbacks** - Button clicks
- ✅ **message_deliveries** - Delivery confirmations
- ✅ **message_reads** - Read receipts

**Step 4: Subscribe page to app**

1. Go to **Messenger** → **Configuration** → **Pages**
2. Click "Add or Remove Pages"
3. Select your Facebook Page
4. Grant required permissions
5. Click "Subscribe" next to your page

**Step 5: Test webhook**

Send a message to your Facebook Page.

Check backend logs for:
```
INFO: Received Messenger webhook event
INFO: Processing message for page_id=123456
```

---

## Configure Stripe webhooks

**Stripe webhooks notify your backend of payment events.**

### Prerequisites

- ✅ Stripe account created
- ✅ `STRIPE_SECRET_KEY` set in `backend/.env`

### Setup steps

**Step 1: Go to webhook settings**

1. Open [Stripe Dashboard](https://dashboard.stripe.com)
2. Go to **Developers** → **Webhooks**
3. Click "Add endpoint"

**Step 2: Add endpoint**

1. **Endpoint URL:**
   - Local: `https://your-ngrok-url.ngrok.io/api/stripe/webhook`
   - Production: `https://yourdomain.com/api/stripe/webhook`
2. **Description:** "SocialSync AI payments"
3. **Events to send:** Select:
   - ✅ `checkout.session.completed` - Payment completed
   - ✅ `invoice.payment_succeeded` - Subscription payment
   - ✅ `invoice.payment_failed` - Payment failed
   - ✅ `customer.subscription.updated` - Subscription changed
   - ✅ `customer.subscription.deleted` - Subscription cancelled
4. Click "Add endpoint"

**Step 3: Get webhook signing secret**

After creating endpoint:
1. Click on the endpoint you just created
2. Click "Reveal" next to **Signing secret**
3. Copy the value (starts with `whsec_`)
4. Add to `backend/.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_abc123...
   ```
5. Restart backend: `docker-compose restart backend`

**Step 4: Test webhook**

Stripe provides a test button:
1. In webhook endpoint details, click "Send test webhook"
2. Select `checkout.session.completed`
3. Click "Send test event"

Check backend logs:
```
INFO: Received Stripe webhook event
INFO: Processing checkout.session.completed
```

---

## Production deployment

**When deploying to production, update webhook URLs in all platforms.**

### Update environment variables

**Set production URLs in `backend/.env`:**

```bash
BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### Update webhook URLs

**Replace ngrok URLs with production domain in:**

1. **Meta Developer → Instagram webhook**: `https://api.yourdomain.com/api/instagram/webhook`
2. **Meta Developer → WhatsApp webhook**: `https://api.yourdomain.com/api/whatsapp/webhook`
3. **Meta Developer → Messenger webhook**: `https://api.yourdomain.com/api/messenger/webhook`
4. **Stripe → Webhooks**: `https://api.yourdomain.com/api/stripe/webhook`

**Each platform will re-verify your endpoint.**

### SSL certificate required

**All webhook URLs must use HTTPS (not HTTP).**

Production hosting providers (Google Cloud Run, Railway, Vercel) automatically provide SSL certificates.

For custom domains:
- Use Let's Encrypt (free SSL)
- Configure SSL before setting up webhooks
- Ensure certificate is valid and not expired

---

## Troubleshooting

### Webhook verification failed (403)

**Error:** "The challenge could not be validated"

**Cause:** Verify token mismatch

**Solution:**
1. Check `INSTAGRAM_VERIFY_TOKEN` / `WHATSAPP_VERIFY_TOKEN` / `MESSENGER_VERIFY_TOKEN` in `backend/.env`
2. Must **exactly match** the token in Meta webhook settings (case-sensitive)
3. Remove extra spaces or line breaks
4. Restart backend: `docker-compose restart backend`
5. Try verification again in Meta dashboard

### Webhook verification succeeded but no events received

**Cause:** Not subscribed to correct events or page not subscribed

**Solution:**

**For Instagram/Messenger:**
1. Verify event subscriptions are checked (messages, comments, etc.)
2. Click "Subscribe" after selecting events

**For Messenger specifically:**
1. Go to **Messenger** → **Configuration** → **Pages**
2. Ensure page shows "Subscribed" status
3. If not, click "Subscribe"

**For WhatsApp:**
1. Verify WhatsApp Business Account is connected
2. Check phone number is verified
3. Ensure message template is approved (for sending messages)

### ngrok session expired

**Error:** Webhook URL not reachable

**Cause:** ngrok free tier sessions expire after 2 hours

**Solution:**
1. Restart ngrok: `ngrok http 8000`
2. Get new URL
3. Update webhook URL in Meta/Stripe dashboards
4. Re-verify webhook

**Avoid this:** Upgrade to ngrok paid plan ($8/month) for persistent URLs and longer sessions.

### SSL certificate errors

**Error:** "SSL certificate problem: unable to get local issuer certificate"

**Cause:** Invalid or expired SSL certificate

**Solution:**
1. Verify SSL certificate is valid: `curl -I https://yourdomain.com`
2. Use SSL checker: [ssllabs.com/ssltest](https://www.ssllabs.com/ssltest/)
3. Ensure certificate covers your domain (not just www. or vice versa)
4. Renew certificate if expired

### Webhook signature verification failed (Stripe)

**Error:** "No signatures found matching the expected signature"

**Cause:** Wrong `STRIPE_WEBHOOK_SECRET`

**Solution:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Click on your endpoint
3. Click "Reveal" next to Signing secret
4. Copy the `whsec_...` value
5. Update `STRIPE_WEBHOOK_SECRET` in `backend/.env`
6. Restart backend

### Events received but not processed

**Cause:** Error in event handler code

**Solution:**
1. Check backend logs: `docker-compose logs -f backend`
2. Look for Python exceptions or error messages
3. Verify database connection is working
4. Check required fields are present in webhook payload
5. Test with Stripe test events or send test messages

### Rate limiting errors

**Error:** "Too many requests"

**Cause:** Exceeding Meta/Stripe rate limits

**Solution:**
1. Implement exponential backoff in retry logic
2. Don't respond to webhooks synchronously (use Celery tasks)
3. Check for duplicate webhook deliveries
4. Meta: Max 200 requests per hour per user
5. Stripe: No hard limit but implement 1-second delays between retries

---

**Next:** [Configure AI Providers](ai-providers.md) to enable automated responses.
