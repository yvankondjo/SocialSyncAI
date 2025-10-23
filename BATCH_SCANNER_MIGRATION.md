# Batch Scanner Migration - Redis/Asyncio → Celery Worker

**Date:** 2025-10-20
**Status:** ✅ COMPLETED (100% Celery)
**Version:** 2.0

---

## 📋 Overview

Migration du système de batch scanning pour les DMs/conversations de WhatsApp et Instagram.

**AVANT (Legacy) - SUPPRIMÉ:**
- Asyncio loop dans le process FastAPI
- Single point of failure (si FastAPI crash → plus de DMs traités)
- Couplage fort avec FastAPI

**APRÈS (Architecture finale):**
- ✅ Celery worker distributed (robuste, scalable)
- ✅ Celery Beat schedule (toutes les 0.5s)
- ✅ Architecture cohérente avec le système de comments
- ✅ Plus de code legacy - 100% Celery

---

## 🔧 Changements Implémentés

### 1. Nouvelle Task Celery

**Fichier:** `backend/app/workers/ingest.py`

```python
@celery.task(bind=True, name="app.workers.ingest.scan_redis_batches")
def scan_redis_batches_task(self):
    """
    Scan Redis for due message batches and process them.
    Runs every 0.5s via Celery Beat.
    """
    from app.services.batch_scanner import batch_scanner
    asyncio.run(batch_scanner._process_due_conversations())
```

### 2. Celery Beat Schedule

**Fichier:** `backend/app/workers/celery_app.py`

```python
celery.conf.beat_schedule = {
    "scan-redis-batches-every-500ms": {
        "task": "app.workers.ingest.scan_redis_batches",
        "schedule": 0.5,  # Every 500ms
        "options": {
            "expires": 0.4,  # Avoid overlap
        }
    },
    # ... autres schedules
}
```

### 3. FastAPI Lifespan Simplifié

**Fichier:** `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Batch scanning is now handled by Celery Beat worker
    logging.info("✅ DM/Chat batch scanning handled by Celery Beat (every 0.5s)")
    yield
    logging.info("🛑 FastAPI shutdown complete")
```

**Plus de scanner legacy** - FastAPI ne gère plus le batch scanning.

---

## 🧪 Test Production

### Démarrage Complet

**Commandes requises:**
```bash
# Terminal 1: Backend FastAPI
cd backend
uvicorn app.main:app --reload

# Terminal 2: Celery Worker (ingest queue - REQUIS pour DMs)
celery -A app.workers.celery_app worker -l info -Q ingest

# Terminal 3: Celery Beat (REQUIS pour batch scanning)
celery -A app.workers.celery_app beat -l info
```

**⚠️ IMPORTANT:** Sans Celery Beat, les DMs/chats ne seront PAS traités !

---

### Test Fonctionnel

**Objectif:** Vérifier que le système Celery fonctionne

**Test:**
1. Envoyer un message WhatsApp ou Instagram DM
2. Vérifier logs FastAPI : `"✅ DM/Chat batch scanning handled by Celery Beat"`
3. Vérifier logs Celery Beat : task `scan-redis-batches-every-500ms` scheduled
4. Vérifier logs Celery Worker : `"[BATCH_SCAN] Starting Redis batch scan"`
5. Vérifier que le message est traité dans les 2-3 secondes

**Critères de succès:**
- ✅ FastAPI démarre sans erreur
- ✅ Celery Beat schedule la task toutes les 0.5s
- ✅ Worker Celery traite les batches
- ✅ Réponse AI générée et envoyée dans les 3s
- ✅ Aucune erreur dans les logs

---

## 🔒 Mécanisme de Sécurité

Le code utilise un **lock Redis atomique** pour éviter les doublons :

**Fichier:** `app/services/message_batcher.py` ligne 147

```python
lock_key = f'{base_key}:lock'
lock_acquired = await redis_client.set(lock_key, 'processing', nx=True, ex=20)

if not lock_acquired:
    logger.info(f'Batch {base_key} already being processed')
    return None  # Autre scanner traite déjà ce batch
```

**Garanties:**
- ✅ Un seul scanner peut traiter un batch à la fois
- ✅ Lock expire après 20s (évite deadlock)
- ✅ Safe pour exécution parallèle

---

## 🚀 Migration Production

### Étape 1: Validation Staging

1. Tester Phase 2 (Legacy) → OK
2. Tester Phase 3 (Celery) → OK
3. Tester Phase 4 (Parallèle) → OK
4. Load test (optionnel mais recommandé)

### Étape 2: Déploiement Production

**Option A: Migration Immediate (Recommandé)**

```bash
# 1. Définir env var
export USE_CELERY_BATCH_SCANNER=true

# 2. Démarrer Celery Beat (AVANT de restart FastAPI)
celery -A app.workers.celery_app beat -d

# 3. Restart FastAPI
systemctl restart socialsyncai-api

# 4. Vérifier logs
journalctl -u socialsyncai-api -f | grep "CELERY batch scanner"
```

