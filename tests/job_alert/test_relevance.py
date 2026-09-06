from datetime import date
import pytest
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.models import RawPosting
from tools.job_alert.scraper import forwarded_notice, _candidate_links
from tools.job_alert.sources import Source
from tools.research_monitor import to_opportunity, notification_events, render


def posting(field, institution='국내 지역대학교', title='전임교원 신규 초빙'):
    return evaluate_posting(RawPosting(institution, field + ' ' + title, 'https://example.test/' + field,
        f'모집분야 {field} 정년트랙 박사학위 소지자 접수기간 2026.09.01 ~ 2026.09.20'), date(2026,9,6))


@pytest.mark.parametrize('field', ['무기화학', '분석화학', '생화학', '이론화학', '화학교육', 'biochemistry', 'medicinal chemistry', '섬유', '환경공학'])
def test_broad_chemistry_is_retained_without_core_specialism(field):
    p = posting(field)
    assert p is not None
    assert p.fit_score == 50


def test_direct_then_adjacent_then_broad_in_digest():
    ps = [posting('분석화학'), posting('이차전지'), posting('유기반도체')]
    events = notification_events([to_opportunity(p) for p in ps], {'records': {}}, date(2026,9,6))
    assert [e['op']['relevance_rank'] for e in events] == [0, 1, 2]
    text = render(events, [], date(2026,9,6)).text_body
    assert '전공 직접 관련' in text and '화학 관련 폭넓은 검토' in text


def test_institute_name_is_not_a_whitelist():
    assert posting('유기반도체', '새로운 국내 출연연', '정규직 연구원 신규 채용')
    assert posting('국문학') is None


def test_same_title_at_different_institutions_is_not_deduplicated():
    ops = [to_opportunity(posting('유기반도체', name)) for name in ('가대학교', '나대학교')]
    ops[1]['key'] = 'different-institution-url'
    events = notification_events(ops, {'records': {}}, date(2026,9,6))
    assert len(events) == 2


def test_nst_follows_original_notice_not_navigation():
    source = Source('NST-1', 'NST 소관 출연연', 'https://www.nst.re.kr/')
    markup = '''<nav><a href="https://unrelated.test">채용공고</a></nav>
    <table><tr><th>소관기관</th><td>한국지질자원연구원</td></tr>
    <tr><th>주소 링크</th><td><a href="https://www.kigam.re.kr/board.es?act=view&amp;list_no=42">원문</a></td></tr></table>'''
    institution, url = forwarded_notice(source, markup)
    assert institution == '한국지질자원연구원' and 'list_no=42' in url
    assert forwarded_notice(source, '<a href="https://unrelated.test">메뉴</a>') is None


def test_kfri_clickable_row_is_parsed_without_javascript_execution():
    source = Source('KFRI', '한국식품연구원', 'https://www.kfri.re.kr/web/board/13/postList')
    markup = '''<table><tr onclick="location.href='/web/board/13/123'"><td class="tit_td">2026 정규직 연구원 채용 공고</td></tr></table>'''
    links = _candidate_links(source, markup)
    assert len(links) == 1 and links[0][1] == 'https://www.kfri.re.kr/web/board/13/123'
