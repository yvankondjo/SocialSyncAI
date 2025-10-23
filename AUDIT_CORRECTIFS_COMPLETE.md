# Rapport d'Audit & Correctifs - SocialSync AI

**Date:** 2025-10-20
**Status:** ✅ TOUS LES CORRECTIFS APPLIQUÉS
**Version:** 1.0

---

## 📋 Résumé Exécutif

Audit complet de la codebase et correction de 4 incohérences architecturales identifiées.

**Incohérences corrigées:**
1. ✅ Architecture DMs vs Comments (Batch Scanner → Celery)
2. ✅ API Versions hardcodées (v23.0 → META_GRAPH_VERSION)
3. ✅ Retours services inconsistants (HTTPException → RuntimeError)
4. ✅ HMAC Webhooks désactivé (Sécurité critique)

---

## 🔧 Correctif 1/4: Migration Batch Scanner → Celery

### Problème Identifié

**Incohérence architecturale:**
- DMs/Chats: Batch scanner asyncio dans process FastAPI (single point of failure)
- Comments: Celery workers + Beat (distributed, robuste)

**Impact:**
- Si FastAPI crash → DMs plus traités
- Architecture non cohérente

### Solution Appliquée

✅ **Migration 100% Celery**

**Fichiers modifiés:**
- `backend/app/workers/ingest.py` - Nouvelle task `scan_redis_batches`
- `backend/app/workers/celery_app.py` - Schedule Celery Beat (0.5s)
- `backend/app/main.py` - Suppression du lifespan batch scanner
- `backend/app/core/config.py` - Suppression flag USE_CELERY_BATCH_SCANNER

**Nouvelle architecture:**
```python
# Celery Beat schedule
celery.conf.beat_schedule = {
    "scan-redis-batches-every-500ms": {
        "task": "app.workers.ingest.scan_redis_batches",
        "schedule": 0.5,  # Every 500ms
    },
}
```

**Avantages:**
- ✅ Robustesse: Si FastAPI crash, Celery continue
- ✅ Scalabilité: Multiple workers possibles
- ✅ Cohérence: Même pattern que comments
- ✅ Monitoring: Celery Flower/inspect

**Documentation:** Voir `BATCH_SCANNER_MIGRATION.md`

---

## 🔧 Correctif 2/4: API Versions Hardcodées

### Problème Identifié

**Incohérence de configuration:**
- Config globale: `META_GRAPH_VERSION = v24.0`
- WhatsApp Service: Hardcoded `v23.0`
- Instagram Service: Hardcoded `v23.0`
- Response Manager: Hardcoded `v23.0`
- Social Auth Service: ✅ Utilise config (OK)

**Impact:**
- Version drift selon les services
- Comportements API différents
- Difficulté de migration de version

### Solution Appliquée

✅ **Uniformisation avec META_GRAPH_VERSION**

**Fichiers modifiés:**

1. **backend/app/services/whatsapp_service.py** (ligne 32)
```python
# AVANT
self.api_url = "https://graph.facebook.com/v23.0"

# APRÈS
graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
self.api_url = f"https://graph.facebook.com/{graph_version}"
```

2. **backend/app/services/instagram_service.py** (ligne 24)
```python
# AVANT
self.api_url = 'https://graph.instagram.com/v23.0'

# APRÈS
graph_version = os.getenv('META_GRAPH_VERSION', 'v24.0')
self.api_url = f'https://graph.instagram.com/{graph_version}'
```

3. **backend/app/services/response_manager.py** (ligne 540)
```python
# AVANT
url = f'https://graph.facebook.com/v23.0/{media_id}'

# APRÈS
graph_version = os.getenv('META_GRAPH_VERSION', 'v24.0')
url = f'https://graph.facebook.com/{graph_version}/{media_id}'
```

**Avantages:**
- ✅ Configuration centralisée
- ✅ Migration de version simplifiée (1 seul endroit)
- ✅ Cohérence garantie entre services

---

## 🔧 Correctif 3/4: Retours Services Inconsistants

### Problème Identifié

**Pattern anti-pattern:**
- Services lèvent `HTTPException` (responsabilité des routers)
- Mix de patterns: RuntimeError, HTTPException, `{'success': False}`

**Impact:**
- Couplage fort avec FastAPI
- Services non réutilisables hors contexte HTTP
- Code difficile à tester

### Solution Appliquée

✅ **Services lèvent RuntimeError, routers gèrent HTTPException**

**Fichiers modifiés:**

**backend/app/services/instagram_service.py** (3 endroits)

1. Ligne 130:
```python
# AVANT
raise HTTPException(status_code=500, detail=f'Erreur conversations: {str(e)}')

# APRÈS
raise RuntimeError(f'Erreur conversations: {str(e)}')
```

