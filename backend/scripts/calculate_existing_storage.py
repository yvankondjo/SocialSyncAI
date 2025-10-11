#!/usr/bin/env python3
"""
Script pour calculer l'usage de stockage existant des utilisateurs.
Parcourt tous les utilisateurs et calcule la taille totale de leurs documents et FAQ.
Met à jour la colonne storage_used_mb dans user_subscriptions.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from app.services.credits_service import get_credits_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_user_storage_usage():
    """Calcule l'usage de stockage pour tous les utilisateurs existants."""
    db = get_db()

    try:
        # Récupérer tous les utilisateurs avec leurs abonnements
        subscriptions = db.table('user_subscriptions').select('user_id, storage_used_mb').execute()
        logger.info(f"Trouvé {len(subscriptions.data)} abonnements à traiter")

        total_updated = 0

        for subscription in subscriptions.data:
            user_id = subscription['user_id']
            current_used_mb = subscription.get('storage_used_mb', 0) or 0

            # Calculer la taille des documents
            docs_size_bytes = 0
            docs = db.table('knowledge_documents').select('file_size_bytes').eq('user_id', user_id).execute()
            for doc in docs.data:
                docs_size_bytes += doc.get('file_size_bytes', 0) or 0

            # Calculer la taille des FAQ
            faqs_size_bytes = 0
            faqs = db.table('faq_qa').select('text_size_bytes').eq('user_id', user_id).execute()
            for faq in faqs.data:
                faqs_size_bytes += faq.get('text_size_bytes', 0) or 0

            # Convertir en MB
            total_size_mb = (docs_size_bytes + faqs_size_bytes) / (1024 * 1024)

            # Mettre à jour si différent
            if abs(total_size_mb - current_used_mb) > 0.001:  # Tolérance de 1KB
                db.table('user_subscriptions').update({
                    'storage_used_mb': round(total_size_mb, 2)
                }).eq('user_id', user_id).execute()

                logger.info(f"Utilisateur {user_id}: {current_used_mb:.2f}MB -> {total_size_mb:.2f}MB")
                total_updated += 1
            else:
                logger.debug(f"Utilisateur {user_id}: déjà à jour ({total_size_mb:.2f}MB)")

        logger.info(f"Calcul terminé. {total_updated} utilisateurs mis à jour.")

    except Exception as e:
        logger.error(f"Erreur lors du calcul: {e}")
        raise
    finally:
        # Fermer la connexion si nécessaire
        pass

if __name__ == "__main__":
    logger.info("Début du calcul de l'usage de stockage existant...")
    calculate_user_storage_usage()
    logger.info("Calcul terminé avec succès.")


