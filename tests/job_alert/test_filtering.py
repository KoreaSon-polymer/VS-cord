from datetime import date
import pytest
from tools.job_alert.filtering import evaluate_posting
from tools.job_alert.models import RawPosting

TODAY = date(2026, 9, 6)
BODY = '채용분야 유기반도체 고분자 전기화학 박사학위 소지자 접수기간 2026.09.01 ~ 2026.09.20 대전'

def raw(title, text=BODY):
    return RawPosting('KRICT', title, 'https://example.test/notice?id=1', text)

@pytest.mark.parametrize('title', [
    '유기반도체 박사후연구원 채용', '정규직 전환 가능한 Post-Doc 채용',
    '전기화학 연구교수 초빙', '고분자 비전임교원 채용', '전임교원 비정년트랙 채용',
    '화학 위촉연구원 모집', '나노종합기술원 원장 초빙공고', '연수직 연구원 채용',
    '기간제 연구원 채용', '계약직 연구원 채용', '광촉매 석좌교수 초빙',
])
def test_excludes_roles_user_does_not_want(title):
    assert evaluate_posting(raw(title), TODAY) is None

@pytest.mark.parametrize('title,extra', [
    ('정규직 연구직 신규 채용',''), ('전임교원 신규 초빙',' 정년트랙'),
    ('전기화학 선임연구원 공개채용',' 고용형태 정규직'),
])
def test_accepts_permanent_and_faculty(title, extra):
    p = evaluate_posting(raw(title, BODY + extra), TODAY)
    assert p is not None and p.deadline == date(2026,9,20)
    assert p.research_fields


def test_nonregular_does_not_match_regular():
    assert evaluate_posting(raw('연구원 공개채용', BODY+' 고용형태 비정규직'), TODAY) is None


def test_culture_ai_and_admin_rejected():
    assert evaluate_posting(raw('정규직 연구원 채용', '문화기술 인공지능 접수기간 2026.09.01 ~ 2026.09.20'), TODAY) is None
    assert evaluate_posting(raw('정규직 행정원 채용', '화학과 사무보조 접수기간 2026.09.01 ~ 2026.09.20'), TODAY) is None


def test_expired_range_and_publication_day_are_not_deadline():
    assert evaluate_posting(raw('정규직 연구원 채용', BODY.replace('2026.09.20','2026.09.02')+' 임용예정일 2026.10.01'), TODAY) is None
    assert evaluate_posting(raw('정규직 연구원 채용', '유기반도체 공고일 2026.09.06 임용일 2026.10.01'), TODAY) is None
    p = evaluate_posting(raw('정규직 연구원 채용 (2026.09.06)', BODY), TODAY)
    assert p is not None and p.deadline == date(2026,9,20)


def test_rolling_permanent_role():
    assert evaluate_posting(raw('고분자 정년트랙 교수 초빙', '화학 분야 박사학위 소지자 상시채용'), TODAY) is not None
