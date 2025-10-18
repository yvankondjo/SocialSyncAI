# AI Moderation System - Architecture & Integration

**Dernière mise à jour**: 2025-10-18
**Related Docs**: [Comment Polling](../Tasks/COMMENT_POLLING_IMPLEMENTATION.md), [Celery Workers](CELERY_WORKERS.md)

## Vue d'ensemble

Le système de modération AI protège les utilisateurs contre les contenus problématiques en utilisant OpenAI Moderation API comme guardrail principal et en envoyant automatiquement des emails d'escalation pour les cas graves.

**Nouveauté (2025-10-18)**: Contrôle granulaire avec `context_type` - permet d'activer/désactiver IA séparément pour chats vs commentaires.

---

## Architecture

### 1. Flow de décision (ordre de priorité)

```
Message/Comment entrant + context_type
    ↓
┌──────────────────────────────────┐
│ 1. Scope Check (NOUVEAU)        │
│    - Si context="chat":          │
│      ai_enabled_for_chats?       │
│    - Si context="comment":       │
│      ai_enabled_for_comments?    │
│    NO → IGNORE                   │
└──────────────────────────────────┘
    ↓ YES
┌─────────────────────────────┐
│ 2. AI Control activé?       │
│    ai_control_enabled?      │
│    NO → IGNORE              │
└─────────────────────────────┘
    ↓ YES
┌─────────────────────────────┐
│ 3. OpenAI Moderation API    │
│    Analyse: hate, violence, │
│    harassment, self-harm,   │
│    sexual, illicit          │
└─────────────────────────────┘
    ↓
 FLAGGED?
    ↓
   YES → Assess Severity
         ├─ HIGH → ESCALATE (+ email)
         └─ LOW → IGNORE
    ↓
   NO
    ↓
┌─────────────────────────────┐
│ 4. Custom User Rules        │
│    - Similarité exemples    │
│    - Mots-clés escalation   │
└─────────────────────────────┘
    ↓
 Match?
    ↓
   YES → IGNORE ou ESCALATE
    ↓
   NO
    ↓
┌─────────────────────────────┐
│ 4. DEFAULT → RESPOND        │
│    Continuer avec RAG agent │
└─────────────────────────────┘
```

### 2. Composants principaux

#### AIDecisionService
**Fichier**: `/workspace/backend/app/services/ai_decision_service.py`

**Responsabilités**:
- Appeler OpenAI Moderation API
- Évaluer la sévérité du contenu flaggé
- Appliquer les règles custom utilisateur
- Logger toutes les décisions en DB

**Méthodes clés**:
```python
check_message(message_text: str) -> Tuple[AIDecision, float, str, str]
_check_openai_moderation(text: str) -> Dict[str, Any]
_assess_severity(categories: Dict[str, bool]) -> str
log_decision(...) -> Optional[Dict[str, Any]]
```

#### EmailEscalationService
**Fichier**: `/workspace/backend/app/services/email_escalation_service.py`

**Responsabilités**:
- Générer des emails d'escalation via LLM (GPT-4o-mini)
- Envoyer des emails via SMTP
- Logger tous les emails dans la DB
- Gérer les fallbacks (template statique si LLM échoue)

**Méthodes clés**:
```python
generate_escalation_email(message_text, reason, context) -> Dict[str, str]
send_escalation_email(to_email, subject, body, user_id, ...) -> bool
get_escalation_history(user_id, limit) -> list
```

---

## OpenAI Moderation API

### Spécifications

- **Modèle**: `omni-moderation-latest` (2025)
- **Coût**: GRATUIT
- **Latence**: ~50ms
- **Précision**: 95% accuracy
- **Langues**: 40+ langues supportées

### Catégories détectées

| Catégorie | Description | Sévérité |
|-----------|-------------|----------|
| `violence` | Contenu violent | HIGH |
| `violence/graphic` | Violence graphique | HIGH |
| `self-harm` | Auto-mutilation | HIGH |
| `self-harm/intent` | Intention de se nuire | HIGH |
| `self-harm/instructions` | Instructions d'auto-mutilation | HIGH |
| `harassment/threatening` | Harcèlement menaçant | HIGH |
| `hate` | Discours de haine | LOW |
| `sexual` | Contenu sexuel | LOW |
| `harassment` | Harcèlement | LOW |
| `illicit` | Contenu illicite | LOW |

### Sévérité

**HIGH (ESCALATE + Email)**:
- Violence physique
- Auto-mutilation
- Menaces directes

