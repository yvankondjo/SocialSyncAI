# 🚀 **Redis Message Batching - Guide Complet**

## 📋 **Vue d'Ensemble**

Système de batching intelligent pour éviter les réponses multiples aux messages rapides sur WhatsApp/Instagram.

**Flux :**
1. **Message reçu** → **BDD immédiate** (idempotent)
2. **Message ajouté** → **Redis batch** (fenêtre 30s)
3. **Scanner traite** → **Réponse unique** après silence

---

## 🔧 **Installation & Configuration**

### **1. Pré-requis**
```bash
# Redis doit être disponible
docker-compose up redis -d

# Ou installer Redis localement
sudo apt install redis-server
```

### **2. Variables d'Environnement**
```bash
# Dans votre .env
REDIS_URL=redis://redis:6379/0

# Configuration optionnelle
BATCH_WINDOW_SECONDS=30     # Fenêtre d'attente
CACHE_TTL_HOURS=1           # TTL du cache conversation
HISTORY_LIMIT=200           # Messages max en historique
SCANNER_INTERVAL=0.5        # Fréquence scan (500ms)
```

### **3. Migration BDD**
```sql
-- Ajouter idempotence et traçabilité
ALTER TABLE conversation_messages 
ADD CONSTRAINT unique_external_message_id UNIQUE (external_message_id);

ALTER TABLE conversation_messages 
ADD COLUMN webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN webhook_payload JSONB DEFAULT '{}';
```

---

## 🏗️ **Architecture**

### **Composants**

1. **MessageBatcher** (`app/services/message_batcher.py`)
   - Gestion cache Redis
   - Fenêtre glissante
   - Hydratation BDD → Redis

2. **BatchScanner** (`app/services/batch_scanner.py`)
   - Scanner toutes les 500ms
   - Traitement batches dus
   - Envoi réponses intelligentes

3. **Integration Webhook** (`app/routers/whatsapp.py`)
   - BDD first (idempotent)
   - Redis second (batching)
   - Pas de réponse immédiate

### **Clés Redis**

```redis
# Par conversation
conv:whatsapp:{phone_number_id}:{wa_id}:history    # Cache messages (TTL 1h)
conv:whatsapp:{phone_number_id}:{wa_id}:msgs       # Batch en cours (TTL 1h)
conv:whatsapp:{phone_number_id}:{wa_id}:deadline   # Timestamp deadline (TTL 1h)
conv:whatsapp:{phone_number_id}:{wa_id}:lock       # Lock distribué (TTL 20s)

# Global
conv:deadlines                                     # ZSET agenda global
```

---

## 🔄 **Flux Détaillé**

### **1. Premier Message (Cache Miss)**
```
Webhook → BDD INSERT → Redis hydratation (SELECT derniers 200)
       → Cache :history + :msgs + :deadline (now+30s)
       → ZADD conv:deadlines
```

### **2. Messages Suivants (Cache Hit)**
```
Webhook → BDD INSERT (idempotent) → Redis append :history + :msgs
       → :deadline = now+30s (fenêtre repoussée)
       → ZADD conv:deadlines (update score)
```

### **3. Scanner Processing**
```
Toutes les 500ms → ZRANGEBYSCORE conv:deadlines ≤ now
                → SETNX :lock → LRANGE + DEL :msgs
                → Générer réponse IA → Envoyer via API
                → ZREM conv:deadlines → DEL :lock
```

---

## 🧪 **Test Manuel**

### **1. Vérifier Redis**
```bash
redis-cli ping
# PONG

redis-cli -u redis://redis:6379/0 ping
# PONG
```

### **2. Test Webhook**
```bash
# Envoyer 3 messages rapides via WhatsApp
# Vérifier logs :
curl localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{...webhook_payload...}'

# Logs attendus :
# ✅ Message xxx sauvegardé en BDD
# 📝 Message ajouté au batch existant
# (30s plus tard)
# ⚡ Réponse envoyée pour whatsapp:xxx:xxx
```

### **3. Monitoring Redis**
```bash
# Vérifier les clés
redis-cli keys "conv:*"

# Vérifier l'agenda
redis-cli zrange conv:deadlines 0 -1 withscores

# Vérifier un batch
redis-cli llen "conv:whatsapp:123:456:msgs"
```

---

## 📊 **Monitoring & Logs**

### **Logs Importants**
- `✅ Message xxx sauvegardé en BDD` → BDD OK
- `🆕 Nouvelle session de conversation` → Cache hydraté
- `📝 Message ajouté au batch existant` → Fenêtre repoussée
- `⚡ Réponse envoyée pour xxx` → Batch traité
- `❌ Erreur Redis batching` → Redis down mais BDD OK

### **Métriques à Surveiller**
```python
# Dans votre monitoring
redis_client.zcard("conv:deadlines")     # Nombre conversations en attente
redis_client.dbsize()                    # Taille totale Redis
redis_client.memory_usage("conv:xxx")    # Mémoire par conversation
```

---

## 🐛 **Troubleshooting**

### **Redis Inaccessible**
```
❌ Erreur Redis batching (message toujours sauvé en BDD)
✅ Graceful degradation : messages sauvés, pas de batching
```

### **Doublons Webhooks**
```
🔄 Message xxx déjà traité (idempotent)
✅ Contrainte UNIQUE empêche les doublons
```

### **Scanner Bloqué**
```bash
# Vérifier les locks
redis-cli keys "*:lock"

# Nettoyer manuellement si besoin
redis-cli del "conv:whatsapp:123:456:lock"
```

### **Mémoire Redis Haute**
```bash
# Vérifier TTL
redis-cli ttl "conv:whatsapp:123:456:history"

# Force cleanup
redis-cli eval "return redis.call('del', unpack(redis.call('keys', 'conv:*')))" 0
```

---

## 🔒 **Sécurité & Performance**

### **Limitations**
- **TTL automatique** : 1h max par conversation
- **Bornes historique** : 200 messages max
- **Lock timeout** : 20s max processing
- **Scan fréquence** : 500ms (ajustable)

### **Scalabilité**
- **Single server** : In-memory OK jusqu'à ~10K conversations/h
- **Multi-server** : Redis partagé + locks distribués
- **High volume** : Considérer Redis Cluster

---

## 📈 **Évolutions Futures**

1. **IA Avancée** : Intégration OpenAI/Claude pour réponses contextuelles
2. **Multi-plateforme** : Étendre à Instagram, Telegram, etc.
3. **Analytics** : Métriques de performance des batches
4. **Admin UI** : Interface pour monitorer/gérer les batches

---

## ✅ **Checklist Déploiement**

- [ ] Redis accessible (`REDIS_URL` configuré)
- [ ] Migration BDD appliquée (`unique_external_message_id`)
- [ ] Variables d'environnement définies
- [ ] Scanner démarré avec l'app (`lifespan` activé)
- [ ] Webhooks configurés dans Meta for Developers
- [ ] Tests manuels validés (3 messages → 1 réponse)
- [ ] Monitoring en place (logs + Redis métriques)

**🎯 Système prêt pour la production !**
