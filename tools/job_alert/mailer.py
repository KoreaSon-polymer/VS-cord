from __future__ import annotations

import smtplib
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from email.message import EmailMessage

from .reporting import EmailContent


@dataclass(frozen=True, slots=True)
class SmtpConfig:
    recipient: str
    host: str
    port: int
    username: str
    password: str
    sender: str


@dataclass(frozen=True, slots=True)
class MissingSmtpConfiguration:
    missing_names: tuple[str, ...]


def load_smtp_config(
    environment: Mapping[str, str],
) -> SmtpConfig | MissingSmtpConfiguration:
    required = (
        "MONITOR_EMAIL_TO",
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    )
    missing = tuple(name for name in required if not environment.get(name, "").strip())
    if missing:
        return MissingSmtpConfiguration(missing)
    username = environment["SMTP_USERNAME"]
    return SmtpConfig(
        recipient=environment["MONITOR_EMAIL_TO"],
        host=environment["SMTP_HOST"],
        port=int(environment.get("SMTP_PORT") or "587"),
        username=username,
        password=environment["SMTP_PASSWORD"],
        sender=environment.get("SMTP_FROM") or username,
    )


def send_email(config: SmtpConfig, content: EmailContent) -> None:
    message = EmailMessage()
    message["Subject"] = content.subject
    message["From"] = config.sender
    message["To"] = config.recipient
    message.set_content(content.text_body)
    message.add_alternative(content.html_body, subtype="html")
    context = ssl.create_default_context()
    with smtplib.SMTP(config.host, config.port, timeout=30) as smtp:
        _ = smtp.ehlo()
        _ = smtp.starttls(context=context)
        _ = smtp.ehlo()
        _ = smtp.login(config.username, config.password)
        print("SMTP connection successful")
        refused = smtp.send_message(message)
    if refused:
        raise smtplib.SMTPRecipientsRefused(refused)
    print(f"Sent direct email to {config.recipient}")
