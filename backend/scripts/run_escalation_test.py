"""Utility script to trigger escalation flows for manual verification.

Usage examples:

    # Service only
    python scripts/run_escalation_test.py --user-email yvankondjo8@gmail.com \
        --message "Escalade de test" --reason "Validation manuelle" --mode service

    # Tool (IA) only
    python scripts/run_escalation_test.py --user-email yvankondjo8@gmail.com \
        --mode tool

Environment requirements:
- RESEND_API_KEY, FROM_EMAIL, SUPPORT_EMAIL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- Optionally FRONTEND_URL, JWT_SECRET_KEY for link generation
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Force email configuration for this test
os.environ["SUPPORT_EMAIL"] = "yvankondjo8@gmail.com"
os.environ["FROM_EMAIL"] = "onboarding@resend.dev"

from app.db.session import get_db  # noqa: E402  (after load_dotenv)
from app.services.escalation import Escalation  # noqa: E402
from app.services.rag_agent import create_escalation_tool  # noqa: E402


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trigger escalation flow manually")
    parser.add_argument("--user-email", required=True, help="Email de l'utilisateur cible")
    parser.add_argument(
        "--conversation-id",
        help="Conversation spécifique à escalader. Si non fourni, la première conversation de l'utilisateur sera utilisée.",
    )
    parser.add_argument("--message", default="Escalade déclenchée manuellement")
    parser.add_argument("--reason", default="Validation du flux d'escalade")
    parser.add_argument("--confidence", type=float, default=80.0)
    parser.add_argument(
        "--mode",
        choices=["service", "tool", "both"],
        default="both",
        help="Choisir la voie de test",
    )

    return parser.parse_args(argv)


def _resolve_user_and_conversation(email: str, conversation_id: Optional[str]) -> tuple[str, str]:
    db = get_db()

    user_result = db.table("users").select("id").eq("email", email).single().execute()
    if not user_result.data:
        raise RuntimeError(f"Utilisateur introuvable pour l'email {email}")

    user_id = user_result.data["id"]

    if conversation_id:
        conv_result = (
            db.table("conversations")
            .select("id", "ai_mode", "metadata")
            .eq("id", conversation_id)
            .single()
            .execute()
        )
        if not conv_result.data:
            raise RuntimeError(
                "Conversation introuvable. Vérifiez l'identifiant fourni."
            )
        metadata = conv_result.data.get("metadata") or {}
        if metadata.get("user_id") and metadata.get("user_id") != user_id:
            raise RuntimeError("La conversation existe mais n'est pas liée à cet utilisateur.")
        return user_id, conv_result.data["id"]

    conv_query = (
        db.table("conversations")
        .select("id", "ai_mode", "metadata")
        .order("updated_at", desc=True)
        .limit(20)
        .execute()
    )

    for row in conv_query.data or []:
        metadata = row.get("metadata") or {}
        if metadata.get("user_id") == user_id:
            return user_id, row["id"]

    if conv_query.data:
        return user_id, conv_query.data[0]["id"]

    raise RuntimeError(
        "Aucune conversation trouvée pour cet utilisateur. Utilisez --conversation-id ou créez une conversation."
    )


async def _run_service(user_id: str, conversation_id: str, message: str, confidence: float, reason: str) -> Optional[str]:
    service = Escalation(user_id=user_id, conversation_id=conversation_id)
    escalation_id = await service.create_escalation(message=message, confidence=confidence, reason=reason)
    return escalation_id


async def _run_tool(user_id: str, conversation_id: str, message: str, confidence: float, reason: str):
    tool = create_escalation_tool(user_id=user_id, conversation_id=conversation_id)
    return await tool.ainvoke({
        "message": message,
        "confidence": confidence,
        "reason": reason,
    })


async def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    try:
        user_id, conversation_id = _resolve_user_and_conversation(args.user_email, args.conversation_id)
    except RuntimeError as exc:
        logging.error(exc)
        return 1

    logging.info("Utilisateur: %s (%s)", args.user_email, user_id)
    logging.info("Conversation: %s", conversation_id)
    logging.info("Message: %s", args.message)
    logging.info("Confiance: %.1f", args.confidence)
    logging.info("Raison: %s", args.reason)

    if args.mode in {"service", "both"}:
        logging.info("🧪 Test du service Escalation…")
        escalation_id = await _run_service(user_id, conversation_id, args.message, args.confidence, args.reason)
        if escalation_id:
            logging.info("✅ Escalade créée via service: %s", escalation_id)
        else:
            logging.error("❌ Le service n'a pas pu créer l'escalade")

    if args.mode in {"tool", "both"}:
        logging.info("🤖 Test du tool IA 'escalation'…")
        result = await _run_tool(user_id, conversation_id, args.message, args.confidence, args.reason)
        logging.info(
            "Résultat tool → escalated=%s, id=%s, raison=%s",
            result.escalated,
            result.escalation_id,
            result.reason,
        )

    logging.info("📬 Vérifiez la boîte mail yvankondjo8@gmail.com pour confirmer la réception.")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main(sys.argv[1:]))
    except KeyboardInterrupt:
        exit_code = 130
    sys.exit(exit_code)
