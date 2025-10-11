import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag_agent import create_escalation_tool, EscalationResult


@pytest.mark.asyncio
async def test_escalation_tool_success():
    with patch("app.services.rag_agent.Escalation") as escalation_cls:
        instance = escalation_cls.return_value
        instance.create_escalation = AsyncMock(return_value="esc-success")

        tool = create_escalation_tool(user_id="user-123", conversation_id="conv-456")

        result = await tool.ainvoke({
            "message": "Need human",
            "confidence": 88.0,
            "reason": "Difficult question"
        })

        assert isinstance(result, EscalationResult)
        assert result.escalated is True
        assert result.escalation_id == "esc-success"
        assert "succès" in result.reason
        instance.create_escalation.assert_awaited_once()


@pytest.mark.asyncio
async def test_escalation_tool_failure():
    with patch("app.services.rag_agent.Escalation") as escalation_cls:
        instance = escalation_cls.return_value
        instance.create_escalation = AsyncMock(return_value=None)

        tool = create_escalation_tool(user_id="user-123", conversation_id="conv-456")

        result = await tool.ainvoke({
            "message": "Need human",
            "confidence": 30.0,
            "reason": "Unclear"
        })

        assert isinstance(result, EscalationResult)
        assert result.escalated is False
        assert result.escalation_id is None
        assert "Échec" in result.reason


@pytest.mark.asyncio
async def test_escalation_tool_exception():
    with patch("app.services.rag_agent.Escalation") as escalation_cls, \
         patch("app.services.rag_agent.logging") as logging_module:
        instance = escalation_cls.return_value
        instance.create_escalation = AsyncMock(side_effect=RuntimeError("boom"))

        logging_module.getLogger.return_value = MagicMock()
        tool = create_escalation_tool(user_id="user-123", conversation_id="conv-456")

        result = await tool.ainvoke({
            "message": "Need human",
            "confidence": 70.0,
            "reason": "Error"
        })

        assert isinstance(result, EscalationResult)
        assert result.escalated is False
        assert result.escalation_id is None
        assert "Erreur technique" in result.reason
