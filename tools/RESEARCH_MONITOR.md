# Korean permanent research careers and funding monitor v2

## Scope

Job alerts are for Korean university full-time faculty appointments and permanent research positions at public research institutes. Postdocs, research fellows, temporary/contract researchers, non-tenure-track faculty, adjuncts, research professors, directors and presidents are excluded. Chemistry, organic/polymer semiconductors, synthesis, photocatalysis, electrochemistry, materials, interfaces, devices and sensors form the research relevance vocabulary. Permanent employment and research-field evidence are required; a title containing `postdoc` does not qualify merely because a body mentions permanent employment.

Funding remains separate from jobs: fellowships, early-career/basic research and relevant institutional/joint calls may be useful. Personal eligibility is not asserted from keywords. Every item shows the observed qualification and host conditions; unavailable details are labeled unverified. Institutional calls are labeled for collaboration/future appointment rather than presented as immediately accessible personal grants.

## What changed

- The old funding program was a gzip/base64 executable; it is now readable Python.
- One scheduled workflow replaces two daily workflows. Legacy workflows allow preview only.
- Funding reports no longer create GitHub issues, assign anyone or mention the repository owner. The workflow has no issue-write permission or issue API code.
- A delivered-notice JSON ledger replaces searching GitHub issues for deduplication. URL session IDs, tracking and list-page parameters do not change notice identity. State is updated only after successful SMTP delivery.
- New notices, changed conditions/deadlines and the 14/7/3-day reminder thresholds generate events, each once. No routine empty daily email. A weekly Monday health summary makes broken collection visible.
- `비정규직` no longer matches `정규직`. Publication and appointment dates are not used as application deadlines. Expired calls are excluded before ranking, even if they mention a priority program.
- University expansion includes SNU, POSTECH, Korea, Yonsei, SKKU, Hanyang, Pusan, PKNU and KNU, in addition to the four science institutes. Six pages of the Korean Council for University Education faculty board cover additional universities nationwide. This supplements 16 institute boards and ALIO/JOB-ALIO. A configured source is not a guarantee of successful coverage.
- NRF uses its current `/page/362`, `/page/364` boards and `data-post_no` detail identifiers. IRIS attachment IDs are resolved to its official download endpoint, and its HWP body text is extracted. IRIS uses the `ListView` page and resolves notice IDs from its onclick attributes rather than mistaking JavaScript links for real notices. IRIS covers multiple ministries/agencies, including NRF and energy/industrial programs. MSIT uses the business-call board rather than its homepage.
- Main article content and up to three bounded PDF/HWP/HWPX/ZIP attachments are read. Encrypted HWP, scanned PDFs, unrecognized JavaScript download buttons and login-only boards can still require manual review. No OCR or fabricated attachment content.

## Operation

The scheduled workflow runs daily at 00:30 UTC (09:30 KST). GitHub may start scheduled workflows later than the cron time. Monday health information is included in the same digest. Existing SMTP secret names are reused.

```bash
python -m pip install -r tools/research_monitor_requirements.txt pytest
python -m pytest tests -q
DRY_RUN=true python -m tools.research_monitor
```

`monitor-output/digest.txt`, `health.json` and `candidates.json` are uploaded as the `research-monitor-report` workflow artifact, with 14-day retention. Push-triggered runs are always dry runs. Manual dispatch defaults to dry run. A scheduled run delivers only if a new/change/reminder event or weekly summary is due. Preview does not send mail and does not change state.

`tools/research_monitor_state.json` holds successful deliveries. Do not delete it to troubleshoot collectors: that would cause a fresh baseline. Failed SMTP leaves the state intact, so the next run can retry. If SMTP succeeds but the subsequent state commit fails, duplicate mail is possible; the failed persistence step must be repaired before manually repeating a delivery run.

## Coverage and limitations

The health report distinguishes HTTP failures, no usable candidate links, detail/attachment failures and successful extraction. A successful HTTP response or a zero-notice digest does not imply every institution has been checked completely. Date/field evidence that cannot be extracted is conservatively excluded; the source and attachment health should be reviewed weekly. Source queries are bounded to control runtime and may not include older postings beyond the configured pages.

Live checks on 2026-09-06 confirmed the NRF, IRIS, KCUE, Korea, Yonsei, SNU, Pusan and PKNU board routes. SKKU returned 404, KNU returned 500 and MSIT intermittently returned 502 in the local environment; these remain visible in health instead of being reported as empty boards. A subsequent live collection extracted 26 of 36 job-source queries and selected a KIMS permanent recruitment notice. A focused funding recheck read IRIS calls successfully; their individual eligibility still requires the attached call conditions. The per-run health output remains the authoritative coverage record. No claim of nationwide completeness is made.

The monitor uses GitHub scheduling, local JSON state and SMTP. It has no Cloudflare D1 dependency. Cloudflare database quota alarms require identifying the separate Worker/database consuming the quota.
