# Korean research funding monitor

This GitHub Actions workflow checks official Korean R&D funding announcement sources once per day and creates a GitHub Issue only when it finds a practically useful opportunity for the configured research profile.

## Schedule

The workflow runs every day at 09:30 Korea Standard Time.

Manual run: GitHub repository → Actions → Korean research funding monitor → Run workflow.

## Notification behavior

1. Default notification: when a relevant opportunity is found, the workflow creates a GitHub Issue and mentions or assigns the repository owner. GitHub then sends an email notification according to the account notification settings.
2. Optional direct email: add SMTP repository secrets and the same report will also be sent to the address stored in `MONITOR_EMAIL_TO`.

Required secrets for direct email:

- `MONITOR_EMAIL_TO`, the recipient email address
- `SMTP_HOST`, for example `smtp.gmail.com`
- `SMTP_PORT`, normally `587`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`, for Gmail use an app password rather than the normal account password
- `SMTP_FROM`, optional if it is the same as `SMTP_USERNAME`

## Monitored sources

The script checks candidate pages from NRF, IRIS, MSIT, MOE, MOTIE, KEIT, KIAT, KETEP, IITP, and NST. Some official Korean sites use dynamic pages or JavaScript-only links, so the monitor is intentionally conservative. If it finds a relevant title but cannot parse every detail, it includes the source board and asks for original PDF or IRIS page verification.

## Relevance profile

The filter prioritizes:

- 세종과학펠로우십
- 학문후속세대지원사업
- 우수신진연구
- 개인기초연구
- 창의도전연구기반지원
- 신진연구자 정착지원
- 해외우수연구자 유치
- 귀국 연구자 지원
- International collaboration programs suitable for Korean researchers abroad
- Energy, hydrogen, carbon neutrality, semiconductor, advanced materials, nanomaterials, sensors, electrochemistry, optoelectronic devices, and organic electronic materials programs

The research fit keywords are organic semiconductors, organic optoelectronic materials, photocatalysis, photocatalytic hydrogen evolution, hydrogen sensors, organic photoelectrochemistry, OMIECs, OECTs, n-type SAMs, interfacial charge transfer, polymer semiconductors, electrochemistry, materials chemistry, and energy materials.

## Deadline handling

The script tries to extract and separate announcement date, application period, researcher submission deadline, institution approval deadline, final submission deadline, and attached PDF deadlines. If dates from HTML or IRIS and attached PDFs differ, the report flags the discrepancy and asks for the original announcement PDF to be treated as authoritative.

## Duplicate prevention

Each opportunity receives a dedupe key based on agency, title, and URL. Before creating a new Issue, the script checks existing Issues for the same key.
