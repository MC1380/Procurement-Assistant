
from pydantic import BaseModel


class EmailSendResult(BaseModel):
    """Result of a simulated email send operation."""

    success: bool
    recipient: str
    subject: str
    message: str


class MockEmailSender:
    """Simulate sending emails without contacting an email provider."""

    def send(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> EmailSendResult:
        """Return a simulated result instead of sending a real email."""

        if not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not subject.strip():
            raise ValueError("Subject cannot be empty.")

        if not body.strip():
            raise ValueError("Email body cannot be empty.")

        return EmailSendResult(
            success=True,
            recipient=recipient,
            subject=subject,
            message="Email simulated successfully.",
        )