**Option B: Migration Progressive (Plus safe)**

```bash
# Jour 1: Dual-run (les deux actifs)
# USE_CELERY_BATCH_SCANNER=false
# Celery Beat running

# Jour 2: Monitor pour doublons (il ne devrait pas y en avoir)

# Jour 3: Basculer vers Celery uniquement
export USE_CELERY_BATCH_SCANNER=true
systemctl restart socialsyncai-api
```

### Étape 3: Cleanup Code (Après 1 semaine de stabilité)

1. Supprimer l'ancien code dans `batch_scanner.py`
2. Supprimer le flag `USE_CELERY_BATCH_SCANNER`
3. Simplifier `app/main.py` lifespan
4. Update documentation

---

## 📊 Monitoring

### Métriques à surveiller

**Avant migration (baseline):**
```bash
# Logs FastAPI
grep "conversations processed" backend/logs/*.log | tail -20
```

**Après migration:**
```bash
# Logs Celery Worker
grep "[BATCH_SCAN]" celery/logs/*.log | tail -20
```

**KPIs:**
- ⏱️ Temps de traitement moyen: < 5s
- ✅ Taux de succès: > 95%
- 📉 Erreurs: < 5%
- 🔄 Scans par minute: ~120 (0.5s interval)

### Commandes Debug

```bash
# Voir les tasks Celery actives
celery -A app.workers.celery_app inspect active

# Voir le schedule Beat
celery -A app.workers.celery_app inspect scheduled

# Stats du worker
celery -A app.workers.celery_app inspect stats
```

---

## ⚠️ Troubleshooting

### Problème: Celery Beat ne schedule pas la task

**Symptôme:** Logs Celery Beat vides, aucun `[BATCH_SCAN]` dans worker

**Solution:**
```bash
# Vérifier que ingest.py est importé
python -c "from app.workers import ingest; print('OK')"

# Vérifier le schedule Beat
celery -A app.workers.celery_app inspect scheduled

# Restart Beat
pkill -f "celery.*beat"
celery -A app.workers.celery_app beat -l info
```

---

### Problème: Messages non traités

**Symptôme:** Messages WhatsApp/Instagram DM non traités après 2s

**Diagnostic:**
```bash
# 1. Vérifier Redis
redis-cli
> KEYS conv:*
> ZRANGE conv:deadlines 0 -1 WITHSCORES

# 2. Vérifier mode actif
# Logs FastAPI: chercher "LEGACY" ou "CELERY"

# 3. Vérifier Celery worker
celery -A app.workers.celery_app inspect active
```

**Solutions:**
- Mode Legacy: Restart FastAPI
- Mode Celery: Restart Celery Beat + Worker

---

### Problème: Réponses dupliquées

**Symptôme:** Utilisateur reçoit 2 réponses identiques

**Cause:** Lock Redis non acquis (très rare)

**Solution:**
```bash
# Vérifier si les deux scanners sont actifs
ps aux | grep "batch_scanner"
ps aux | grep "celery.*beat"

# Choisir UN SEUL mode
export USE_CELERY_BATCH_SCANNER=true  # OU false
systemctl restart socialsyncai-api
```

---

## 📚 Documentation Associée

- `.agent/README.md` - Index général
- `.agent/System/CELERY_WORKERS.md` - Architecture Celery
- `.agent/Tasks/COMMENT_MONITORING_V2.md` - Architecture similaire (comments)

---

## ✅ Checklist de Migration

**Pre-Migration:**
- [ ] Lire cette documentation
- [ ] Tests Phase 2 (Legacy) passés
- [ ] Tests Phase 3 (Celery) passés
- [ ] Tests Phase 4 (Parallèle) passés
- [ ] Load test (optionnel)

**Migration:**
- [ ] Backup BDD
- [ ] Export métriques baseline
- [ ] Set `USE_CELERY_BATCH_SCANNER=true`
- [ ] Démarrer Celery Beat
- [ ] Restart FastAPI
- [ ] Vérifier logs (pas d'erreurs)

**Post-Migration (Jour 1-7):**
- [ ] Monitor erreurs (< 5%)
- [ ] Monitor temps de réponse (< 5s)
- [ ] Vérifier aucun doublon
- [ ] Comparer métriques vs baseline

**Cleanup (Après 1 semaine):**
- [ ] Supprimer ancien code scanner
- [ ] Supprimer flag config
- [ ] Update docs
- [ ] Archiver cette migration doc

---

**Status:** ✅ READY FOR TESTING
**Next Step:** Execute Phase 2 (Test Mode Legacy)

---

*Dernière mise à jour: 2025-10-20*
