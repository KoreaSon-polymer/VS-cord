from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from .models import JobPosting, SentRecord

STATE_PATH = Path(__file__).with_name("notified_state.json")


class StateRecordModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    url_key: str
    auxiliary_key: str
    content_hash: str
    deadline: str | None

    def to_record(self) -> SentRecord:
        deadline = date.fromisoformat(self.deadline) if self.deadline else None
        return SentRecord(
            url_key=self.url_key,
            auxiliary_key=self.auxiliary_key,
            content_hash=self.content_hash,
            deadline=deadline,
        )


class StateFileModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    records: tuple[StateRecordModel, ...]


def load_state(path: Path = STATE_PATH) -> tuple[SentRecord, ...]:
    parsed = StateFileModel.model_validate_json(path.read_text(encoding="utf-8"))
    return tuple(item.to_record() for item in parsed.records)


def save_state(
    previous: tuple[SentRecord, ...],
    sent_postings: tuple[JobPosting, ...],
    path: Path = STATE_PATH,
) -> None:
    sent_records = tuple(SentRecord.from_posting(item) for item in sent_postings)
    sent_urls = {item.url_key for item in sent_records}
    sent_auxiliary = {item.auxiliary_key for item in sent_records}
    retained = tuple(
        item
        for item in previous
        if item.url_key not in sent_urls and item.auxiliary_key not in sent_auxiliary
    )
    combined = retained + sent_records
    model = StateFileModel(
        records=tuple(
            StateRecordModel(
                url_key=item.url_key,
                auxiliary_key=item.auxiliary_key,
                content_hash=item.content_hash,
                deadline=item.deadline.isoformat() if item.deadline else None,
            )
            for item in combined
        )
    )
    _ = path.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")