2. Ligne 160:
```python
# AVANT
raise HTTPException(status_code=502, detail=f'Échec Instagram: {e.response.text}')

# APRÈS
raise RuntimeError(f'Échec Instagram: {e.response.text}')
```

3. Ligne 168:
```python
# AVANT
raise HTTPException(status_code=504, detail='Timeout Instagram')

# APRÈS
raise RuntimeError('Timeout Instagram')
```

**Pattern recommandé:**
```python
# Dans un service
def my_service_function():
    if error:
        raise RuntimeError("Description de l'erreur")
    return {'success': True, 'data': result}

# Dans un router
@router.get("/endpoint")
async def my_endpoint():
    try:
        result = my_service_function()
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Avantages:**
- ✅ Séparation des responsabilités
- ✅ Services testables indépendamment
- ✅ Réutilisabilité (CLI, workers, tests)

---

## 🔧 Correctif 4/4: HMAC Webhooks Désactivé 🔴 CRITIQUE

### Problème Identifié

**Faille de sécurité critique:**
- Validation HMAC commentée dans WhatsApp webhooks
- Validation HMAC commentée dans Instagram webhooks
- Risque d'injection de données malveillantes

**Impact:**
- ⚠️ **CRITIQUE**: Webhooks non authentifiés
- Attaquant peut envoyer des faux messages
- Injection de données dans la BDD

### Solution Appliquée

✅ **HMAC Validation réactivée**

**Fichiers modifiés:**

1. **backend/app/routers/whatsapp.py** (ligne 146-149)
```python
# AVANT
# TODO: Réactiver la vérification HMAC lorsque la configuration Meta sera stabilisée
# if not verify_webhook_signature(payload, signature, webhook_secret):
#     logger.warning("Signature webhook invalide")
#     raise HTTPException(status_code=403, detail="Signature invalide")

# APRÈS
# HMAC validation for security (re-enabled 2025-10-20)
if not verify_webhook_signature(payload, signature, webhook_secret):
    logger.warning("Signature webhook invalide - vérifiez META_APP_SECRET")
    raise HTTPException(status_code=403, detail="Signature invalide")
```

2. **backend/app/routers/instagram.py** (ligne 186-189)
```python
# AVANT
# TODO: Réactiver la vérification HMAC lorsque la configuration Meta sera stabilisée
# if not verify_instagram_webhook_signature(payload, signature, webhook_secret):
#     logger.warning("Invalid Instagram webhook signature")
#     raise HTTPException(status_code=403, detail="Invalid signature")

# APRÈS
# HMAC validation for security (re-enabled 2025-10-20)
if not verify_instagram_webhook_signature(payload, signature, webhook_secret):
    logger.warning("Invalid Instagram webhook signature - check META_APP_SECRET in Meta for Developers")
    raise HTTPException(status_code=403, detail="Invalid signature")
```

**⚠️ IMPORTANT - Configuration requise:**

Vérifier que `META_APP_SECRET` est configuré dans `.env`:
```bash
META_APP_SECRET=your_meta_app_secret_from_developers_console
```

**Test de validation:**
```bash
# Tester avec Meta webhook test tool
# https://developers.facebook.com/tools/webhooks/

