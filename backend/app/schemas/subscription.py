"""
Schemas de base pour les fonctionnalités d'abonnement - VERSION OPEN-SOURCE
"""
from pydantic import BaseModel
from typing import Optional


class StorageUsage(BaseModel):
    """Modèle pour l'utilisation du stockage"""
    used_mb: float = 0.0
    quota_mb: float = float('inf')  # Illimité en open-source
    percentage: float = 0.0


class StorageQuotaExceededError(Exception):
    """
    Exception levée quand le quota de stockage est dépassé.

    NOTE: En version open-source, cette exception ne devrait jamais être levée
    car le stockage est illimité.
    """
    pass
