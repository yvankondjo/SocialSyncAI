#!/usr/bin/env python3
"""
Script pour mettre à jour les prix Stripe existants avec la période d'essai de 7 jours.
"""

import os
import sys
import logging
import stripe
from typing import Dict, Any

# Ajouter le chemin du backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import get_db
from app.core.config import get_settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_stripe_client():
    """Initialise le client Stripe."""
    settings = get_settings()
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY non configuré")
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe

def update_stripe_prices_with_trial():
    """Met à jour les prix Stripe existants pour ajouter la période d'essai."""
    logger.info("🔄 Mise à jour des prix Stripe avec période d'essai...")
    
    db = get_db()
    stripe = get_stripe_client()
    
    # Récupérer les prix Stripe existants sans période d'essai
    result = db.table('prices').select('id, product_id, unit_amount').is_('trial_period_days', 'null').execute()
    
    updated_count = 0
    
    for price in result.data:
        price_id = price['id']
        product_id = price['product_id']
        unit_amount = price['unit_amount']
        
        logger.info(f"   Mise à jour prix: {price_id} (Produit: {product_id})")
        
        try:
            # Mettre à jour le prix Stripe pour ajouter la période d'essai
            updated_price = stripe.Price.modify(
                price_id,
                recurring={
                    'trial_period_days': 7
                }
            )
            
            # Mettre à jour la base de données
            db.table('prices').update({
                'trial_period_days': 7
            }).eq('id', price_id).execute()
            
            logger.info(f"   ✅ Prix mis à jour: {price_id} - Période d'essai: 7 jours")
            updated_count += 1
            
        except stripe.error.StripeError as e:
            logger.error(f"   ❌ Erreur Stripe pour {price_id}: {e}")
        except Exception as e:
            logger.error(f"   ❌ Erreur générale pour {price_id}: {e}")
    
    logger.info(f"✅ Mise à jour terminée: {updated_count} prix mis à jour")
    return updated_count

def main():
    """Fonction principale."""
    try:
        updated_count = update_stripe_prices_with_trial()
        
        if updated_count > 0:
            logger.info("🎯 Prochaines étapes:")
            logger.info("   1. Vérifier les prix dans le dashboard Stripe")
            logger.info("   2. Tester la création d'un abonnement avec période d'essai")
            logger.info("   3. Vérifier que les webhooks fonctionnent correctement")
        else:
            logger.info("ℹ️  Aucun prix à mettre à jour")
            
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
