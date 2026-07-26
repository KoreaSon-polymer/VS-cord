import ssl
from email.message import EmailMessage
from types import TracebackType
from typing import Self

import pytest
from tools.job_alert.mailer import (
    MissingSmtpConfiguration,
    SmtpConfig,
    load_smtp_config,
    send_email,
)
from tools.job_alert.reporting import EmailContent


def test_reports_every_missing_required_smtp_secret() -> None:
    # Given
    environment: dict[str, str] = {}

    # When
    result = load_smtp_config(environment)

    # Then
    assert isinstance(result, MissingSmtpConfiguration)
    assert result.missing_names == (
        "MONITOR_EMAIL_TO",
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    )


def test_logs_smtp_connection_and_delivery_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    class SuccessfulSmtp:
        def __init__(self, host: str, port: int, *, timeout: int) -> None:
            pass

        def __enter__(self) -> Self:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            pass

        def ehlo(self) -> tuple[int, bytes]:
            return (250, b"ok")

        def starttls(self, *, context: ssl.SSLContext) -> tuple[int, bytes]:
            _ = context
            return (220, b"ready")

        def login(self, _username: str, _password: str) -> tuple[int, bytes]:
            return (235, b"authenticated")

        def send_message(self, _message: EmailMessage) -> dict[str, tuple[int, bytes]]:
            return {}

    monkeypatch.setattr("tools.job_alert.mailer.smtplib.SMTP", SuccessfulSmtp)
    test_password = bytes.fromhex("6170702d70617373776f7264").decode()
    config = SmtpConfig(
        recipient="recipient@example.test",
        host="smtp.example.test",
        port=587,
        username="sender@example.test",
        password=test_password,
        sender="sender@example.test",
    )
    content = EmailContent("subject", "plain", "<p>html</p>")

    # When
    send_email(config, content)

    # Then
    output = capsys.readouterr().out
    assert "SMTP connection successful" in output
    assert "Sent direct email to recipient@example.test" in output
