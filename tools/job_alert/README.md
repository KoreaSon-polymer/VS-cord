# Superseded by the unified permanent-career monitor

See [RESEARCH_MONITOR.md](../RESEARCH_MONITOR.md) for current filters, source coverage, scheduling and delivery. The historical instructions below describe v1 and must not be used to re-enable its schedules.

# Daily Korean Research Job Alert

This monitor is independent from `.github/workflows/korean-funding-monitor.yml`.
It does not import, modify, or share state with the Korean research funding monitor.

## Schedule and manual test

The workflow runs every day at 09:30 Korea Standard Time (00:30 UTC). It also
supports `workflow_dispatch`.

Set `force_test_email=true` to send one synthetic KRICT postdoctoral posting.
The subject starts with `[TEST]`, and test data never updates
`notified_state.json`.

## Sources

The monitor attempts the official recruitment or announcement pages for:

- JOB-ALIO and ALIO
- KRICT, KIST, KIMS, KIER, KIMM, ETRI, KRISS, KBSI, KISTI
- KITECH, KERI, KICT, KAERI, and IBS
- DGIST, GIST, UNIST, and KAIST

Each source is isolated. A blocked or changed site is reported in the Actions
log and job summary without preventing other sources from being processed.

## Filtering

The allowlist favors postdoctoral researchers, research professors, regular
research staff, senior/principal researchers, and other doctoral research
positions. Relevance scoring covers organic and polymer semiconductors,
photocatalysis, hydrogen production and sensing, electrochemistry, organic
electronics, OMIEC/OECT, n-type SAMs, interfacial charge transfer,
optoelectronic devices, device physics, and materials chemistry.

The denylist rejects expired postings, successful-candidate announcements,
selection results, bids, funding programs, research grants, and project calls.
Every retained item must contain a research-position indicator.

## Deduplication

The canonical URL is the primary key. A SHA-256 auxiliary key combines the
institution, title, start date, and deadline. The content fingerprint detects
deadline changes, edited notices, and repostings. State is updated only after a
successful real SMTP send. Test emails never affect state.

## SMTP secrets

Configure these repository Actions secrets:

- `MONITOR_EMAIL_TO`
- `SMTP_HOST`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_PORT` (optional, defaults to `587`)
- `SMTP_FROM` (optional, defaults to `SMTP_USERNAME`)

The sender uses STARTTLS. For Gmail and other providers that require it, use an
app password rather than the normal account password.

For Gmail, use:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<Gmail address>
SMTP_PASSWORD=<Google App Password>
SMTP_FROM=<Gmail address>
MONITOR_EMAIL_TO=<recipient email>
```

A normal Gmail account password does not work for this SMTP setup. Enable
two-step verification for the sending Google account and create a Google App
Password. Store that App Password only as the `SMTP_PASSWORD` repository
secret.

From PowerShell, run the secure interactive setup helper:

```powershell
.\scripts\set_smtp_secrets.ps1
```

The helper hides password input, passes values directly to `gh secret set`,
and prints only the configured secret names. It does not write credentials to
disk.

If required secrets are absent, the workflow still completes collection but
prints every missing secret name and an explicit `email not sent` status in
both the log and job summary. Secret values are never printed.

## Local dry run

```bash
uv pip install --system -r tools/job_alert/requirements-dev.txt
FORCE_TEST_EMAIL=true DRY_RUN=true python -m tools.job_alert.monitor
```
