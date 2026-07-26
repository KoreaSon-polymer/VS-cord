from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Final

from .models import JobPosting, PriorityLevel, RunMetrics
from .relevance import recommended_profile_emphasis

URGENT_DAYS: Final = 7


@dataclass(frozen=True, slots=True)
class EmailContent:
    subject: str
    text_body: str
    html_body: str


def _format_posting(index: int, posting: JobPosting) -> str:
    deadline = posting.deadline.isoformat() if posting.deadline else "원문 확인"
    fields = ", ".join(posting.research_fields)
    reasons = "\n".join(f"  - {reason}" for reason in posting.fit_reasons)
    emphases = recommended_profile_emphasis(posting.research_fields)
    emphasis_lines = "\n".join(
        f"  {item}. {emphasis}" for item, emphasis in enumerate(emphases, start=1)
    )
    change = f"\n- 변경사항: {posting.change_note}" if posting.change_note else ""
    return (
        f"### {index}. {posting.institution} · {posting.position} · {posting.title}\n"
        f"- 채용 제목: {posting.title}\n"
        f"- 고용 형태: {posting.employment_type}\n"
        f"- 연구 분야: {fields}\n"
        f"- 지원 자격: {posting.qualifications}\n"
        f"- 근무지: {posting.location}\n"
        f"- 접수 시작일: {posting.start_date or '원문 확인'}\n"
        f"- 접수 마감일: {deadline}\n"
        f"- 최초 발견일: {posting.first_seen}\n"
        f"- 이전 알림 여부: {'예' if posting.previously_notified else '아니오'}\n"
        f"- 적합도: {posting.fit_score}/100\n"
        f"- Priority: {posting.priority.value}\n"
        f"- Fit analysis:\n{reasons or '  - Researcher-level role'}\n"
        f"- Recommended profile emphasis:\n"
        f"{emphasis_lines or '  1. Relevant research experience'}\n"
        f"- 원문 URL: {posting.url}{change}"
    )


def build_email(
    postings: tuple[JobPosting, ...],
    metrics: RunMetrics,
    *,
    is_test: bool,
) -> EmailContent:
    today = metrics.collected_at.date()
    marker = "[TEST] " if is_test else ""
    subject = (
        f"{marker}[Korean Research Job Alert] 신규 공고 {len(postings)}건 · {today}"
    )
    urgent = tuple(
        posting
        for posting in postings
        if posting.deadline is not None
        and 0 <= (posting.deadline - today).days <= URGENT_DAYS
    )
    high_fit = tuple(
        posting
        for posting in postings
        if posting.priority is PriorityLevel.APPLY_SERIOUSLY
    )
    all_items = "\n\n".join(
        _format_posting(index, posting)
        for index, posting in enumerate(postings, start=1)
    )
    errors = "\n".join(f"- {item}" for item in metrics.source_errors) or "- 없음"
    urgent_lines = "\n".join(f"- {item.title}" for item in urgent) or "- 없음"
    high_fit_lines = (
        "\n".join(f"- {item.title} ({item.fit_score}/100)" for item in high_fit)
        or "- 없음"
    )
    text = "\n".join(
        (
            "# Daily Korean Research Job Alert",
            "",
            f"- 신규 공고: {len(postings)}건",
            f"- 마감 임박: {len(urgent)}건",
            f"- 높은 적합도: {len(high_fit)}건",
            f"- 수집 시간: {metrics.collected_at.isoformat()}",
            f"- 수집 후보: {metrics.collected_count}건",
            f"- 중복 제외: {metrics.deduplicated_count}건",
            f"- 필터 제외: {metrics.excluded_count}건",
            "",
            "## 마감 임박 공고",
            urgent_lines,
            "",
            "## 높은 적합도 공고",
            high_fit_lines,
            "",
            "## 전체 신규 공고 목록",
            "",
            all_items or "신규 공고 없음",
            "",
            "## 오류 또는 접근 실패 소스",
            errors,
        )
    )
    return EmailContent(
        subject=subject,
        text_body=text,
        html_body=f"<pre style='white-space:pre-wrap'>{html.escape(text)}</pre>",
    )
