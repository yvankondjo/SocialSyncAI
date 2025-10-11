import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.escalation import Escalation


def _setup_support_table(mock_table, insert_data=None, update_data=None):
    insert_execute = MagicMock(return_value=MagicMock(data=insert_data))
    mock_table.insert.return_value.execute.return_value = MagicMock(data=insert_data)

    update_mock = MagicMock()
    update_mock.eq.return_value.execute.return_value = MagicMock(data=update_data)
    mock_table.update.return_value = update_mock


def _setup_conversations_table(mock_table):
    update_mock = MagicMock()
    update_mock.eq.return_value.execute.return_value = MagicMock(data=[{"id": "conv-456"}])
    mock_table.update.return_value = update_mock


def _setup_users_table(mock_table, email):
    select_mock = MagicMock()
    eq_mock = MagicMock()
    single_mock = MagicMock()
    execute_mock = MagicMock(return_value=MagicMock(data=email))

    single_mock.execute.return_value = execute_mock.return_value
    eq_mock.single.return_value = single_mock
    select_mock.eq.return_value = eq_mock
    mock_table.select.return_value = select_mock


@pytest.fixture
def escalation_dependencies():
    mock_db = MagicMock()
    support_table = MagicMock()
    conversations_table = MagicMock()
    users_table = MagicMock()

    table_map = {
        "support_escalations": support_table,
        "conversations": conversations_table,
        "users": users_table,
    }

    mock_db.table.side_effect = lambda name: table_map[name]

    with patch("app.services.escalation.get_db", return_value=mock_db), \
         patch("app.services.escalation.EmailService") as email_service_cls, \
         patch("app.services.escalation.LinkService") as link_service_cls:

        email_service = email_service_cls.return_value
        link_service = link_service_cls.return_value
        email_service.send_escalation_email = AsyncMock(return_value=True)
        link_service.generate_conversation_link.return_value = "https://example.com/escalation"

        service = Escalation(user_id="user-123", conversation_id="conv-456")

        yield {
            "service": service,
            "db": mock_db,
            "support_table": support_table,
            "conversations_table": conversations_table,
            "users_table": users_table,
            "email_service": email_service,
            "link_service": link_service,
        }


@pytest.mark.asyncio
async def test_create_escalation_success(escalation_dependencies):
    deps = escalation_dependencies

    _setup_support_table(deps["support_table"], insert_data=[{"id": "esc-789"}], update_data=[{"id": "esc-789", "notified": True}])
    _setup_conversations_table(deps["conversations_table"])
    _setup_users_table(deps["users_table"], email={"email": "user@example.com"})

    escalation_id = await deps["service"].create_escalation(
        message="Need human help",
        confidence=92.5,
        reason="Complex question"
    )

    assert escalation_id == "esc-789"
    deps["email_service"].send_escalation_email.assert_awaited_once_with(
        to_email="support@yourdomain.com",
        escalation_data={
            "id": "esc-789",
            "conversation_id": "conv-456",
            "user_id": "user-123",
            "user_email": "user@example.com",
            "message": "Need human help",
            "confidence": 92.5,
            "reason": "Complex question"
        },
        conversation_link="https://example.com/escalation"
    )
    deps["link_service"].generate_conversation_link.assert_called_once_with(
        conversation_id="conv-456",
        user_id="user-123",
        escalation_id="esc-789"
    )


@pytest.mark.asyncio
async def test_create_escalation_without_email(escalation_dependencies):
    deps = escalation_dependencies

    _setup_support_table(deps["support_table"], insert_data=[{"id": "esc-001"}])
    _setup_conversations_table(deps["conversations_table"])
    _setup_users_table(deps["users_table"], email={})

    escalation_id = await deps["service"].create_escalation(
        message="No email",
        confidence=50,
        reason="Missing email"
    )

    assert escalation_id == "esc-001"
    deps["email_service"].send_escalation_email.assert_not_called()


@pytest.mark.asyncio
async def test_create_escalation_insert_failure(escalation_dependencies):
    deps = escalation_dependencies

    _setup_support_table(deps["support_table"], insert_data=[])

    escalation_id = await deps["service"].create_escalation(
        message="Failure",
        confidence=10,
        reason="Insert failed"
    )

    assert escalation_id is None
    deps["email_service"].send_escalation_email.assert_not_called()
