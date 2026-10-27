
import pytest

from procurement_assistant.services.email_service import MockEmailSender


def test_mock_email_sender_returns_success():
    sender = MockEmailSender()

    result = sender.send(
        recipient="manager@example.com",
        subject="Purchase approval required",
        body="Please review purchase request REQ-001.",
    )

    assert result.success is True
    assert result.recipient == "manager@example.com"
    assert result.subject == "Purchase approval required"
    assert result.message == "Email simulated successfully."


def test_mock_email_sender_rejects_empty_recipient():
    sender = MockEmailSender()

    with pytest.raises(ValueError, match="Recipient cannot be empty."):
        sender.send(
            recipient=" ",
            subject="Purchase approval required",
            body="Please review this request.",
        )


def test_mock_email_sender_rejects_empty_subject():
    sender = MockEmailSender()

    with pytest.raises(ValueError, match="Subject cannot be empty."):
        sender.send(
            recipient="manager@example.com",
            subject=" ",
            body="Please review this request.",
        )


def test_mock_email_sender_rejects_empty_body():
    sender = MockEmailSender()

    with pytest.raises(ValueError, match="Email body cannot be empty."):
        sender.send(
            recipient="manager@example.com",
            subject="Purchase approval required",
            body=" ",
        )