# Vérifier logs
grep "Signature webhook" backend/logs/*.log
```

**Avantages:**
- ✅ Sécurité: Webhooks authentifiés
- ✅ Protection contre injections
- ✅ Conformité best practices Meta

---

## 📊 Récapitulatif des Modifications

### Fichiers Modifiés (9 fichiers)

**Workers & Config:**
- ✅ `backend/app/workers/ingest.py` - Nouvelle task scan_redis_batches
- ✅ `backend/app/workers/celery_app.py` - Schedule Beat 0.5s
- ✅ `backend/app/core/config.py` - Suppression flag legacy
- ✅ `backend/app/main.py` - Lifespan simplifié

**Services:**
- ✅ `backend/app/services/whatsapp_service.py` - API version dynamique
- ✅ `backend/app/services/instagram_service.py` - API version + RuntimeError
- ✅ `backend/app/services/response_manager.py` - API version dynamique

**Routers:**
- ✅ `backend/app/routers/whatsapp.py` - HMAC activé
- ✅ `backend/app/routers/instagram.py` - HMAC activé

### Lignes Modifiées

- **Total:** ~50 lignes modifiées
- **Ajouts:** ~15 lignes (commentaires + nouvelle task)
- **Suppressions:** ~35 lignes (code legacy + flags)

---

## 🧪 Tests Requis

### Test 1: Batch Scanner Celery

```bash
# Démarrer tous les services
# Terminal 1
uvicorn app.main:app --reload

# Terminal 2
celery -A app.workers.celery_app worker -l info -Q ingest

# Terminal 3
celery -A app.workers.celery_app beat -l info

# Test
# Envoyer un DM WhatsApp/Instagram
# Vérifier réponse AI dans les 3s
```

**Critères de succès:**
- ✅ FastAPI log: "DM/Chat batch scanning handled by Celery Beat"
- ✅ Celery Beat schedule visible: `scan-redis-batches-every-500ms`
- ✅ Worker traite les batches
- ✅ Réponse AI générée

---

### Test 2: API Versions

```bash
# Vérifier les logs de connexion
grep "graph.facebook.com" backend/logs/*.log | grep "v24.0"

# Doit afficher v24.0 partout (plus de v23.0)
```

**Critères de succès:**
- ✅ Tous les appels API utilisent v24.0
- ✅ Pas de v23.0 hardcodé dans les logs

---

### Test 3: HMAC Webhooks

```bash
# Tester avec curl (signature invalide)
curl -X POST http://localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=INVALID" \
  -d '{"entry":[]}'

# Doit retourner 403 Forbidden
```

**Critères de succès:**
- ✅ Webhook avec signature invalide → 403
- ✅ Log: "Signature webhook invalide"
- ✅ Meta webhook test tool → 200 OK

---

## ⚠️ Points d'Attention Production

### 1. Celery Beat REQUIS

Sans Celery Beat, les DMs/chats ne seront PAS traités !

```bash
# Production: Démarrer Beat en daemon
celery -A app.workers.celery_app beat -d --pidfile=/var/run/celery/beat.pid
```

---

### 2. META_APP_SECRET Obligatoire

Vérifier que `META_APP_SECRET` est configuré, sinon webhooks rejetés.

```bash
# Vérifier
echo $META_APP_SECRET

# Si vide → Configurer
export META_APP_SECRET=your_secret_here
```

---

### 3. Migration API Version

Si en production avec v23.0, tester v24.0 en staging d'abord.

```bash
# Staging
META_GRAPH_VERSION=v24.0

# Production (après validation)
META_GRAPH_VERSION=v24.0
```

---

## 📈 Métriques de Succès

**Avant correctifs:**
- ❌ DMs: Single point of failure
- ❌ API Versions: Drift entre services
- ❌ Services: HTTPException (couplage)
- ❌ Webhooks: Non sécurisés

**Après correctifs:**
- ✅ DMs: Architecture distribuée robuste
- ✅ API Versions: Centralisée, cohérente
- ✅ Services: RuntimeError (découplage)
- ✅ Webhooks: HMAC activé (sécurité)

---

## 🎯 Prochaines Étapes (Optionnel)

### Amélioration Continue

1. **Monitoring Celery** (Recommandé)
   - Installer Celery Flower: `pip install flower`
   - Démarrer: `celery -A app.workers.celery_app flower`
   - Accès: `http://localhost:5555`

2. **Tests Automatisés** (À considérer)
   - Tests unitaires services (sans HTTPException)
   - Tests intégration webhooks HMAC
   - Tests E2E batch scanner Celery

3. **Alerting Production** (Recommandé)
   - Sentry pour erreurs
   - Prometheus pour métriques Celery
   - Logs centralisés (ELK/CloudWatch)

---

## ✅ Checklist de Déploiement

**Pre-Déploiement:**
- [ ] Lire ce rapport
- [ ] Tests Phase 1, 2, 3 passés
- [ ] `META_APP_SECRET` configuré
- [ ] `META_GRAPH_VERSION` défini (v24.0)

**Déploiement:**
- [ ] Backup BDD
- [ ] Deploy code
- [ ] Démarrer Celery Beat
- [ ] Restart FastAPI
- [ ] Restart Celery Workers

**Post-Déploiement (Jour 1):**
- [ ] Vérifier logs (pas d'erreurs)
- [ ] Tester DM WhatsApp → Réponse AI OK
- [ ] Tester DM Instagram → Réponse AI OK
- [ ] Vérifier webhook signature logs (pas de 403)
- [ ] Monitor Celery Beat (schedule actif)

**Post-Déploiement (Semaine 1):**
- [ ] Monitoring erreurs < 5%
- [ ] Temps de réponse DMs < 5s
- [ ] Aucun webhook rejeté (si META_APP_SECRET OK)
- [ ] Aucune régression fonctionnelle

---

## 📚 Documentation Associée

- `BATCH_SCANNER_MIGRATION.md` - Guide détaillé migration Celery
- `.agent/README.md` - Index documentation projet
- `.agent/System/CELERY_WORKERS.md` - Architecture Celery
- `.agent/Tasks/COMMENT_MONITORING_V2.md` - Pattern similaire (comments)

---

**Status:** ✅ TOUS LES CORRECTIFS APPLIQUÉS
**Prêt pour:** Tests & Déploiement

---

*Dernière mise à jour: 2025-10-20*
*Audit réalisé par: Claude Code*