**LOW (IGNORE seulement)**:
- Discours de haine
- Harcèlement non menaçant
- Contenu sexuel

### Fail-safe

Si OpenAI Moderation API est down ou retourne une erreur:
- **Action**: Fail open (ne pas bloquer)
- **Fallback**: Continuer avec custom rules uniquement
- **Log**: Erreur loggée avec `[MODERATION]` tag

---

## Email Escalation

### Flow

1. Message flaggé avec severity HIGH
2. Récupérer email de l'utilisateur (DB ou auth.users)
3. Générer email via LLM:
   - Prompt personnalisé avec contexte complet
   - Format JSON: `{"subject": "...", "body": "..."}`
   - Model: GPT-4o-mini (économique et rapide)
4. Envoyer email:
   - Dev mode: Log seulement (SMTP disabled)
   - Prod mode: Envoi SMTP réel
5. Logger dans DB (table `escalation_emails`)

### Template LLM Prompt

```
Tu es un assistant qui génère des emails d'escalation pour une équipe support.

Contexte:
- Un message a été automatiquement flaggé par notre système de modération
- Raison: {reason}
- Message: "{message_text}"
- Plateforme: {platform}
- Auteur: {author}
- Conversation ID: {conversation_id}

Génère un email professionnel en français qui:
1. Alerte l'équipe support de manière claire et urgente
2. Explique précisément pourquoi le message a été flaggé
3. Fournit tout le contexte nécessaire pour agir
4. Suggère une action concrète à prendre

Ton de voix: Professionnel mais direct, sans dramatiser inutilement.
```

### Fallback Template

Si LLM échoue, utiliser template statique:
```
Sujet: ⚠️ Message flaggé: {reason}

Bonjour,

Un message a été automatiquement flaggé par notre système de modération.

🚨 RAISON: {reason}
📝 CONTENU: {message_text}
📊 CONTEXTE:
- Plateforme: {platform}
- Auteur: {author}
- Conversation ID: {conversation_id}

⚡ ACTION REQUISE:
Veuillez vérifier ce message et répondre manuellement si nécessaire.

Cordialement,
SocialSync AI - Système d'escalation automatique
```

---

## Database Schema

### Table: escalation_emails

```sql
CREATE TABLE escalation_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    message_id UUID,
    decision_id UUID REFERENCES ai_decisions(id),

    -- Email content
    email_to TEXT NOT NULL,
    email_subject TEXT NOT NULL,
    email_body TEXT NOT NULL,

    -- Tracking
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT CHECK (status IN ('sent', 'failed', 'pending')),
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_escalation_emails_user` - Requêtes par utilisateur
- `idx_escalation_emails_decision` - Traçabilité avec ai_decisions
- `idx_escalation_emails_message` - Lien avec messages
- `idx_escalation_emails_status` - Monitoring failed emails

**RLS**:
- Users can view own escalation_emails
- Service role can insert/update (workers)

---

## Integration dans batch_scanner.py

### Code snippet

```python
# Check AI Rules (incluant moderation)
decision, confidence, reason, matched_rule = ai_decision_service.check_message(message_text)

# Log décision
decision_log = ai_decision_service.log_decision(...)
decision_id = decision_log.get("id")

# Handle escalation
if decision == AIDecision.ESCALATE:
    # Get user email
    user_email = get_user_email(user_id)

    # Generate escalation email
    email_service = EmailEscalationService(db=db)
    email_data = await email_service.generate_escalation_email(
        message_text=message_text,
        reason=reason,
        context={"platform": platform, "author": contact_id, ...}
    )

    # Send email
    await email_service.send_escalation_email(
        to_email=user_email,
        subject=email_data["subject"],
        body=email_data["body"],
        user_id=user_id,
        message_id=message_id,
        decision_id=decision_id
    )

    # Do NOT auto-respond
    return
```

---

## Configuration

### Variables d'environnement

```bash
# OpenAI Moderation
OPENAI_MODERATION_ENABLED=true  # Activer/désactiver moderation API
OPENAI_API_KEY=sk-...  # Même clé que RAG agent

# Email Escalation
ESCALATION_FROM_EMAIL=noreply@socialsyncai.com
ESCALATION_SMTP_ENABLED=false  # true pour envoi réel
ESCALATION_SMTP_HOST=smtp.gmail.com
ESCALATION_SMTP_PORT=587
ESCALATION_SMTP_USER=your-email@gmail.com
ESCALATION_SMTP_PASSWORD=your-app-password
```

