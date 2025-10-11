#!/usr/bin/env python3
"""
Script de test pour la fonctionnalité d'escalade

Utilisation :
cd backend
python test_escalation.py

Assurez-vous que les variables d'environnement sont configurées dans .env
"""

import asyncio
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from app.services.escalation import Escalation
from app.services.link_service import LinkService
from app.services.email_service import EmailService


async def test_escalation_flow():
    """Test complet du flux d'escalade"""

    print("🧪 Test du système d'escalade vers un humain")
    print("=" * 50)

    # Vérifier les variables d'environnement
    required_env_vars = [
        "RESEND_API_KEY",
        "JWT_SECRET_KEY",
        "FRONTEND_URL"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("Configurez votre fichier .env selon ESCALATION_SETUP.md")
        return

    print("✅ Variables d'environnement configurées")

    # IDs de test (à adapter selon votre base de données)
    test_user_id = "user_test_id"  # Remplacez par un vrai user_id
    test_conversation_id = "conv_test_id"  # Remplacez par une vraie conversation_id

    try:
        # 1. Test du service de liens
        print("\n🔗 Test du service de liens...")
        link_service = LinkService()
        test_link = link_service.generate_conversation_link(
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        print(f"✅ Lien généré: {test_link[:50]}...")

        # 2. Test du service email (sans envoi réel)
        print("\n📧 Test du service email...")
        email_service = EmailService()

        # Simuler les données d'escalade
        test_escalation_data = {
            "id": "test_escalation_123",
            "conversation_id": test_conversation_id,
            "user_id": test_user_id,
            "user_email": "test@example.com",  # Email de test
            "message": "Je ne comprends pas cette réponse technique",
            "confidence": 85.5,
            "reason": "Question technique complexe nécessitant expertise humaine"
        }

        # Tester le rendu du template (sans envoi)
        html_content = email_service._render_escalation_template(
            test_escalation_data,
            test_link
        )
        print(f"✅ Template rendu ({len(html_content)} caractères)")

        # 3. Test du service d'escalade (commenté pour éviter les envois réels)
        print("\n🚨 Test du service d'escalade...")
        print("⚠️  Service d'escalade non testé automatiquement pour éviter les envois d'emails")
        print("   Utilisez l'endpoint de test: POST /support/escalations/test")

        # Instructions pour le test manuel
        print("\n📋 Instructions pour tester manuellement:")
        print("1. Assurez-vous d'avoir un utilisateur et une conversation dans la base")
        print("2. Appelez l'endpoint de test:")
        print("   POST /support/escalations/test")
        print(f"   Body: {{'conversation_id': '{test_conversation_id}'}}")
        print("3. Vérifiez que l'escalade est créée en base")
        print("4. Vérifiez les logs pour les erreurs")

        print("\n🎉 Tests terminés avec succès!")

    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_escalation_flow())
