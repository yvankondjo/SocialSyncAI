import logging
from typing import Optional, Dict, Any
from datetime import datetime

from supabase import Client
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CreditsService:
    """
    Service de gestion des crédits - VERSION OPEN-SOURCE

    MODE ILLIMITÉ : Cette version ne limite pas l'utilisation.
    Tous les utilisateurs ont des crédits illimités.
    """

    def __init__(self, db: Client, redis_client=None):
        self.db = db
        self.redis = redis_client

    async def check_credits_available(
        self,
        user_id: str,
        cost: float,
        operation: str = "unknown"
    ) -> bool:
        """
        Vérifie si l'utilisateur a suffisamment de crédits.

        VERSION OPEN-SOURCE: Retourne toujours True (crédits illimités)

        Args:
            user_id: ID de l'utilisateur
            cost: Coût estimé de l'opération
            operation: Description de l'opération

        Returns:
            True (toujours - mode illimité)
        """
        logger.info(f"[OPEN-SOURCE] Credits check for user {user_id}: {cost} credits for {operation} - UNLIMITED MODE")
        return True

    async def deduct_credits(
        self,
        user_id: str,
        amount: float = None,
        operation: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        credits_to_deduct: float = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Déduit des crédits du compte utilisateur.

        VERSION OPEN-SOURCE: Ne fait rien, retourne simplement un résultat simulé.

        Args:
            user_id: ID de l'utilisateur
            amount: Montant de crédits à déduire (deprecated, use credits_to_deduct)
            operation: Description de l'opération (deprecated, use reason)
            metadata: Métadonnées additionnelles
            credits_to_deduct: Montant de crédits à déduire (preferred)
            reason: Description de l'opération (preferred)

        Returns:
            Dict simulant une transaction réussie
        """
        # Handle both old and new parameter names for backward compatibility
        deduct_amount = credits_to_deduct if credits_to_deduct is not None else amount
        operation_desc = reason if reason is not None else operation

        logger.info(f"[OPEN-SOURCE] Credits deduction for user {user_id}: {deduct_amount} credits for {operation_desc} - NO DEDUCTION (unlimited mode)")

        return {
            "success": True,
            "user_id": user_id,
            "amount": deduct_amount,
            "operation": operation_desc,
            "remaining_balance": float('inf'),  # Infini
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "unlimited"
        }

    async def get_credits_balance(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère le solde de crédits d'un utilisateur.

        VERSION OPEN-SOURCE: Retourne toujours un solde illimité.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dict avec le solde (toujours illimité)
        """
        logger.info(f"[OPEN-SOURCE] Getting credits balance for user {user_id} - UNLIMITED")

        return {
            "user_id": user_id,
            "balance": float('inf'),
            "used_this_month": 0,
            "mode": "unlimited",
            "plan": "open-source",
            "last_updated": datetime.utcnow().isoformat()
        }

    async def get_feature_access(self, user_id: str) -> Dict[str, Any]:
        """
        Vérifie si l'utilisateur a accès aux fonctionnalités.

        VERSION OPEN-SOURCE: Tous les utilisateurs ont accès à toutes les fonctionnalités.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dict avec toutes les fonctionnalités activées (mode illimité)
        """
        logger.info(f"[OPEN-SOURCE] Feature access check for user {user_id} - ALL FEATURES GRANTED (unlimited mode)")

        # Return an object with all features enabled
        class UnlimitedFeatures:
            def __init__(self):
                self.images = True
                self.audio = True
                self.video = True
                self.ai_responses = True
                self.scheduled_posts = True
                self.analytics = True
                self.unlimited = True
                # Unlimited calls per batch for open-source version
                self.max_calls_per_batch = 999999

        return UnlimitedFeatures()

    async def ensure_user_credits_exist(self, user_id: str) -> Dict[str, Any]:
        """
        S'assure qu'un enregistrement de crédits existe pour l'utilisateur.

        VERSION OPEN-SOURCE: Créé ou met à jour l'enregistrement si nécessaire.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dict avec les informations de crédits
        """
        try:
            # Vérifier si l'utilisateur existe
            result = self.db.table('user_credits').select('*').eq('user_id', user_id).execute()

            if not result.data:
                # Créer un enregistrement avec crédits illimités
                now = datetime.utcnow().isoformat()
                new_credits = {
                    'user_id': user_id,
                    'credits_balance': 999999,  # Symbolique (on check pas vraiment)
                    'storage_used_mb': 0,
                    'created_at': now,
                    'updated_at': now
                }

                insert_result = self.db.table('user_credits').insert(new_credits).execute()
                logger.info(f"[OPEN-SOURCE] Created credits record for user {user_id} with unlimited access")

                return insert_result.data[0] if insert_result.data else new_credits

            return result.data[0]

        except Exception as e:
            logger.error(f"[OPEN-SOURCE] Error ensuring credits exist for user {user_id}: {e}")
            # En cas d'erreur, on retourne quand même un dict pour ne pas bloquer
            return {
                'user_id': user_id,
                'credits_balance': 999999,
                'mode': 'unlimited'
            }

    async def can_use_model(self, user_id: str, model_name: str) -> bool:
        """
        Vérifie si l'utilisateur peut utiliser un modèle AI spécifique.

        VERSION OPEN-SOURCE: Retourne toujours True (tous les modèles disponibles).

        Args:
            user_id: ID de l'utilisateur
            model_name: Nom du modèle AI

        Returns:
            True (toujours - mode illimité)
        """
        logger.info(f"[OPEN-SOURCE] Model access check for user {user_id} - model {model_name} - GRANTED (unlimited mode)")
        return True

    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'utilisation d'un utilisateur.

        VERSION OPEN-SOURCE: Retourne des stats minimales.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dict avec les statistiques d'utilisation
        """
        return {
            "user_id": user_id,
            "total_operations": 0,
            "total_cost": 0,
            "current_balance": float('inf'),
            "mode": "unlimited",
            "message": "Open-source version - unlimited usage"
        }
