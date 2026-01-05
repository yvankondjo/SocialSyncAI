# Meta Platforms Configuration

**Connect Instagram, WhatsApp, and Messenger to SocialSync AI.**

This guide shows you how to create a Meta Developer app and configure OAuth for social media integrations.

---

## Table of Contents

- [Overview](#overview)
- [Create a Meta Developer account](#create-a-meta-developer-account)
- [Create a Meta app](#create-a-meta-app)
- [Configure Instagram](#configure-instagram)
- [Configure WhatsApp](#configure-whatsapp)
- [Configure Messenger](#configure-messenger)
- [Update environment variables](#update-environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Meta Developer provides a single app for all Meta platform integrations.**

One Meta app enables:
- Instagram Business Account messaging and posting
- WhatsApp Business API messaging
- Messenger (Facebook Pages) messaging

**What you'll need:**
- Facebook account
- Business verification (for production WhatsApp)
- Instagram Business Account (for Instagram features)
- Facebook Page (for Messenger features)

**Estimated setup time:** 15-20 minutes

---

## Create a Meta Developer account

**Step 1: Sign up**

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click "Get Started"
3. Log in with your Facebook account
4. Complete registration (accept terms, verify email)

**Step 2: Register as developer**

1. Enter your name
2. Verify your email address
3. Accept Meta Platform Terms and Policies

---

## Create a Meta app

**Step 1: Create new app**

1. In Meta Developer dashboard, click "Create App"
2. **Use case:** Select "Other" → "Business"
3. Click "Next"

**Step 2: App details**

1. **App name:** Enter a name (e.g., "SocialSync AI Production")
2. **Contact email:** Your email address
3. **Business account:** Select or create a Meta Business Account
4. Click "Create App"

**Step 3: Get app credentials**

1. Go to **App Settings** → **Basic**
2. **Save these values:**
   - **App ID** → Copy to `META_APP_ID`
   - **App Secret** → Click "Show", copy to `META_APP_SECRET`

---

## Configure Instagram

**Instagram integration enables direct messages and post scheduling.**

### Add Instagram product

**Step 1: Add product**

1. In your Meta app dashboard, click "Add Products"
2. Find **Instagram** → Click "Set Up"
3. Choose **Instagram Basic Display** or **Instagram Graph API**

**Recommended:** Use Instagram Graph API for full features (requires Instagram Business Account).

### Configure OAuth

**Step 2: Add redirect URI**

1. Go to **Instagram** → **Basic Display** → **Settings**
2. Find **OAuth Redirect URIs**
3. Add your callback URL:
   ```
   https://yourdomain.com/api/social-accounts/connect/instagram/callback
   ```
4. For local testing, also add:
   ```
   http://localhost:8000/api/social-accounts/connect/instagram/callback
   ```
5. Click "Save Changes"

### Request permissions

**Step 3: App permissions**

Instagram Graph API requires these permissions:
- `instagram_basic` - Basic profile information
- `instagram_content_publish` - Post photos and videos
- `instagram_manage_messages` - Send and receive DMs
- `instagram_manage_comments` - Read and reply to comments

**To request:**
1. Go to **App Review** → **Permissions and Features**
2. Search for each permission above
3. Click "Request Advanced Access"
4. Provide business verification (may take 1-3 days for review)

---

## Configure WhatsApp

**WhatsApp Business API enables automated messaging at scale.**

### Add WhatsApp product

**Step 1: Add product**

1. In your Meta app, click "Add Products"
2. Find **WhatsApp** → Click "Set Up"
3. Choose **WhatsApp Business Platform**

### Embedded Signup

**Step 2: Configure Embedded Signup**

**Embedded Signup lets users connect their WhatsApp Business accounts through your UI.**

1. Go to **WhatsApp** → **Configuration**
2. Find **Embedded Signup Configuration ID**
3. Copy the Config ID → Save as `META_CONFIG_ID`

**Step 3: Add callback URL**

1. In **Embedded Signup settings**, add:
   ```
   https://yourdomain.com/api/social-accounts/connect/whatsapp/callback
   ```
2. Save changes

### Webhook configuration

**Webhooks deliver incoming WhatsApp messages to your backend.**

See [Webhooks Configuration](webhooks.md#whatsapp) for detailed setup.

**Quick setup:**

1. Go to **WhatsApp** → **Configuration** → **Webhook**
2. **Callback URL:** `https://yourdomain.com/api/whatsapp/webhook`
3. **Verify token:** Choose a random string, save as `WHATSAPP_VERIFY_TOKEN`
4. **Subscription fields:** Enable `messages`
5. Click "Verify and Save"

---

## Configure Messenger

**Messenger integration enables Facebook Page messaging.**

### Add Messenger product

**Step 1: Add product**

1. In your Meta app, click "Add Products"
2. Find **Messenger** → Click "Set Up"

### Configure OAuth

**Step 2: Add redirect URI**

1. Go to **Messenger** → **Settings**
2. Find **Redirect URIs**
3. Add:
   ```
   https://yourdomain.com/api/social-accounts/connect/messenger/callback
   ```
4. Save changes

### Request permissions

**Step 3: Required permissions**

Request these permissions in **App Review**:
- `pages_messaging` - Send and receive messages
- `pages_read_engagement` - Read page content
- `pages_manage_metadata` - Manage page settings
- `pages_show_list` - List pages user manages

### Webhook configuration

**Step 4: Subscribe to webhooks**

1. Go to **Messenger** → **Configuration** → **Webhooks**
2. **Callback URL:** `https://yourdomain.com/api/messenger/webhook`
3. **Verify token:** Choose a random string, save as `MESSENGER_VERIFY_TOKEN`
4. **Subscription fields:** Enable `messages`, `messaging_postbacks`
5. Click "Verify and Save"

---

## Update environment variables

**Add Meta credentials to `backend/.env`:**

```bash
# Meta App Credentials (Required for all platforms)
META_APP_ID=1234567890123456
META_APP_SECRET=abcdef1234567890abcdef1234567890
META_GRAPH_VERSION=v21.0
META_CONFIG_ID=1234567890  # Only for WhatsApp

# Instagram
INSTAGRAM_CLIENT_ID=1234567890123456  # Usually same as META_APP_ID
INSTAGRAM_CLIENT_SECRET=abcdef1234567890abcdef1234567890  # Usually same as META_APP_SECRET
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/social-accounts/connect/instagram/callback
INSTAGRAM_VERIFY_TOKEN=your_random_secure_string_123

# WhatsApp
WHATSAPP_REDIRECT_URI=https://yourdomain.com/api/social-accounts/connect/whatsapp/callback
WHATSAPP_VERIFY_TOKEN=your_random_secure_string_456

# Messenger
MESSENGER_VERIFY_TOKEN=your_random_secure_string_789
```

**Important:** For local development, use `http://localhost:8000` instead of `https://yourdomain.com`.

---

## Troubleshooting

### OAuth callback error: "redirect_uri_mismatch"

**Cause:** Redirect URI in Meta app doesn't match the one sent in OAuth request

**Solution:**
1. Check **exact URL** in Meta Developer settings
2. Must match exactly: `https://yourdomain.com/api/social-accounts/connect/instagram/callback`
3. Include or exclude trailing slash consistently
4. Use https:// (not http://) for production
5. For local testing, add `http://localhost:8000/...` separately

### Webhook verification failed (403)

**Cause:** Verify token doesn't match

**Solution:**
1. Verify token in Meta webhook settings must **exactly match** environment variable
2. Check for extra spaces or line breaks
3. Token is case-sensitive
4. Restart backend after changing: `docker-compose restart backend`

### "App Not Set Up" error

**Cause:** Instagram product not added or not configured

**Solution:**
1. Go to Meta app → **Products**
2. Ensure Instagram is in "Products Added" section
3. Complete Basic Display or Graph API setup
4. Add redirect URI in Instagram settings

### Permission denied errors

**Cause:** Missing required permissions or permissions not approved

**Solution:**
1. Go to **App Review** → **Permissions and Features**
2. Verify all required permissions show "Approved" or "Standard Access"
3. Some permissions require business verification (can take 1-3 days)
4. For testing, use **Test Users** in **Roles** section

### WhatsApp Embedded Signup not working

**Cause:** Missing Config ID or wrong callback URL

**Solution:**
1. Verify `META_CONFIG_ID` is set in backend/.env
2. Check callback URL matches exactly in Embedded Signup settings
3. Ensure WhatsApp product is added to your app
4. Try using Meta's test phone number first before real WhatsApp account

### "Invalid App ID" error

**Cause:** Wrong `META_APP_ID` or app is in development mode

**Solution:**
1. Double-check App ID in App Settings → Basic
2. Ensure app is "Live" not "Development Mode" for production
3. If using development mode, add test users in **Roles** section

---

**Next:** [Configure Webhooks](webhooks.md) for real-time message delivery.
