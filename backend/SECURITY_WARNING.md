# 🚨 CRITICAL SECURITY WARNING

## Exposed Secrets Detected

The `backend/.env` file contains **REAL production secrets** that were previously committed to version control.

### Immediate Actions Required:

1. **Revoke ALL secrets** in the current `.env` file:
   - [ ] Instagram Client Secret
   - [ ] Supabase Service Role Key (CRITICAL - full database access)
   - [ ] Supabase JWT Secret
   - [ ] Supabase Database Password
   - [ ] Reddit Client Secret
   - [ ] Meta App Secret
   - [ ] OpenRouter API Key
   - [ ] Gemini API Key
   - [ ] LangSmith API Key
   - [ ] Resend API Key
   - [ ] Stripe Secret Key
   - [ ] All WhatsApp tokens

2. **Generate new secrets** for all services

3. **Update `.env`** with new credentials

4. **Verify `.env` is gitignored**:
   ```bash
   git check-ignore backend/.env
   # Should output: backend/.env
   ```

5. **Check git history** for exposed secrets:
   ```bash
   git log --all --full-history -- backend/.env
   ```
   If the file was ever committed, consider rotating ALL credentials.

6. **Remove from git history** (if committed):
   ```bash
   # WARNING: This rewrites git history!
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch backend/.env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

### How to Use `.env.example`:

1. Copy template:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Fill in your **new** credentials

3. Never commit `.env` to git

## Security Best Practices:

- ✅ Use environment-specific secrets (dev vs prod)
- ✅ Rotate secrets regularly
- ✅ Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- ✅ Enable MFA on all service accounts
- ❌ Never commit `.env` files
- ❌ Never hardcode secrets in code
- ❌ Never share secrets in Slack/Discord/Email
