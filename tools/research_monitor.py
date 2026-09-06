"""One daily digest for permanent Korean careers and useful research funding."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

import anyio
from tools.funding_monitor.monitor import collect as collect_funding
from tools.job_alert.scraper import collect_sources
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.mailer import SmtpConfig, load_smtp_config, send_email
from tools.job_alert.reporting import EmailContent
from tools.notice_utils import canonical_url

KST = timezone(timedelta(hours=9))
STATE_PATH = Path('tools/research_monitor_state.json')
OUTPUT_PATH = Path('monitor-output')
REMINDERS = (14, 7, 3)


def load_state(path=STATE_PATH):
    if not path.exists():
        return {'version': 2, 'records': {}, 'last_health_sent': None}
    state = json.loads(path.read_text())
    if state.get('version') != 2 or not isinstance(state.get('records'), dict):
        raise ValueError('Unsupported/corrupt delivery state; refusing to resend everything')
    return state


def save_state(state, path=STATE_PATH):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def to_opportunity(posting):
    return dict(kind='job', key=hashlib.sha256(canonical_url(posting.url).encode()).hexdigest()[:24],
                fingerprint=posting.content_hash, title=posting.title, institution=posting.institution,
                url=posting.url, deadline=str(posting.deadline) if posting.deadline else None,
                priority='전임교원 신규 임용' if '교원' in posting.position else '정규 연구직',
                category=posting.employment_type, fields=list(posting.research_fields),
                relevance=posting.fit_reasons[0], relevance_rank={90: 0, 70: 1, 50: 2}.get(posting.fit_score, 2),
                eligibility=posting.qualifications, host='', amount='',
                action='초빙 분야·직무기술서와 학위·경력·논문 요건 대조', errors=[])


def notification_events(opportunities, state, today):
    """One event per notice/revision/reminder bucket, independent of today's URL session."""
    events, seen = [], set()
    records = state['records']
    for op in opportunities:
        # Common faculty titles at different universities are distinct calls.
        # Ignore an optional English institute abbreviation for direct/NST mirrors.
        institution = re.sub(r'\s*\([A-Za-z -]+\)', '', op['institution'])
        mirror = hashlib.sha256((op['kind'] + '|' + ''.join(institution.split()).lower() + '|' + ''.join(op['title'].split()).lower() + '|' + str(op['deadline'])).encode()).hexdigest()
        if op['key'] in seen or mirror in seen:
            continue
        seen.update((op['key'], mirror))
        previous = records.get(op['key']) or next((v for v in records.values() if v.get('mirror') == mirror), None)
        end = date.fromisoformat(op['deadline']) if op['deadline'] else None
        if end and end < today:
            continue
        days = (end - today).days if end else None
        bucket = min((b for b in REMINDERS if days is not None and 0 <= days <= b), default=None)
        reason = None
        if previous is None:
            reason = '신규'
        elif previous['fingerprint'] != op['fingerprint']:
            # Mirrored source formatting alone must not create an update.
            if previous.get('url') == op['url']:
                reason = '조건·일정 변경'
        elif bucket is not None and f"{op['deadline']}:{bucket}" not in previous.get('reminders', []):
            reason = f'마감 {days}일 전'
        if reason:
            events.append(dict(op=op, reason=reason, bucket=bucket, mirror=mirror, previous=previous))
    return sorted(events, key=lambda e:(e['op']['kind'] != 'job', e['op'].get('relevance_rank', 0), e['op']['priority'] == '협력·향후 임용 참고', e['op']['deadline'] or '9999'))


def mark_delivered(state, events, today):
    for event in events:
        op = event['op']
        reminders = list((event['previous'] or {}).get('reminders', []))
        if event['bucket'] is not None:
            reminders.append(f"{op['deadline']}:{event['bucket']}")
        state['records'][op['key']] = dict(fingerprint=op['fingerprint'], mirror=event['mirror'],
                                          url=op['url'], deadline=op['deadline'],
                                          sent_at=today.isoformat(), reminders=sorted(set(reminders)))


