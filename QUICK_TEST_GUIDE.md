# Quick Test Guide - Comment Monitoring System

**Time:** 10-15 minutes
**Goal:** Verify all features work end-to-end

---

## Prerequisites

- [ ] Backend running (`uvicorn app.main:app --reload`)
- [ ] Celery worker running (`celery -A app.workers.celery_app worker -l info`)
- [ ] Celery beat running (`celery -A app.workers.celery_app beat -l info`)
- [ ] Frontend running (`npm run dev`)
- [ ] Instagram account connected

---

## Test 1: AI Control Toggles (2 min)

### Comments Toggle

1. Go to: **Dashboard → Comment Monitoring**
2. Look for: **"Monitoring Settings"** panel
3. Find toggle: **"AI auto-replies on comments"**
4. Test:
   - ✅ Toggle OFF → Should turn red/grey
   - ✅ Toggle ON → Should turn green
   - ✅ Click "Save Settings" → Should save successfully

### Conversations Toggle

1. Go to: **Dashboard → Settings → AI**
2. Scroll to: **"Conversation AI Controls"** card
3. Find toggle: **"AI auto-replies for DMs/Chats"**
4. Test:
   - ✅ Toggle OFF → Should disable
   - ✅ Toggle ON → Should enable
   - ✅ Click "Save Changes" → Should save

**Expected Result:** Both toggles work independently

---

## Test 2: Comment Polling (3 min)

### Sync Instagram Posts

1. Go to: **Dashboard → Comment Monitoring**
2. Click: **"Sync Instagram Posts"** button
3. Wait for: Success message

**Expected Result:**
```
✅ Successfully imported X posts, Y monitored
```

### Check Database

```bash
# Connect to Supabase database
psql <your_connection_string>

# Verify posts imported
SELECT id, platform, caption, monitoring_enabled
FROM monitored_posts
LIMIT 5;
```

**Expected Result:** Posts are in database with `monitoring_enabled = true`

---

## Test 3: Force Comment Poll (2 min)

### Trigger Manual Poll

```bash
# Use debug endpoint to force immediate polling
curl -X POST http://localhost:8000/api/debug/comments/force-poll \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "success": true,
  "metrics": {
    "posts_checked": 5,
    "comments_found": 3,
    "errors": 0
  }
}
```

### Check Logs

```bash
# Watch Celery worker logs
tail -f celery.log | grep "\\[POLL\\]"
```

**Expected Log Output:**
```
[POLL] Checking 5 monitored posts for new comments
[POLL] Post abc-123: found 2 new comments
[POLL] Completed: 5 posts checked, 3 comments found
```

---

## Test 4: AI Context Enrichment (3 min)

### Post a Test Comment

1. **On Instagram:**
   - Go to one of your recent posts
   - Comment: `"How much does this cost?"`

2. **Wait 5 minutes** (or force poll again)

3. **Check AI Context:**
```bash
# Get comment ID from database
psql <connection_string> -c "SELECT id, text FROM comments ORDER BY created_at DESC LIMIT 1;"

# View AI context for that comment
curl http://localhost:8000/api/debug/comments/comment-context/{COMMENT_ID} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "context": {
    "comment": {
      "text": "How much does this cost?",
      "author_name": "test_user"
    },
    "post": {
      "caption": "New product launch!",
      "media_url": "https://..."
    },
    "ai_context_parts": [
      {
        "type": "image_url",
        "image_url": {"url": "https://..."}
      },
      {
        "type": "text",
        "text": "📸 Post Caption: New product launch!\n\n❓ New Comment: How much does this cost?"
      }
    ]
  }
}
```

**Verify:**
- ✅ Context includes post image URL
- ✅ Context includes caption
- ✅ Context includes comment text

---

## Test 5: Conversation Detection (3 min)

### Test @mention Detection

```bash
curl -X POST http://localhost:8000/api/debug/comments/test-should-respond \
  -H "Content-Type: application/json" \
  -d '{
    "comment": {
      "text": "@sarah_jones I totally agree with you!",
      "author_name": "john_doe",
      "parent_id": null
    },
    "post": {
      "caption": "New product launch",
      "owner_username": "my_brand"
    },
    "owner_username": "my_brand",
    "all_comments": []
  }'
```

**Expected Response:**
```json
{
  "should_respond": false,
  "reason": "user_conversation",
  "explanation": "Comment mentions @sarah_jones (not owner)"
}
```

### Test Direct Question

