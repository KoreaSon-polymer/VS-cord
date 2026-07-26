from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from io import TextIOWrapper
from typing import assert_never

import anyio

from .deduplication import classify_postings
from .filtering import evaluate_posting
from .mailer import MissingSmtpConfiguration, SmtpConfig, load_smtp_config, send_email
from .models import JobPosting, RunMetrics
from .relevance import rank_postings
from .reporting import build_email
from .scraper import collect_sources
from .sources import SOURCES
from .state import load_state, save_state
from .summary import render_summary, write_summary

KST = timezone(timedelta(hours=9), name="KST")


def configure_console(stream: TextIOWrapper) -> None:
    stream.reconfigure(errors="backslashreplace")


def _enabled(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name, "").strip().casefold() == "true"


def _missing_names(
    config: SmtpConfig | MissingSmtpConfiguration,
) -> tuple[str, ...]:
    match config:
        case SmtpConfig():
            return ()
        case MissingSmtpConfiguration(missing_names=missing_names):
            return missing_names
        case _ as unreachable:
            assert_never(unreachable)


async def run(environment: Mapping[str, str]) -> int:
    now = datetime.now(KST)
    force_test = _enabled(environment, "FORCE_TEST_EMAIL")
    dry_run = _enabled(environment, "DRY_RUN")
    smtp_config = load_smtp_config(environment)
    missing_secrets = _missing_names(smtp_config)
    print(f"Run started at {now.isoformat()} (KST)")
    if missing_secrets:
        print("이메일 발송 설정 누락: " + ", ".join(missing_secrets))
        print("이메일 미발송 상태: SMTP configuration incomplete")

    if force_test:
        candidates = (JobPosting.test_payload(now.date()),)
        collected_count = 1
        deduplicated_count = 0
        excluded_count = 0
        source_errors: tuple[str, ...] = ()
        sources_attempted = 0
    else:
        source_results = await collect_sources()
        raw_postings = tuple(
            posting for result in source_results for posting in result.postings
        )
        evaluated = tuple(
            evaluate_posting(posting, now.date()) for posting in raw_postings
        )
        accepted = tuple(posting for posting in evaluated if posting is not None)
        deduplicated = classify_postings(accepted, load_state())
        candidates = rank_postings(deduplicated.new_postings)
        collected_count = len(raw_postings)
        deduplicated_count = deduplicated.deduplicated_count
        excluded_count = len(raw_postings) - len(accepted)
        source_errors = tuple(
            f"{result.source_name}: {result.error}"
            for result in source_results
            if result.error
        )
        sources_attempted = len(SOURCES)

    email_status = "not sent: no new postings"
    if candidates:
        email_status = "not sent: SMTP configuration incomplete"
    if dry_run and candidates:
        email_status = "dry-run: email rendered"
    metrics = RunMetrics(
        sources_attempted=sources_attempted,
        collected_count=collected_count,
        new_count=len(candidates),
        deduplicated_count=deduplicated_count,
        excluded_count=excluded_count,
        source_errors=source_errors,
        collected_at=now,
        email_status=email_status,
    )
    email = build_email(candidates, metrics, is_test=force_test)
    if dry_run and candidates:
        print(f"DRY RUN email subject: {email.subject}")
        print(email.text_body)
    elif candidates:
        match smtp_config:
            case SmtpConfig():
                send_email(smtp_config, email)
                metrics = replace(metrics, email_status="sent")
                if not force_test:
                    save_state(load_state(), candidates)
            case MissingSmtpConfiguration():
                print("이메일 미발송 상태: required SMTP secrets are missing")
            case _ as unreachable:
                assert_never(unreachable)
    write_summary(render_summary(metrics, missing_secrets=missing_secrets))
    return 0


def main() -> int:
    if isinstance(sys.stdout, TextIOWrapper):
        configure_console(sys.stdout)
    if isinstance(sys.stderr, TextIOWrapper):
        configure_console(sys.stderr)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    return anyio.run(run, os.environ)


if __name__ == "__main__":
    raise SystemExit(main())