def render(events, health, today, include_health=False):
    parts = [f'한국 정규 연구직·전임교원 및 연구비 | {today}', '']
    for i, event in enumerate(events, 1):
        op = event['op']
        deadline = op['deadline'] or '공고문 확인 / 상시채용 여부 확인'
        parts += [f"{i}. [{event['reason']}] {op['title']}",
                  f"기관: {op['institution']} | 구분: {op['category']}",
                  f"마감(KST): {deadline} | 분류: {op['priority']}",
                  '연구·사업 관련 근거: ' + ', '.join(op['fields'][:8]),
                  '자격: ' + op['eligibility']]
        if op['kind'] == 'job':
            parts += ['전공 관련성: ' + op.get('relevance', '원문 확인') + ' (공고 키워드 기준, 지원 자격·합격 가능성을 의미하지 않음)']
        if op['kind'] == 'funding':
            parts += ['기관 조건: ' + op['host'], '지원 규모·기간: ' + op['amount']]
        parts += ['다음 확인: ' + op['action'], op['url'], '']
    impaired = [h for h in health if h['status'] != 'ok' or h.get('detail_failures')]
    if impaired:
        parts += [f'수집 제한: {len(impaired)}/{len(health)}개 조회에서 접근 실패·목록 또는 첨부 확인이 필요합니다. 확인하지 못한 기관에 공고가 없다는 의미가 아닙니다.']
    if include_health:
        parts += ['', '주간 수집 상태 (기관별 상세 결과는 실행 보고서에 기록)']
        parts += [f"- {h['source']}: {h['status']} / 후보 {h['count']}건" for h in health]
    if not events:
        parts.insert(2, '이번 주 발송할 신규·변경·마감 알림은 없습니다. 아래 수집 제한을 확인하세요.')
    text = '\n'.join(parts)
    subject = f'[한국 연구 커리어] 신규·변경·마감 {len(events)}건 | {today}' if events else f'[한국 연구 커리어] 주간 수집 상태 | {today}'
    return EmailContent(subject, text, "<div style='font-family:Arial,sans-serif;line-height:1.65;white-space:pre-wrap'>" + html.escape(text) + '</div>')


async def run(environment):
    today = datetime.now(KST).date()
    dry_run = environment.get('DRY_RUN', '').lower() == 'true'
    state = load_state()
    # Save outputs even with no email: empty results and broken collection differ.
    source_results = await collect_sources()
    job_ops = [to_opportunity(p) for r in source_results for raw in r.postings if (p := evaluate_posting(raw, today))]
    funding_ops, funding_health = await anyio.to_thread.run_sync(collect_funding)
    health = [dict(source=r.source_name, count=r.discovered, status='ok' if not r.error else r.error,
                   detail_failures=r.detail_errors) for r in source_results] + funding_health
    opportunities = job_ops + funding_ops
    events = notification_events(opportunities, state, today)
    last = state.get('last_health_sent')
    health_due = today.weekday() == 0 and (not last or (today-date.fromisoformat(last)).days >= 7)
    email = render(events, health, today, include_health=health_due)
    OUTPUT_PATH.mkdir(exist_ok=True)
    (OUTPUT_PATH/'digest.txt').write_text(email.text_body)
    (OUTPUT_PATH/'health.json').write_text(json.dumps(health, ensure_ascii=False, indent=2))
    (OUTPUT_PATH/'candidates.json').write_text(json.dumps(opportunities, ensure_ascii=False, indent=2))
    summary = f"Jobs accepted: {len(job_ops)}; funding accepted: {len(funding_ops)}; notification events: {len(events)}; dry-run: {dry_run}\n"
    summary += '\n'.join(f"- {h['source']}: {h['status']}, candidates={h['count']}" for h in health)
    print(summary)
    if environment.get('GITHUB_STEP_SUMMARY'):
        Path(environment['GITHUB_STEP_SUMMARY']).write_text(summary)
    if dry_run:
        print('Preview saved; no email sent and delivery state unchanged.')
        return 0
    if not events and not health_due:
        print('No new actionable notices. No email.')
        return 0
    config = load_smtp_config(environment)
    if not isinstance(config, SmtpConfig):
        raise RuntimeError('SMTP configuration missing; delivery state unchanged')
    send_email(config, email)
    mark_delivered(state, events, today)
    if health_due:
        state['last_health_sent'] = today.isoformat()
    save_state(state)
    return 0


def main():
    return anyio.run(run, os.environ)


if __name__ == '__main__':
    raise SystemExit(main())
