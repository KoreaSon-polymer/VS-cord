from __future__ import annotations

import os
from pathlib import Path

from .models import RunMetrics


def render_summary(metrics: RunMetrics, *, missing_secrets: tuple[str, ...]) -> str:
    errors = "\n".join(f"- {item}" for item in metrics.source_errors) or "- 없음"
    secret_status = (
        "설정 완료"
        if not missing_secrets
        else "설정 누락: " + ", ".join(f"`{name}`" for name in missing_secrets)
    )
    return (
        "# Daily Korean Research Job Alert\n\n"
        f"- 실행 시간 (KST): {metrics.collected_at.isoformat()}\n"
        f"- 소스 수: {metrics.sources_attempted}\n"
        f"- 수집 후보: {metrics.collected_count}\n"
        f"- 신규 공고: {metrics.new_count}\n"
        f"- 중복 제외: {metrics.deduplicated_count}\n"
        f"- 필터 제외: {metrics.excluded_count}\n"
        f"- SMTP secrets: {secret_status}\n"
        f"- 이메일 발송 상태: **{metrics.email_status}**\n\n"
        "## 오류 또는 접근 실패 소스\n"
        f"{errors}\n"
    )


def write_summary(content: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            _ = summary_file.write(content)
    print(content)