```bash
curl -X POST http://localhost:8000/api/debug/comments/test-should-respond \
  -H "Content-Type: application/json" \
  -d '{
    "comment": {
      "text": "How much does this cost?",
      "author_name": "customer",
      "parent_id": null
    },
    "post": {
      "caption": "New product",
      "owner_username": "my_brand"
    },
    "owner_username": "my_brand",
    "all_comments": []
  }'
```

**Expected Response:**
```json
{
  "should_respond": true,
  "reason": "respond",
  "explanation": "Direct question detected"
}
```

---

## Test 6: AI Flag Enforcement (2 min)

### Disable AI for Comments

1. Go to **Comment Monitoring**
2. Toggle **"AI auto-replies on comments"** OFF
3. Click **"Save Settings"**

### Post Test Comment

1. On Instagram, comment: `"Test with AI disabled"`
2. Force poll:
```bash
curl -X POST http://localhost:8000/api/debug/comments/force-poll \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Worker Logs

```bash
tail -f celery.log | grep "AI disabled"
```

**Expected Log:**
```
[PROCESS] AI disabled for comments (user_id=xxx). Skipping AI processing for comment
```

### Verify in Database

```bash
psql <connection_string> -c "SELECT triage FROM comments WHERE text LIKE 'Test with AI%';"
```

**Expected Result:**
```
 triage
--------
 ignore
```

**Verification:**
- ✅ Comment is saved
- ✅ Triage is 'ignore'
- ✅ No AI reply generated

---

## Test 7: Vision AI Response (5 min)

### Re-enable AI

1. Toggle **"AI auto-replies on comments"** ON
2. Save settings

### Post Image-Related Question

1. On Instagram, comment on a **product photo**:
   - `"What color is the product in the image?"`

2. Force poll or wait 5 min

3. Check for AI reply:
```bash
psql <connection_string> -c "
  SELECT author_name, text, triage, ai_reply_text
  FROM comments
  WHERE text LIKE '%color%'
  ORDER BY created_at DESC
  LIMIT 1;
"
```

**Expected Result:**
```
 author_name | text                              | triage  | ai_reply_text
-------------+-----------------------------------+---------+------------------
 test_user   | What color is the product in...   | respond | The product appears to be blue...
```

**Verification:**
- ✅ AI saw the image (mentions color)
- ✅ Response is contextual
- ✅ Reply posted on Instagram

---

## Troubleshooting

### Issue: No comments fetched

**Check:**
```bash
# Verify Instagram credentials
psql <connection_string> -c "
  SELECT platform, account_id, access_token IS NOT NULL as has_token
  FROM social_accounts
  WHERE platform = 'instagram';
"
```

**Solution:** Reconnect Instagram account if `has_token = false`

---

### Issue: AI not responding

**Check:**
1. AI global toggle: Settings → AI → "Activer l'IA" = ON
2. Comment AI toggle: Comment Monitoring → "AI auto-replies" = ON
3. Worker logs for errors

**Debug:**
```bash
# Check monitoring rules
psql <connection_string> -c "
  SELECT user_id, ai_enabled_for_comments
  FROM monitoring_rules;
"
```

---

### Issue: Conversation detection too aggressive

**Adjust:** Modify rules in `backend/app/services/comment_triage.py`

**Test:** Use `/api/debug/comments/test-should-respond` endpoint

---

## Success Criteria

- [x] Both AI toggles work (comments + conversations)
- [x] Instagram posts sync successfully
- [x] Comments are fetched from Instagram
- [x] AI context includes images
- [x] Conversation detection prevents spam
- [x] AI flag enforcement works
- [x] AI replies are posted to Instagram

**If all checked:** ✅ System is production ready!

---

## Next Steps

1. **Monitor for 24 hours** - Watch for errors
2. **Test with real customers** - Verify responses are good
3. **Add Facebook connector** - Follow integration guide
4. **Fetch music metadata** - Enhance context

---

## Support

**Logs Location:**
- Celery: `celery.log`
- FastAPI: Console output
- Frontend: Browser DevTools

**Debug Endpoints:**
- `/api/debug/comments/force-poll`
- `/api/debug/comments/comment-context/{id}`
- `/api/debug/comments/test-should-respond`

**Documentation:**
- API Docs: `.agent/System/comment-monitoring-unified-api.md`
- Integration Guide: `.agent/SOP/add-new-social-platform.md`

---

**Test Duration:** 10-15 minutes
**Status:** Ready to test ✅
