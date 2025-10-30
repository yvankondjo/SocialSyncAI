"""
Test Final d'Escalation RAGAgent

Teste l'outil d'escalation en invoquant directement le graphe RAGAgent
avec des messages forçant l'escalation.
"""

import os
import sys
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from langchain_core.messages import HumanMessage
from app.services.rag_agent import RAGAgent
from app.db.session import get_db
from app.deps.runtime_prod import CHECKPOINTER_POSTGRES

supabase = get_db()

# IDs de test
TEST_USER_ID = "b46a7229-2c29-4a88-ada1-c21a59f4eda1"
TEST_CONVERSATION_ID = "6ea38a38-e128-46e6-bde2-4a3aae1e890e"


def test_escalation():
    """Teste l'escalation du RAGAgent"""

    print("\n" + "="*80)
    print("TEST FINAL ESCALATION RAG AGENT")
    print("="*80 + "\n")

    # Messages qui doivent forcer l'escalation
    escalation_messages = [
        "I URGENTLY NEED TO SPEAK WITH A HUMAN! AI cannot handle this. Please ESCALATE this to a real person NOW. I explicitly request human assistance immediately!",
        "This is getting ridiculous. I've been trying for hours and your bot is useless! CONNECT ME TO A HUMAN AGENT RIGHT NOW! I DEMAND to speak with someone who can actually help!",
        "Legal matter requiring human judgment. ESCALATE IMMEDIATELY. I need to discuss GDPR compliance with a real person. AI cannot handle this sensitive legal issue.",
    ]

    for idx, message_text in enumerate(escalation_messages, 1):
        print(f"\n{'='*80}")
        print(f"TEST #{idx}")
        print(f"{'='*80}\n")

        print(f"📝 Message:\n{message_text}\n")

        try:
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

            # Créer RAGAgent
            print("🤖 Création RAGAgent...")
            agent = RAGAgent(
                user_id=TEST_USER_ID,
                conversation_id=TEST_CONVERSATION_ID,
                system_prompt="You are a customer support assistant. If a customer explicitly requests human assistance or mentions urgent/legal/complex matters, you MUST call the escalation tool.",
                model_name="gpt-4o-mini",
                checkpointer=CHECKPOINTER_POSTGRES
            )

            # Créer message
            human_message = HumanMessage(content=message_text)

            # Invoquer le graphe (SYNCHRONE, pas async)
            print("🔄 Invocation agent.graph.invoke()...")

            response_data = agent.graph.invoke(
                {"messages": [human_message]},
                config={"configurable": {"thread_id": TEST_CONVERSATION_ID}}
            )

            # Extraire la réponse
            if response_data and "messages" in response_data:
                ai_messages = [
                    m for m in response_data["messages"]
                    if hasattr(m, "type") and m.type == "ai"
                ]

                if ai_messages:
                    response_text = ai_messages[-1].content
                    print(f"✅ Réponse RAG: {response_text[:150]}...\n")
                else:
                    print("⚠️  Aucun message AI dans la réponse\n")
            else:
                print("⚠️  Format de réponse invalide\n")

            # Vérifier état APRÈS
            print("🔍 Vérification état APRÈS:")

            conv_after = supabase.table("conversations")\
                .select("ai_mode")\
                .eq("id", TEST_CONVERSATION_ID)\
                .execute()

            ai_mode_after = conv_after.data[0]['ai_mode']
            print(f"   - ai_mode: {ai_mode_after}")

            escalations_after = supabase.table("support_escalations")\
                .select("*")\
                .eq("conversation_id", TEST_CONVERSATION_ID)\
                .order("created_at", desc=True)\
                .execute()

            escalation_count = len(escalations_after.data)
            print(f"   - Escalations: {escalation_count}")

            # Vérifier si nouvelle escalation
            escalation_created = escalation_count > len(escalations_before.data)

            if escalation_created:
                latest_escalation = escalations_after.data[0]
                print(f"\n   ✅ NOUVELLE ESCALATION CRÉÉE:")
                print(f"      - ID: {latest_escalation['id'][:8]}...")
                print(f"      - Reason: {latest_escalation.get('reason', 'N/A')[:100]}")
                print(f"      - Status: {latest_escalation.get('status', 'N/A')}")
                print(f"      - Created: {latest_escalation.get('created_at', 'N/A')}")

            # Résultat
            ai_mode_disabled = ai_mode_after == "OFF"

            print(f"\n📊 RÉSULTAT TEST #{idx}:")
            print(f"   - Escalation créée: {'✅ OUI' if escalation_created else '❌ NON'}")
            print(f"   - AI mode désactivé: {'✅ OUI' if ai_mode_disabled else '❌ NON'}")

            if escalation_created and ai_mode_disabled:
                print(f"\n   🎉 TEST #{idx} RÉUSSI!")
            elif escalation_created:
                print(f"\n   ⚠️  TEST #{idx} PARTIEL (escalation OK, mais ai_mode toujours ON)")
            else:
                print(f"\n   ❌ TEST #{idx} ÉCHOUÉ")
                print(f"      RAGAgent n'a pas appelé l'outil escalation")
                print(f"      Le message n'était probablement pas assez explicite")

            # Réinitialiser pour test suivant
            if escalation_created and ai_mode_disabled:
                print(f"\n🔄 Réinitialisation ai_mode pour test suivant...")
                supabase.table("conversations")\
                    .update({"ai_mode": "ON"})\
                    .eq("id", TEST_CONVERSATION_ID)\
                    .execute()

        except Exception as e:
            print(f"\n❌ ERREUR: {str(e)}")
            import traceback
            traceback.print_exc()

    # Résumé final
    print("\n" + "="*80)
    print("RÉSUMÉ FINAL")
    print("="*80 + "\n")

    escalations_final = supabase.table("support_escalations")\
        .select("*")\
        .eq("conversation_id", TEST_CONVERSATION_ID)\
        .order("created_at", desc=True)\
        .execute()

    print(f"📊 Total escalations créées: {len(escalations_final.data)}\n")

    if escalations_final.data:
        print("Détails des escalations:\n")
        for esc in escalations_final.data:
            print(f"  - ID: {esc['id'][:8]}...")
            print(f"    Reason: {esc.get('reason', 'N/A')[:100]}")
            print(f"    Status: {esc.get('status', 'N/A')}")
            print(f"    Created: {esc.get('created_at', 'N/A')}\n")
    else:
        print("⚠️  Aucune escalation créée")
        print("L'outil d'escalation n'a pas été appelé par le RAGAgent")
        print("\nPossibles raisons:")
        print("  - Le system prompt n'est pas assez clair")
        print("  - L'outil escalation n'est pas bien configuré")
        print("  - Le RAGAgent ne détecte pas les demandes d'escalation")

    print("\n" + "="*80)


if __name__ == "__main__":
    test_escalation()
