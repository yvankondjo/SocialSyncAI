"""
Test RAG Agent Escalation avec Vraies Conversations

Ce script teste l'outil d'escalation du RAGAgent en appelant directement
le service avec des messages forçant l'escalation.
"""

import os
import sys
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.rag_agent import RAGAgent
from app.db.session import get_db

supabase = get_db()

# IDs de test
TEST_USER_ID = "b46a7229-2c29-4a88-ada1-c21a59f4eda1"
TEST_CONVERSATION_ID = "6ea38a38-e128-46e6-bde2-4a3aae1e890e"
TEST_SOCIAL_ACCOUNT_ID = "fe923251-da7e-4116-a71f-6297c74dc6a8"


async def test_rag_escalation():
    """Teste l'escalation du RAGAgent avec un message forçant l'escalation"""

    print("\n" + "="*80)
    print("TEST ESCALATION RAG AGENT AVEC VRAIES DONNÉES")
    print("="*80 + "\n")

    # Messages forçant l'escalation
    escalation_messages = [
        "I NEED TO SPEAK WITH A HUMAN RIGHT NOW! This is urgent! AI cannot help me with this. I explicitly request to be escalated to a human agent immediately.",
        "Connect me to a real person NOW! I've been trying to resolve this for hours and your AI is useless. I demand human assistance!",
        "This is a legal matter that requires human judgment. Please escalate this conversation to your support team immediately.",
    ]

    for idx, message in enumerate(escalation_messages, 1):
        # Créer RAGAgent pour cette conversation
        rag_agent = RAGAgent(
            user_id=TEST_USER_ID,
            conversation_id=TEST_CONVERSATION_ID
        )
        print(f"\n{'='*80}")
        print(f"TEST #{idx}: Escalation Message")
        print(f"{'='*80}\n")

        print(f"📝 Message: {message[:100]}...\n")

        try:
            # Insérer le message dans la DB
            message_data = {
                "conversation_id": TEST_CONVERSATION_ID,
                "external_message_id": f"TEST_ESC_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                "direction": "inbound",
                "content": message,
                "status": "sent",
                "message_type": "text"
            }

            msg_result = supabase.table("conversation_messages").insert(message_data).execute()

            if not msg_result.data:
                print(f"❌ Échec insertion message")
                continue

            message_id = msg_result.data[0]["id"]
            print(f"✅ Message inséré: {message_id[:8]}...\n")

            # Vérifier état AVANT
            conv_before = supabase.table("conversations")\
                .select("ai_mode")\
                .eq("id", TEST_CONVERSATION_ID)\
                .execute()

            print(f"📊 État AVANT:")
            print(f"   - ai_mode: {conv_before.data[0]['ai_mode']}")

            escalations_before = supabase.table("support_escalations")\
                .select("*")\
                .eq("conversation_id", TEST_CONVERSATION_ID)\
                .execute()

            print(f"   - Escalations: {len(escalations_before.data)}\n")

            # Appeler RAGAgent
            print("🤖 Appel RAGAgent.generate_response()...\n")

            response = await rag_agent.generate_response(
                user_id=TEST_USER_ID,
                message_text=message,
                conversation_id=TEST_CONVERSATION_ID,
                customer_name="Urgent Escalation Test User",
                platform="instagram"
            )

            print(f"📝 Réponse RAG: {response[:200]}...\n")

            # Vérifier état APRÈS
            print("🔍 Vérification état APRÈS:\n")

            conv_after = supabase.table("conversations")\
                .select("ai_mode")\
                .eq("id", TEST_CONVERSATION_ID)\
                .execute()

            ai_mode_after = conv_after.data[0]['ai_mode']
            print(f"   - ai_mode: {ai_mode_after}")

            escalations_after = supabase.table("support_escalations")\
                .select("*")\
                .eq("conversation_id", TEST_CONVERSATION_ID)\
                .execute()

            escalation_count = len(escalations_after.data)
            print(f"   - Escalations: {escalation_count}")

            if escalation_count > len(escalations_before.data):
                latest_escalation = escalations_after.data[-1]
                print(f"\n   ✅ NOUVELLE ESCALATION CRÉÉE:")
                print(f"      - ID: {latest_escalation['id'][:8]}...")
                print(f"      - Reason: {latest_escalation.get('reason', 'N/A')[:80]}")
                print(f"      - Status: {latest_escalation.get('status', 'N/A')}")
                print(f"      - Created: {latest_escalation.get('created_at', 'N/A')}")

            # Résultat du test
            escalation_created = escalation_count > len(escalations_before.data)
            ai_mode_disabled = ai_mode_after == "OFF"

            print(f"\n📊 RÉSULTAT TEST #{idx}:")
            print(f"   - Escalation créée: {'✅ OUI' if escalation_created else '❌ NON'}")
            print(f"   - AI mode désactivé: {'✅ OUI' if ai_mode_disabled else '❌ NON'}")

            if escalation_created and ai_mode_disabled:
                print(f"\n   🎉 TEST #{idx} RÉUSSI!")
            else:
                print(f"\n   ⚠️  TEST #{idx} ÉCHOUÉ")
                print(f"      RAGAgent n'a pas détecté le besoin d'escalation")

            # Réinitialiser pour test suivant
            if escalation_created:
                print(f"\n🔄 Réinitialisation ai_mode pour test suivant...")
                supabase.table("conversations")\
                    .update({"ai_mode": "ON"})\
                    .eq("id", TEST_CONVERSATION_ID)\
                    .execute()

        except Exception as e:
            print(f"\n❌ ERREUR: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("FIN DES TESTS ESCALATION")
    print("="*80)

    # Résumé final
    print("\n📊 RÉSUMÉ FINAL:\n")

    escalations_final = supabase.table("support_escalations")\
        .select("*")\
        .eq("conversation_id", TEST_CONVERSATION_ID)\
        .execute()

    print(f"Total escalations créées: {len(escalations_final.data)}")

    for esc in escalations_final.data:
        print(f"\n  - Escalation {esc['id'][:8]}...")
        print(f"    Reason: {esc.get('reason', 'N/A')[:100]}")
        print(f"    Status: {esc.get('status', 'N/A')}")
        print(f"    Created: {esc.get('created_at', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_rag_escalation())
