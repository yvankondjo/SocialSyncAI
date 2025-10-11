# 🚀 Checklist Déploiement - Système Crédits Stripe

## Phase 1: Préparation Supabase (10 min)

### ✅ Créer la fonction SQL manquante

Dans Supabase Dashboard > SQL Editor :

```sql
-- Fonction resolve_plan_credits
CREATE OR REPLACE FUNCTION public.resolve_plan_credits(p_subscription_id text)
RETURNS integer
LANGUAGE sql
SET search_path = pg_temp
AS $$
  SELECT COALESCE(
    NULLIF((pr.metadata->>'credits_per_cycle')::int, NULL),
    NULLIF((pd.metadata->>'credits_per_cycle')::int, NULL),
    NULLIF((pd.metadata->>'credits_monthly')::int, NULL),
    1000
  ) AS plan_credits
  FROM public.subscriptions s
  LEFT JOIN public.prices pr ON pr.id = s.price_id
  LEFT JOIN public.products pd ON pd.id = pr.product_id
  WHERE s.id = p_subscription_id
  LIMIT 1;
$$;
```

### ✅ Vérifier métadonnées produits

Dans Supabase Dashboard > Table Editor > products :

Vérifier que tous les produits ont dans `metadata` :
```json
{
  "trial_credits": 100,
  "credits_per_cycle": 2000,
  "trial_duration_days": 7
}
```

## Phase 2: Tests Locaux (15 min)

### ✅ Test des fonctions SQL

```bash
cd /workspace/backend
python -c "
import asyncio, os
from dotenv import load_dotenv
from supabase import create_client
from app.services.stripe_service import StripeService

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

async def test():
    service = StripeService(supabase, None)
    
    # Test résolution crédits
    credits = await service._resolve_plan_credits('test_id')
    print(f'Résolution crédits: {credits}')
    
    # Test zéro crédits
    await service._zero_credits_on_cancel('test_sub')
    print('Purge crédits: OK')
    
    print('✅ Tests locaux réussis')

asyncio.run(test())
"
```

### ✅ Test webhook simulé

Créer un script de test webhook :

```python
# test_webhook.py
import asyncio, json, os
from dotenv import load_dotenv
from supabase import create_client
from app.services.stripe_service import StripeService

async def test_webhook():
    load_dotenv()
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
    service = StripeService(supabase, None)
    
    # Simuler webhook essai
    trial_event = {
        'type': 'customer.subscription.created',
        'id': 'evt_test_trial',
        'data': {
            'object': {
                'id': 'sub_test_trial',
                'status': 'trialing',
                'customer': 'cus_test',
                'metadata': {'user_id': 'user_test'},
                'trial_end': 1735689600,  # 2025-01-01
                'items': {'data': [{'price': {'id': 'price_test'}}]}
            }
        }
    }
    
    result = await service._process_webhook_event(trial_event)
    print(f'Webhook essai traité: {result}')

asyncio.run(test_webhook())
```

## Phase 3: Tests Stripe (20 min)

### ✅ Configuration Stripe Test

1. Dans Stripe Dashboard > Developers > Webhooks :
   - Créer webhook endpoint : `https://votredomaine.com/stripe/webhook`
   - Sélectionner événements :
     - `customer.subscription.created`
     - `invoice.payment_succeeded`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`

2. Copier le webhook secret dans `.env` :
```env
STRIPE_WEBHOOK_SECRET=whsec_...
```

### ✅ Test scénario complet

1. **Créer produit test** dans Stripe :
   - Nom: "Test Plan"
   - Prix: 9.99€/mois
   - Metadata produit: `{"trial_credits": 100, "credits_per_cycle": 2000}`

2. **Test checkout** :
   ```javascript
   // Frontend - créer session checkout
   const response = await fetch('/api/create-checkout-session', {
     method: 'POST',
     body: JSON.stringify({ price_id: 'price_test_id' })
   });
   const { checkout_url } = await response.json();
   window.location = checkout_url;
   ```

3. **Simuler paiement** dans Stripe Dashboard

4. **Vérifier** :
   - ✅ Crédits essai appliqués (100)
   - ✅ Transaction créée
   - ✅ Webhook traité sans doublon

## Phase 4: Validation Métier (10 min)

### ✅ Scénarios à tester

| Scénario | Attendu | Vérification |
|----------|---------|--------------|
| **Essai gratuit** | +100 crédits | `SELECT credits_balance FROM user_credits WHERE user_id = ?` |
| **Paiement réussi** | Reset à 2000 crédits | Vérifier après webhook `invoice.payment_succeeded` |
| **Annulation** | Balance = 0 | Vérifier après webhook `customer.subscription.deleted` |
| **Paiement échoué** | Balance inchangée | Vérifier après webhook `invoice.payment_failed` |

### ✅ Audit des transactions

```sql
-- Vérifier l'historique
SELECT 
  transaction_type, 
  credits_amount, 
  credits_balance_after, 
  reason, 
  created_at 
FROM credit_transactions 
WHERE user_id = ? 
ORDER BY created_at DESC;
```

## Phase 5: Déploiement Production (15 min)

### ✅ Migration données

Si utilisateurs existants :

```sql
-- Créer entrées user_credits pour utilisateurs existants
INSERT INTO user_credits (user_id, credits_balance, plan_credits)
SELECT 
  id as user_id,
  100 as credits_balance,  -- Crédits gratuits par défaut
  1000 as plan_credits
FROM auth.users 
WHERE id NOT IN (SELECT user_id FROM user_credits);
```

### ✅ Configuration production

1. **Variables d'environnement** :
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_live_...
FRONTEND_URL=https://votredomaine.com
```

2. **Webhooks Stripe** :
   - Supprimer webhooks test
   - Créer webhooks production
   - URL: `https://api.votredomaine.com/stripe/webhook`

3. **Monitoring** :
   - Logs Stripe pour webhooks
   - Alertes sur échecs paiement
   - Dashboard crédits utilisateurs

## Phase 6: Monitoring & Maintenance

### ✅ Métriques à surveiller

```sql
-- Crédits distribués ce mois
SELECT 
  SUM(credits_amount) as total_credits_granted,
  COUNT(*) as transactions_count
FROM credit_transactions 
WHERE transaction_type = 'trial_grant'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE);

-- Taux de conversion essai
SELECT 
  COUNT(CASE WHEN status = 'active' THEN 1 END) * 100.0 / COUNT(*) as conversion_rate
FROM subscriptions 
WHERE trial_end IS NOT NULL;
```

### ✅ Alertes à configurer

- Webhook failures > 5/min
- Crédits négatifs (impossible normalement)
- Transactions sans user_id
- Subscriptions sans crédits associés

---

## 📋 Checklist Déploiement

- [ ] Fonction `resolve_plan_credits` créée dans Supabase
- [ ] Métadonnées produits configurées (`trial_credits: 100`)
- [ ] Tests locaux réussis (fonctions SQL + webhooks simulés)
- [ ] Webhooks Stripe configurés (test mode)
- [ ] Scénario complet testé (essai → paiement → annulation)
- [ ] Audit transactions validé
- [ ] Variables production configurées
- [ ] Webhooks production actifs
- [ ] Monitoring configuré
- [ ] Tests post-déploiement effectués

**Temps total estimé : 1h30**
