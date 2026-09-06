from copy import deepcopy
from datetime import date
import pytest
from tools.notice_utils import canonical_url, application_period, matches, article_text
from tools.funding_monitor.monitor import candidates_from_page, evaluate
from tools.research_monitor import notification_events, mark_delivered, load_state, save_state

TODAY = date(2026,9,6)


def test_session_and_page_do_not_change_identity():
    assert canonical_url('https://www.msit.go.kr/bbs/view.do;jsessionid=abc?nttSeqNo=123&pageIndex=1') == canonical_url('https://www.msit.go.kr/bbs/view.do;jsessionid=xyz?pageIndex=2&nttSeqNo=123')
    assert canonical_url('https://x/view?id=1') != canonical_url('https://x/view?id=2')


def test_short_english_keywords_do_not_match_random_words():
    assert not matches('other topic samples', ['HER','PI','SAM'])
    assert matches('HER and n-type SAM', ['HER','SAM'])

@pytest.mark.parametrize('text,end',[
    ('접수기간 2026.09.01 ~ 2026.09.20 임용일 2026.10.01', date(2026,9,20)),
    ('원서접수 2026. 9. 1.(화) 09:00 ~ 9. 20.(일) 18:00', date(2026,9,20)),
    ('접수마감 2026.09.20까지', date(2026,9,20)),
    ('공고일 2026.09.01 임용일 2026.10.01', None),
])
def test_application_date_evidence(text,end):
    assert application_period(text)[1] == end


def test_article_removes_navigation():
    text=article_text('<nav>AI 포닥 채용 2026.10.01</nav><article><p>'+('정규 연구직 고분자 연구 ' * 10)+'</p></article><footer>다음 공고</footer>')
    assert 'AI' not in text and '다음 공고' not in text


def test_iris_onclick_is_a_real_detail_link():
    markup='''<li>공고일자 2026-09-01 <a href="" onclick="f_bsnsAncmBtinSituListForm_view('023557','ancmIng'); return false;">세종과학펠로우십 신규과제 공모</a></li>'''
    cs=candidates_from_page('IRIS','공고','https://www.iris.go.kr/contents/retrieveBsnsAncmBtinSituListView.do',markup)
    assert len(cs)==1 and cs[0]['url'].endswith('ancmId=023557')


def funding(title,detail=None):
    return dict(title=title,agency='NRF',url='https://x/notice?id=1', row='공고일자 2026-09-01',errors=[],detail=detail or ('신청자격 박사학위 취득 후 7년 이내. 지원대상 국내 연구기관 소속 연구자. 주관기관 승인 필요. 지원규모 1억원. 접수기간 2026.09.01 ~ 2026.09.20. '*2))

@pytest.mark.parametrize('title',['나노종합기술원 원장 초빙공고','신진연구 신규과제 선정결과 공고','반도체 연구장비 구매 입찰공고'])
def test_funding_is_not_jobs_results_or_procurement(title):
    assert evaluate(funding(title),TODAY) is None


def test_fellowship_kept_without_claiming_eligibility():
    op=evaluate(funding('세종과학펠로우십 신규과제 공모'),TODAY)
    assert op and '확인 필요' in op['category']
    assert op['deadline']=='2026-09-20'


def test_old_funding_is_not_recommended_because_program_matches():
    assert evaluate(funding('세종과학펠로우십 신규과제 공모',funding('x')['detail'].replace('2026.09','2025.09')),TODAY) is None


def test_delivery_state_and_reminder_are_idempotent(tmp_path):
    state=load_state(tmp_path/'state.json')
    op=evaluate(funding('세종과학펠로우십 신규과제 공모'),TODAY)
    events=notification_events([op,op],state,TODAY)
    assert len(events)==1
    # Selection alone is side-effect free. Mark only after SMTP succeeds.
    assert state['records']=={}
    mark_delivered(state,events,TODAY)
    assert notification_events([op],state,TODAY)==[]
    assert notification_events([op],state,date(2026,9,7))==[]
    reminders=notification_events([op],state,date(2026,9,13))
    assert len(reminders)==1
    mark_delivered(state,reminders,date(2026,9,13))
    assert notification_events([op],state,date(2026,9,13))==[]
    save_state(state,tmp_path/'state.json')
    assert load_state(tmp_path/'state.json')==state


def test_changed_deadline_gets_one_update(tmp_path):
    state=load_state(tmp_path/'state.json')
    op=evaluate(funding('세종과학펠로우십 신규과제 공모'),TODAY)
    mark_delivered(state,notification_events([op],state,TODAY),TODAY)
    changed=deepcopy(op);changed.update(deadline='2026-09-30',fingerprint='different')
    event=notification_events([changed],state,TODAY)
    assert len(event)==1 and event[0]['reason']=='조건·일정 변경'


def test_iris_attachment_url_and_non_tenure_body():
    from tools.notice_documents import attachment_links
    from tools.job_alert.filtering import evaluate_posting
    from tools.job_alert.models import RawPosting
    markup='''<a href="javascript:f_bsnsAncm_downloadAtchFile('abc==','x/y==','공고.hwp','2000');">공고.hwp</a>'''
    links=attachment_links(markup,'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=1')
    assert len(links)==1 and '/comm/file/fileDownload.do?' in links[0]
    assert 'atchFileId=x%2Fy%3D%3D' in links[0]
    raw=RawPosting('대학','화학 전임교원 신규채용','https://x/1','비정년트랙 화학 전공 접수기간 2026.09.01 ~ 2026.09.20')
    assert evaluate_posting(raw,TODAY) is None
