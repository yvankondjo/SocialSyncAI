# Stripe Configuration

**Enable payment processing and user billing with Stripe.**

This guide shows you how to set up Stripe for subscription management and payment processing in SocialSync AI.

---

## Table of Contents

- [When do you need Stripe?](#when-do-you-need-stripe)
- [Create a Stripe account](#create-a-stripe-account)
- [Get your API keys](#get-your-api-keys)
- [Configure webhook](#configure-webhook)
- [Create products and prices](#create-products-and-prices)
- [Test payment flow](#test-payment-flow)
- [Go live checklist](#go-live-checklist)
- [Troubleshooting](#troubleshooting)

---

## When do you need Stripe?

**Stripe is optional.** You only need it if you plan to charge users for your service.

**Use cases for Stripe:**
- **SaaS monetization** - Charge monthly/yearly subscriptions
- **Credit-based pricing** - Sell AI message credits
- **Usage-based billing** - Charge per API call or message
- **One-time payments** - Sell access to premium features

**Skip Stripe if:**
- Running self-hosted for personal use
- Offering free service only
- Using alternative payment processor

---

## Create a Stripe account

**Step 1: Sign up**

1. Go to [stripe.com/register](https://stripe.com/register)
2. Enter email and create password
3. Verify email address
4. Complete phone verification

**Step 2: Activate account**

1. Click "Activate your account"
2. Select **Business type:**
   - Individual (sole proprietor)
   - Company
3. Enter business details:
   - Business name
   - Business address
   - Tax ID (if applicable)
4. Enter bank account for payouts
5. Complete verification

**New accounts can use test mode immediately.** Live mode requires business verification (1-2 business days).

---

## Get your API keys

**Stripe provides separate keys for testing and production.**

### Test keys (Development)

**Step 1: Access test keys**

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Ensure **Test mode** toggle is ON (top right)
3. Go to **Developers** → **API keys**

**Step 2: Copy test keys**

You'll see two keys:

| Key | Name | Starts with | Used for |
|-----|------|-------------|----------|
| **Publishable key** | Test mode | `pk_test_` | Frontend, safe to expose |
| **Secret key** | Test mode | `sk_test_` | Backend, keep secret |

**Copy both keys.**

### Live keys (Production)

**After business verification completes:**

1. Toggle **Test mode** to OFF
2. Go to **Developers** → **API keys**
3. Copy **Live** keys (start with `pk_live_` and `sk_live_`)

**Important:** Never expose secret keys (`sk_test_` or `sk_live_`) in frontend code or public repositories.

### Add to environment

**For testing, add test keys to `backend/.env`:**

```bash
# Stripe Configuration - Test Mode
STRIPE_SECRET_KEY=sk_test_abc123...
STRIPE_PUBLISHABLE_KEY=pk_test_abc123...
```

**For production, use live keys:**

```bash
# Stripe Configuration - Live Mode
STRIPE_SECRET_KEY=sk_live_abc123...
STRIPE_PUBLISHABLE_KEY=pk_live_abc123...
```

Restart backend:
```bash
docker-compose restart backend
```

---

## Configure webhook

**Webhooks notify your backend when payments succeed or fail.**

### Create webhook endpoint

**Step 1: Go to webhooks**

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click "Add endpoint"

**Step 2: Add endpoint URL**

**For local testing with ngrok:**
```
https://your-ngrok-url.ngrok.io/api/stripe/webhook
```

**For production:**
```
https://api.yourdomain.com/api/stripe/webhook
```

**Step 3: Select events**

Click "Select events" and choose:
- ✅ `checkout.session.completed` - Checkout completed
- ✅ `invoice.payment_succeeded` - Subscription payment succeeded
- ✅ `invoice.payment_failed` - Payment failed
- ✅ `customer.subscription.created` - New subscription
- ✅ `customer.subscription.updated` - Subscription changed
- ✅ `customer.subscription.deleted` - Subscription cancelled

Click "Add events"

**Step 4: Add endpoint**

1. **Description:** "SocialSync AI Production" (optional)
2. Click "Add endpoint"

### Get webhook signing secret

**Step 5: Reveal signing secret**

1. Click on the endpoint you just created
2. Find **Signing secret** section
3. Click "Reveal"
4. Copy the secret (starts with `whsec_`)

**Step 6: Add to environment**

Add to `backend/.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_abc123...
```

Restart backend:
```bash
docker-compose restart backend
```

**Test webhook:**

1. In endpoint details, click "Send test webhook"
2. Select `checkout.session.completed`
3. Click "Send test event"

Check backend logs for:
```
INFO: Received Stripe webhook event
INFO: Processing checkout.session.completed for customer=cus_abc123
```

---

## Create products and prices

**Products define what you're selling. Prices define how much it costs.**

### Create a product

**Step 1: Go to products**

1. In Stripe Dashboard, go to **Products**
2. Click "Add product"

**Step 2: Product details**

1. **Name:** "SocialSync AI Pro" (or your plan name)
2. **Description:** "Professional plan with unlimited AI responses"
3. **Image:** Upload logo (optional)
4. Click "Add product"

### Add pricing

**Step 3: Add price**

After creating product:

1. Click "Add another price"
2. **Pricing model:** Choose one:
   - **Standard pricing** - Fixed amount
   - **Package pricing** - Charge per unit (e.g., per 100 credits)
   - **Graduated pricing** - Volume discounts
   - **Volume pricing** - Price decreases with volume
3. **Price:** Enter amount (e.g., $29.00)
4. **Billing period:** Choose:
   - One time
   - Monthly
   - Yearly
   - Custom (weekly, every 6 months, etc.)
5. **Currency:** USD (or your currency)
6. Click "Add price"

**Copy the Price ID** (starts with `price_`) - you'll need this in your code.

### Example pricing structure

**Recommended setup for SaaS:**

| Plan | Price | Billing | Price ID |
|------|-------|---------|----------|
| Free | $0 | - | - |
| Pro | $29/month | Monthly | `price_pro_monthly` |
| Pro | $290/year | Yearly | `price_pro_yearly` |
| Enterprise | Custom | - | Contact sales |

---

## Test payment flow

**Verify checkout works end-to-end.**

### Test with Stripe test cards

**Stripe provides test card numbers that simulate different scenarios.**

**Successful payment:**
```
Card number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

**Other test scenarios:**

| Card Number | Result |
|-------------|--------|
| `4000 0000 0000 9995` | Declined (insufficient funds) |
| `4000 0000 0000 9987` | Declined (lost card) |
| `4000 0000 0000 0002` | Declined (generic) |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |

**Full list:** [stripe.com/docs/testing](https://stripe.com/docs/testing)

### Test checkout flow

**Step 1: Initiate checkout**

1. Log in to SocialSync AI frontend
2. Go to **Pricing** or **Upgrade** page
3. Click "Subscribe to Pro"

**Step 2: Complete test payment**

1. You'll be redirected to Stripe Checkout
2. Enter test card: `4242 4242 4242 4242`
3. Fill in other required fields
4. Click "Subscribe"

**Step 3: Verify success**

After payment:
1. You should be redirected back to SocialSync AI
2. Check **Settings** → **Subscription** shows "Pro" plan
3. User credits should be updated

**Step 4: Check Stripe Dashboard**

1. Go to **Payments** in Stripe Dashboard
2. You should see the test payment
3. Customer created with subscription active

---

## Go live checklist

**Before accepting real payments, complete these steps.**

### Business verification

**Required for live mode:**

- ✅ Business details verified
- ✅ Bank account added for payouts
- ✅ Tax information submitted
- ✅ Identity verification completed (if required)

**Check status:** Stripe Dashboard → Settings → Account

### Update configuration

**Switch from test to live:**

- ✅ Replace `sk_test_` with `sk_live_` in `STRIPE_SECRET_KEY`
- ✅ Replace `pk_test_` with `pk_live_` in `STRIPE_PUBLISHABLE_KEY`
- ✅ Create new webhook endpoint for production domain
- ✅ Update `STRIPE_WEBHOOK_SECRET` with live webhook secret
- ✅ Verify live products and prices are created

### Test in production

- ✅ Make a real $0.50 test payment to yourself
- ✅ Verify webhook received
- ✅ Check subscription activated correctly
- ✅ Test subscription cancellation
- ✅ Verify refund process works

### Legal requirements

- ✅ Terms of Service published
- ✅ Privacy Policy published
- ✅ Refund policy defined
- ✅ Billing descriptors configured (Settings → Business details → Statement descriptor)

### Monitoring

- ✅ Set up email notifications for failed payments
- ✅ Monitor Stripe Dashboard daily for first week
- ✅ Set up alerts for high chargeback rates

---

## Troubleshooting

### Error: "No such customer"

**Cause:** Customer ID not found in Stripe

**Solution:**
1. Verify customer was created during checkout
2. Check `customers` table in database has Stripe customer ID
3. Ensure webhook `checkout.session.completed` was processed
4. Create customer manually:
   ```bash
   curl -X POST http://localhost:8000/api/stripe/create-customer \
     -H "Authorization: Bearer YOUR_JWT" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```

### Webhook signature verification failed

**Error:** "No signatures found matching the expected signature"

**Cause:** Wrong `STRIPE_WEBHOOK_SECRET` or request not from Stripe

**Solution:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Click on your endpoint
3. Click "Reveal" next to Signing secret
4. Copy the `whsec_...` value exactly
5. Update in `backend/.env`
6. Restart backend
7. Test with "Send test webhook" in Stripe

### Payment succeeded but subscription not activated

**Cause:** Webhook not received or processing error

**Solution:**
1. Check webhook endpoint is configured in Stripe
2. Verify endpoint is accessible (use ngrok for local testing)
3. Check backend logs for webhook processing errors:
   ```bash
   docker-compose logs -f backend | grep stripe
   ```
4. Manually activate subscription as workaround:
   ```sql
   UPDATE users SET subscription_status = 'active' 
   WHERE email = 'user@example.com';
   ```
5. Fix webhook issue for future payments

### "Live mode is not available"

**Cause:** Business verification incomplete

**Solution:**
1. Go to Stripe Dashboard → Settings → Account
2. Complete all required verification steps
3. Add bank account for payouts
4. Submit business documents if requested
5. Wait for Stripe approval (usually 1-2 business days)

### Test payments work but live payments fail

**Cause:** Live API keys not configured or webhook issues

**Solution:**
1. Verify using live keys (start with `sk_live_`, not `sk_test_`)
2. Create separate webhook endpoint for live mode
3. Check live webhook secret is configured
4. Ensure products exist in live mode (test products don't transfer)
5. Verify bank account is connected (required for live mode)

### High decline rate

**Causes:** Various (insufficient funds, fraud detection, incorrect card details)

**Solutions:**
1. **Add payment retry logic** - Attempt payment 3 times over 7 days
2. **Send email reminders** - Notify users of failed payments
3. **Enable Stripe Radar** - Reduce fraudulent transactions
4. **Support more payment methods** - Add Apple Pay, Google Pay
5. **Check billing descriptor** - Ensure customers recognize the charge
6. **Reduce friction** - Don't require postal code if not needed

---

**Next:** [Architecture Overview](../architecture/overview.md) to understand system design.
