from io import BytesIO, TextIOWrapper

from tools.job_alert.monitor import configure_console


def test_console_output_does_not_crash_on_unencodable_source_title() -> None:
    # Given
    buffer = BytesIO()
    stream = TextIOWrapper(buffer, encoding="ascii")

    # When
    configure_console(stream)
    _ = stream.write("연구원 • Post-Doc")
    stream.flush()

    # Then
    assert b"\\u2022" in buffer.getvalue()