### Dev vs Prod

**Dev Mode** (recommandé pour développement):
```bash
OPENAI_MODERATION_ENABLED=true
ESCALATION_SMTP_ENABLED=false  # Emails loggés, pas envoyés
```

**Production**:
```bash
OPENAI_MODERATION_ENABLED=true
ESCALATION_SMTP_ENABLED=true  # Emails réellement envoyés
ESCALATION_SMTP_USER=...
ESCALATION_SMTP_PASSWORD=...
```

---

## Monitoring & Logs

### Log Tags

- `[MODERATION]` - Calls OpenAI Moderation API
- `[ESCALATION]` - Email escalation process
- `[ESCALATION_EMAIL]` - Email sending details
- `[AI_DECISION]` - Décisions AI logged
- `[SMTP]` - SMTP operations

### Métriques à surveiller

1. **Taux de moderation**:
   ```sql
   SELECT
       decision,
       COUNT(*) as count,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
   FROM ai_decisions
   WHERE matched_rule LIKE 'openai_moderation%'
   GROUP BY decision;
   ```

2. **Distribution severity**:
   ```sql
   SELECT
       matched_rule,
       COUNT(*) as count
   FROM ai_decisions
   WHERE matched_rule IN ('openai_moderation_high', 'openai_moderation_low')
   GROUP BY matched_rule;
   ```

3. **Email delivery status**:
   ```sql
   SELECT
       status,
       COUNT(*) as count
   FROM escalation_emails
   GROUP BY status;
   ```

4. **Failed emails**:
   ```sql
   SELECT *
   FROM escalation_emails
   WHERE status = 'failed'
   ORDER BY created_at DESC
   LIMIT 20;
   ```

---

## Performance

### Latence ajoutée

- OpenAI Moderation API: ~50ms par message
- Email generation (LLM): 1-2s (async, ne bloque pas)
- Email SMTP: 200-500ms (async, ne bloque pas)

**Total impact sur batch processing**: +50ms seulement (moderation check)

### Coûts

- Moderation API: **GRATUIT** ($0.00)
- Email LLM (GPT-4o-mini): ~$0.0001 par email
- SMTP: Selon provider (Gmail gratuit pour petit volume)

**Estimation mensuelle** (1000 messages, 10 escalations):
- Moderation: $0.00
- Email generation: $0.001
- **Total**: < $0.01/mois

---

## Testing

### Tests disponibles

**Fichier**: `/workspace/backend/tests/test_ai_rules_moderation.py`

**Coverage**: 20+ tests

**Catégories**:
1. OpenAI Moderation API calls
2. Severity assessment
3. Decision flow with moderation
4. Email generation (LLM + fallback)
5. Email sending (dev + SMTP)
6. E2E scenarios
7. Priority order validation

### Run tests

```bash
cd backend
pytest tests/test_ai_rules_moderation.py -v
```

---

## Troubleshooting

### Moderation API errors

**Symptôme**: Logs `[MODERATION] OpenAI Moderation API error`

**Cause**: API down ou clé invalide

**Solution**:
1. Vérifier `OPENAI_API_KEY` valide
2. Tester connexion: `curl https://api.openai.com/v1/moderations -H "Authorization: Bearer $OPENAI_API_KEY"`
3. Si problème persiste, système continue avec custom rules (fail open)

### Emails not sent

**Symptôme**: `status='failed'` dans escalation_emails

**Cause**: SMTP config incorrecte

**Solution**:
1. Vérifier `ESCALATION_SMTP_USER` et `ESCALATION_SMTP_PASSWORD`
2. Tester SMTP: `telnet smtp.gmail.com 587`
3. Si Gmail: activer "App Passwords" dans compte Google
4. Check `error_message` dans DB pour détails

### False positives

**Symptôme**: Messages normaux flaggés par moderation

**Solution**:
1. Vérifier logs `[MODERATION]` pour voir catégories détectées
2. Ajuster severity thresholds si nécessaire
3. Utiliser custom rules pour whitelist patterns spécifiques

---

## Évolutions futures

### Court terme
1. Dashboard UI pour voir escalations
2. Retry automatique pour failed emails
3. Support Slack/Discord notifications

### Long terme
1. Custom severity thresholds par utilisateur
2. Email templates personnalisables
3. Auto-learn from false positives
4. Multi-language email generation

---

**Implémenté**: 2025-10-18
**Status**: Production-ready ✅
