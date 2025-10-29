#!/usr/bin/env python3
"""
Script de seed pour créer des utilisateurs de test
Version open-source - Crédits illimités
"""
import os
import sys
from datetime import datetime, timezone
from supabase import create_client, Client

# Configuration Supabase (à remplir avec vos valeurs)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")

# Utilisateurs de test à créer
TEST_USERS = [
    {
        "email": "demo@socialsync.ai",
        "password": "Demo123456!",
        "full_name": "Demo User",
        "username": "demo_user"
    },
    {
        "email": "test@socialsync.ai",
        "password": "Test123456!",
        "full_name": "Test User",
        "username": "test_user"
    }
]


def create_supabase_client() -> Client:
    """Créé un client Supabase avec la clé de service (admin)"""
    if SUPABASE_URL == "https://your-project.supabase.co":
        print("❌ Erreur: Veuillez configurer SUPABASE_URL")
        print("   Export SUPABASE_URL=https://your-project.supabase.co")
        sys.exit(1)

    if SUPABASE_SERVICE_KEY == "your-service-role-key":
        print("❌ Erreur: Veuillez configurer SUPABASE_SERVICE_ROLE_KEY")
        print("   Export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        sys.exit(1)

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def create_user(supabase: Client, user_data: dict) -> str:
    """
    Créé un utilisateur dans Supabase Auth

    Returns:
        user_id (str): L'ID de l'utilisateur créé
    """
    try:
        # Créer l'utilisateur avec Supabase Auth Admin API
        result = supabase.auth.admin.create_user({
            "email": user_data["email"],
            "password": user_data["password"],
            "email_confirm": True,  # Confirmer l'email automatiquement
            "user_metadata": {
                "full_name": user_data["full_name"],
                "username": user_data["username"]
            }
        })

        user_id = result.user.id
        print(f"✅ Utilisateur créé: {user_data['email']} (ID: {user_id})")
        return user_id

    except Exception as e:
        # Si l'utilisateur existe déjà, on récupère son ID
        if "already registered" in str(e).lower() or "duplicate" in str(e).lower():
            print(f"⚠️  Utilisateur existe déjà: {user_data['email']}")
            # Récupérer l'ID de l'utilisateur existant
            users = supabase.auth.admin.list_users()
            for user in users:
                if user.email == user_data["email"]:
                    return user.id
        else:
            print(f"❌ Erreur création utilisateur {user_data['email']}: {e}")
            return None


def ensure_user_credits(supabase: Client, user_id: str):
    """
    S'assure qu'un enregistrement user_credits existe pour l'utilisateur
    Mode open-source: crédits illimités (999999)
    """
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Vérifier si l'enregistrement existe
        result = supabase.table('user_credits').select('*').eq('user_id', user_id).execute()

        if not result.data:
            # Créer l'enregistrement
            supabase.table('user_credits').insert({
                'user_id': user_id,
                'credits_balance': 999999,  # Illimité (symbolique)
                'storage_used_mb': 0,
                'created_at': now,
                'updated_at': now
            }).execute()
            print(f"   ✅ Crédits créés (illimités)")
        else:
            print(f"   ℹ️  Crédits existent déjà")

    except Exception as e:
        print(f"   ❌ Erreur création crédits: {e}")


def main():
    """Fonction principale de seeding"""
    print("=" * 70)
    print("  SOCIALSYNC AI - SEED USERS (Open-Source)")
    print("=" * 70)
    print()

    # Créer le client Supabase
    print("📡 Connexion à Supabase...")
    supabase = create_supabase_client()
    print("✅ Connecté à Supabase")
    print()

    # Créer les utilisateurs de test
    print("👤 Création des utilisateurs de test...")
    print()

    created_users = []
    for user_data in TEST_USERS:
        user_id = create_user(supabase, user_data)
        if user_id:
            ensure_user_credits(supabase, user_id)
            created_users.append({
                "email": user_data["email"],
                "password": user_data["password"],
                "user_id": user_id
            })
        print()

    # Résumé
    print("=" * 70)
    print("  RÉSUMÉ")
    print("=" * 70)
    print(f"✅ {len(created_users)} utilisateur(s) créé(s)/vérifié(s)")
    print()
    print("📝 Credentials de connexion:")
    print()
    for user in created_users:
        print(f"  • Email: {user['email']}")
        print(f"    Password: {user['password']}")
        print(f"    User ID: {user['user_id']}")
        print()

    print("💡 Prochaines étapes:")
    print("  1. Utilisez ces credentials pour vous connecter")
    print("  2. Créez des comptes sociaux avec: python scripts/seed_social_accounts.py")
    print("  3. Testez l'application sur le dashboard")
    print()


if __name__ == "__main__":
    main()
