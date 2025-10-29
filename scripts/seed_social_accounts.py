#!/usr/bin/env python3
"""
Script de seed pour créer des comptes sociaux de test
Version open-source - Données fictives pour testing
"""
import os
import sys
from datetime import datetime, timezone
from supabase import create_client, Client

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")

# Comptes sociaux de test
TEST_SOCIAL_ACCOUNTS = [
    {
        "platform": "instagram",
        "platform_user_id": "17841400000000001",  # ID fictif
        "username": "demo_instagram",
        "display_name": "Demo Instagram Account",
        "profile_picture_url": "https://via.placeholder.com/150",
        "access_token": "FAKE_IG_TOKEN_FOR_TESTING_DO_NOT_USE_IN_PRODUCTION",
        "is_active": True
    },
    {
        "platform": "whatsapp",
        "platform_user_id": "102200000000001",  # ID fictif
        "username": "+1234567890",
        "display_name": "Demo WhatsApp Business",
        "profile_picture_url": "https://via.placeholder.com/150",
        "access_token": "FAKE_WA_TOKEN_FOR_TESTING_DO_NOT_USE_IN_PRODUCTION",
        "is_active": True
    }
]


def create_supabase_client() -> Client:
    """Créé un client Supabase avec la clé de service"""
    if SUPABASE_URL == "https://your-project.supabase.co":
        print("❌ Erreur: Veuillez configurer SUPABASE_URL")
        sys.exit(1)

    if SUPABASE_SERVICE_KEY == "your-service-role-key":
        print("❌ Erreur: Veuillez configurer SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_user_id_from_email(supabase: Client, email: str) -> str:
    """Récupère le user_id depuis l'email"""
    try:
        users = supabase.auth.admin.list_users()
        for user in users:
            if user.email == email:
                return user.id
        print(f"❌ Utilisateur non trouvé: {email}")
        return None
    except Exception as e:
        print(f"❌ Erreur récupération user: {e}")
        return None


def create_social_account(supabase: Client, user_id: str, account_data: dict):
    """Créé un compte social dans la base de données"""
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Vérifier si le compte existe déjà
        result = supabase.table('social_accounts').select('*').eq(
            'user_id', user_id
        ).eq('platform', account_data['platform']).execute()

        if result.data:
            print(f"   ⚠️  Compte {account_data['platform']} existe déjà")
            return result.data[0]['id']

        # Créer le compte social
        insert_data = {
            'user_id': user_id,
            'platform': account_data['platform'],
            'platform_user_id': account_data['platform_user_id'],
            'username': account_data['username'],
            'display_name': account_data['display_name'],
            'profile_picture_url': account_data['profile_picture_url'],
            'access_token': account_data['access_token'],
            'is_active': account_data['is_active'],
            'created_at': now,
            'updated_at': now,
            'token_expires_at': None,  # Pas d'expiration pour les tokens de test
            'metadata': {
                'is_test_account': True,
                'created_by_seed_script': True
            }
        }

        result = supabase.table('social_accounts').insert(insert_data).execute()
        account_id = result.data[0]['id']
        print(f"   ✅ Compte {account_data['platform']} créé (ID: {account_id})")
        return account_id

    except Exception as e:
        print(f"   ❌ Erreur création compte {account_data['platform']}: {e}")
        return None


def main():
    """Fonction principale"""
    print("=" * 70)
    print("  SOCIALSYNC AI - SEED SOCIAL ACCOUNTS (Open-Source)")
    print("=" * 70)
    print()

    # Demander l'email de l'utilisateur
    user_email = input("📧 Email de l'utilisateur (demo@socialsync.ai): ").strip()
    if not user_email:
        user_email = "demo@socialsync.ai"

    print()
    print("📡 Connexion à Supabase...")
    supabase = create_supabase_client()
    print("✅ Connecté à Supabase")
    print()

    # Récupérer le user_id
    print(f"🔍 Recherche de l'utilisateur: {user_email}")
    user_id = get_user_id_from_email(supabase, user_email)
    if not user_id:
        print()
        print("❌ Utilisateur non trouvé. Veuillez d'abord exécuter:")
        print("   python scripts/seed_users.py")
        sys.exit(1)

    print(f"✅ Utilisateur trouvé (ID: {user_id})")
    print()

    # Créer les comptes sociaux
    print("📱 Création des comptes sociaux...")
    print()

    created_accounts = []
    for account_data in TEST_SOCIAL_ACCOUNTS:
        print(f"Création compte {account_data['platform'].upper()}...")
        account_id = create_social_account(supabase, user_id, account_data)
        if account_id:
            created_accounts.append({
                "platform": account_data['platform'],
                "username": account_data['username'],
                "id": account_id
            })
        print()

    # Résumé
    print("=" * 70)
    print("  RÉSUMÉ")
    print("=" * 70)
    print(f"✅ {len(created_accounts)} compte(s) social créé(s)")
    print()
    print("📱 Comptes créés:")
    for account in created_accounts:
        print(f"  • {account['platform'].upper()}: {account['username']}")
    print()

    print("⚠️  IMPORTANT:")
    print("  Ces comptes utilisent des tokens FICTIFS et ne fonctionneront pas")
    print("  avec les vraies APIs (Instagram, WhatsApp).")
    print()
    print("  Pour utiliser de vrais comptes sociaux:")
    print("  1. Connectez-vous au dashboard")
    print("  2. Allez dans Paramètres > Comptes Sociaux")
    print("  3. Connectez vos vrais comptes Instagram/WhatsApp")
    print()

    print("💡 Prochaines étapes:")
    print("  1. Lancez l'application: docker-compose up")
    print("  2. Ouvrez le dashboard: http://localhost:3000")
    print("  3. Connectez-vous avec les credentials de seed_users.py")
    print()


if __name__ == "__main__":
    main()
