from tools.job_alert.mailer import MissingSmtpConfiguration, load_smtp_config


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
