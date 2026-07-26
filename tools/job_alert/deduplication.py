from __future__ import annotations

from dataclasses import dataclass

from .models import JobPosting, SentRecord


@dataclass(frozen=True, slots=True)
class DeduplicationResult:
    new_postings: tuple[JobPosting, ...]
    deduplicated_count: int


def classify_postings(
    candidates: tuple[JobPosting, ...],
    sent_records: tuple[SentRecord, ...],
) -> DeduplicationResult:
    by_url = {record.url_key: record for record in sent_records}
    by_auxiliary = {record.auxiliary_key: record for record in sent_records}
    new_postings: list[JobPosting] = []
    duplicate_count = 0
    current_urls: set[str] = set()
    current_auxiliary: set[str] = set()
    for posting in candidates:
        if (
            posting.url_key in current_urls
            or posting.auxiliary_key in current_auxiliary
        ):
            duplicate_count += 1
            continue
        current_urls.add(posting.url_key)
        current_auxiliary.add(posting.auxiliary_key)
        previous = by_url.get(posting.url_key) or by_auxiliary.get(
            posting.auxiliary_key
        )
        if previous is None:
            new_postings.append(posting)
            continue
        if previous.content_hash == posting.content_hash:
            duplicate_count += 1
            continue
        if previous.deadline != posting.deadline:
            note = f"접수 마감일 변경: {previous.deadline} → {posting.deadline}"
        else:
            note = "공고 내용 수정 또는 재공고"
        new_postings.append(posting.as_changed(note))
    return DeduplicationResult(tuple(new_postings), duplicate_count)
