import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.db.session import get_db
from datetime import datetime, timedelta

def subscribe_test_user():
    """Subscribe the test user to Pro plan"""
    db = get_db()
    if not db:
        print('❌ Supabase credentials missing')
        return

    user_id = 'b46a7229-2c29-4a88-ada1-c21a59f4eda1'
    plan_name = 'Pro'

    try:
        # 1. Récupérer le plan Pro
        plan_result = db.table('subscription_plans').select('*').eq('name', plan_name).eq('is_active', True).single().execute()
        
        if not plan_result.data:
            print(f"❌ Plan '{plan_name}' non trouvé")
            return
        
        plan = plan_result.data
        print(f"📋 Plan trouvé: {plan['name']} - {plan['price_eur']} EUR - {plan['credits_included']} crédits")
        
        # 2. Vérifier si l'utilisateur a déjà une souscription
        existing = db.table('user_subscriptions').select('*').eq('user_id', user_id).execute()
        
        if existing.data:
            print(f"⚠️  L'utilisateur a déjà une souscription:")
            sub = existing.data[0]
            print(f"   Plan: {sub.get('plan_id')}")
            print(f"   Crédits restants: {sub.get('credits_balance')}")
            print(f"   Statut: {sub.get('subscription_status')}")
            
            # Mettre à jour la souscription existante
            update_data = {
                'plan_id': plan['id'],
                'subscription_status': 'trialing',
                'credits_balance': plan['credits_included'],
                'trial_end': (datetime.utcnow() + timedelta(days=plan['trial_duration_days'])).isoformat(),
                'current_period_start': datetime.utcnow().isoformat(),
                'current_period_end': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = db.table('user_subscriptions').update(update_data).eq('user_id', user_id).execute()
            print(f"✅ Souscription mise à jour!")
            
        else:
            # Créer une nouvelle souscription
            subscription_data = {
                'user_id': user_id,
                'plan_id': plan['id'],
                'subscription_status': 'trialing',
                'credits_balance': plan['credits_included'],
                'trial_end': (datetime.utcnow() + timedelta(days=plan['trial_duration_days'])).isoformat(),
                'current_period_start': datetime.utcnow().isoformat(),
                'current_period_end': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            }
            
            result = db.table('user_subscriptions').insert(subscription_data).execute()
            print(f"✅ Nouvelle souscription créée!")
        
        # 3. Vérifier la souscription finale
        final = db.table('user_subscriptions').select('*').eq('user_id', user_id).single().execute()
        
        if final.data:
            print(f"\n📊 Souscription finale:")
            print(f"   User ID: {user_id}")
            print(f"   Plan: {plan['name']}")
            print(f"   Prix: {plan['price_eur']} EUR")
            print(f"   Crédits: {final.data['credits_balance']}")
            print(f"   Statut: {final.data['subscription_status']}")
            print(f"   Trial jusqu'à: {final.data.get('trial_end', 'N/A')}")
            print(f"   Support images: {plan.get('features', {}).get('images', False)}")
            print(f"   Support audio: {plan.get('features', {}).get('audio', False)}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    subscribe_test_user()
