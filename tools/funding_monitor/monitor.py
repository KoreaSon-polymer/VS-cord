"""Official funding notices with explicit program and eligibility evidence."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import hashlib
import re
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup
from tools.notice_utils import application_period, article_text, canonical_url, dates, matches, research_matches
from tools.notice_documents import attachment_links, document_text, MAX_BYTES

KST = timezone(timedelta(hours=9))
SOURCES = [
    ('NRF', '신규사업공모', 'https://www.nrf.re.kr/page/362?menuNo=362&bizNotGubn=guide'),
    ('NRF', '사업일반공지', 'https://www.nrf.re.kr/page/364?menuNo=364'),
    ('IRIS', '범부처 사업공고', 'https://www.iris.go.kr/contents/retrieveBsnsAncmBtinSituListView.do'),
    ('MSIT', '사업공고', 'https://www.msit.go.kr/bbs/list.do?mId=311&mPid=121&sCode=user'),
    ('MOE', '교육부 공고', 'https://www.moe.go.kr/boardCnts/listRenew.do?boardID=333&m=0205&s=moe'),
]
PROGRAMS = ('세종과학', '학문후속세대', '박사후국내', '박사후 국외', '박사후국외', '박사후 국내',
            '우수신진', '신진연구', '신진 연구', '개인기초', '개인 기초', '기초연구', '창의도전',
            'Brain Pool', '브레인풀', '해외우수연구자', '국제공동연구', '국제 공동연구', '공동연구지원',
            '인터내셔널 모빌리티', '해외연수', '국외연수', '복귀·유치', '복귀유치')
EXCLUDE = re.compile(r'채용|초빙|원장|총장|이사장|입찰|용역|구매|선정\s*결과|선정\s*공고|선정\s*명단|합격|평가위원|기획위원|명단공개|수요\s*조사|만족도|성과\s*조사')
FUNDING = re.compile(r'공모|신규\s*과제|신규\s*지원|신청|접수|지원\s*계획|연구비|펠로우십|fellowship|grant|call for', re.I)


def get(url):
    r = requests.get(url, timeout=(25, 35), headers={'User-Agent': 'KoreanResearchMonitor/2.0'})
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == 'iso-8859-1':
        r.encoding = r.apparent_encoding
    return r.text


def candidates_from_page(agency, source_name, url, markup):
    soup = BeautifulSoup(markup, 'html.parser')
    result, seen = [], set()
    for a in soup.select('a'):
        title = re.sub(r'\s+', ' ', a.get_text(' ', strip=True)).strip()
        if not FUNDING.search(title) or EXCLUDE.search(title):
            continue
        href = a.get('href', '')
        if agency == 'NRF' and a.get('data-post_no') and a.get('data-post_close_yn') != 'Y':
            href = '/biz/notice/view?' + urlencode(dict(ac='view', menuNo='362' if '신규' in source_name else '364', postNo=a['data-post_no'], bizNo=a.get('data-biz_no', ''), bizNotGubn='guide' if '신규' in source_name else 'notice'))
        if agency == 'IRIS':
            m = re.search(r"BtinSituListForm_view\('([0-9]+)'", a.get('onclick', ''))
            if m:
                href = '/contents/retrieveBsnsAncmView.do?ancmId=' + m.group(1)
        if not href or href.startswith(('javascript:', '#')):
            continue
        full = canonical_url(urljoin(url, href))
        if full == canonical_url(url) or full in seen:
            continue
        if not matches(title, PROGRAMS) and not (research_matches(title) or matches(title, ('수소', '에너지소재', '에너지 소재'))):
            continue
        seen.add(full)
        row = a.find_parent('tr') or a.find_parent('li') or a.parent
        result.append(dict(agency=agency, source_name=source_name, title=title, url=full,
                           row=row.get_text(' ', strip=True)[:1500], detail='', errors=[]))
    return result[:30]


def enrich(c):
    try:
        markup = get(c['url'])
        c['detail'] = article_text(markup)
        for url in attachment_links(markup, c['url']):
            try:
                with requests.get(url, timeout=(25, 25), stream=True) as response:
                    response.raise_for_status()
                    data = response.raw.read(MAX_BYTES + 1, decode_content=True)
                extracted = document_text(data)
                if extracted:
                    c['detail'] += '\n' + extracted
            except Exception as e:
                c['errors'].append('attachment: ' + type(e).__name__)
    except Exception as e:
        c['errors'].append('detail: ' + type(e).__name__)
    return c


def evidence(text, pattern, fallback):
    compact = re.sub(r'\s+', ' ', text)
    m = re.search(pattern, compact, re.I)
    return compact[m.start():m.start()+260] if m else fallback


def evaluate(c, today=None):
    today = today or datetime.now(KST).date()
    title, detail = c['title'], c['detail']
    if EXCLUDE.search(title) or not FUNDING.search(title) or len(detail) < 80:
        return None
    text = title + '\n' + detail
    # Match the actual title, so navigation and attachment boilerplate cannot qualify a call.
    programs = matches(title, PROGRAMS)
    fields = research_matches(title) + matches(title, ('수소', '에너지소재', '에너지 소재'))
    if not programs and not fields:
        return None
    start, deadline, deadline_evidence = application_period(detail)
    if deadline and deadline < today:
        return None
    announced_dates = dates(c['row'])
    announced = max((d for d in announced_dates if d <= today), default=None)
    if not deadline and not (announced and (today-announced).days <= 21):
        return None
    eligibility = evidence(detail, r'신청\s*자격|지원\s*대상(?!\s*연구개발과제)|신청\s*대상|연구책임자\s*자격', '자격 정보 미확인')
    host = evidence(detail, r'주관\s*연구개발기관|주관\s*기관|소속\s*기관|기관\s*승인', '주관기관·국내 소속 조건 미확인')
    amount = evidence(detail, r'지원\s*규모|지원\s*기간|과제\s*기간|연구비\s*규모', '지원 규모·기간 미확인')
    early = bool(matches(title, PROGRAMS[:14]) or matches(title, ('해외연수', '국외연수', '복귀·유치', '복귀유치')))
    # No claim of personal eligibility until residency/host/appointment requirements are checked.
    category = '개인·신진 연구자 지원 (자격 확인 필요)' if early else '기관·공동연구형 (국내 PI·주관기관 조건 확인)'
    priority = '우선 검토' if early else '협력·향후 임용 참고'
    if not deadline:
        priority = '일정 확인 필요'
    fingerprint = hashlib.sha256('|'.join([title, str(deadline), eligibility, host, amount]).encode()).hexdigest()
    key = hashlib.sha256(canonical_url(c['url']).encode()).hexdigest()[:24]
    return dict(kind='funding', key=key, fingerprint=fingerprint, title=title,
                institution=c['agency'], url=canonical_url(c['url']), deadline=deadline.isoformat() if deadline else None,
                priority=priority, category=category, fields=list(fields or programs),
                eligibility=eligibility, host=host, amount=amount, deadline_evidence=deadline_evidence,
                action='국외 체류·국내 소속·박사학위 경과연수·기수혜 제한을 공고문에서 대조',
                errors=c['errors'])


def collect():
    health, candidates = [], []
    def source(entry):
        agency, name, url = entry
        try:
            markup = get(url)
            found = candidates_from_page(agency, name, url, markup)
            # IRIS has server-rendered first pages; fetch a second page and upcoming calls.
            if agency == 'IRIS':
                for suffix in ('?pageIndex=2', '?ancmPrg=ancmPre'):
                    try:
                        found += candidates_from_page(agency, name, url, get(url + suffix))
                    except Exception:
                        pass
            return found, dict(source=agency + ' ' + name, url=url, count=len(found), status='ok' if found else 'no_matching_links', errors=[])
        except Exception as e:
            return [], dict(source=agency + ' ' + name, url=url, count=0, status='failed', errors=[type(e).__name__ + ': ' + str(e)[:250]])
    with ThreadPoolExecutor(max_workers=5) as pool:
        for found, h in pool.map(source, SOURCES):
            candidates.extend(found)
            health.append(h)
    unique = {c['url']:c for c in candidates}
    with ThreadPoolExecutor(max_workers=5) as pool:
        detailed = list(pool.map(enrich, list(unique.values())[:80]))
    for h in health:
        h['detail_failures'] = sum(bool(c['errors']) for c in detailed if c['agency'] in h['source'])
    return [op for c in detailed if (op := evaluate(c))], health


def main():
    # Compatibility entry point uses the same single delivery/state pipeline.
    from tools.research_monitor import main as run
    return run()


if __name__ == '__main__':
    raise SystemExit(main())
