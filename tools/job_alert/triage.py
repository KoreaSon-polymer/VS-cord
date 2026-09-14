"""Role-scoped triage. Unknown evidence is reviewed, never called permanent."""
from dataclasses import replace
from datetime import date
import hashlib
import re

from tools.notice_utils import application_period, canonical_url
from .models import RawPosting
from .relevance import job_relevance

TEMP = re.compile(r"박사\s*후|석사\s*후|포닥|post[\s.-]?doc(?:toral)?|연수직|연수연구원|위촉|기간제|비\s*정규|무기계약|비\s*전임|비\s*정년|연구교수|연구교원|겸임|객원|강사|초빙교수|특임|석좌|시간제|인턴|별정제|non[ -]tenure|research professor|adjunct|visiting professor|temporary|fixed[ -]term", re.I)
EXECUTIVE = re.compile(r"(?:원장|총장|이사장|기관장|대표이사|상임감사|소장|director|president)\s*(?:공개\s*)?(?:초빙|공모|채용|모집)", re.I)
REGULAR = re.compile(r"(?<![비무])정규\s*(?:직|연구직)|\bpermanent\b", re.I)
TENURE = re.compile(r"(?<!비)(?<!비 )정년\s*트랙|\btenure[ -]track\b", re.I)
FACULTY = re.compile(r"(?<!비)(?<!비 )전임\s*(?:직\s*)?(?:교원|교수)|교수\s*초빙|교원\s*(?:초빙|공채)|\bfaculty\b|assistant professor", re.I)
RESEARCH = re.compile(r"연구직|연구원|연구\s*분야|연구개발|\bresearch\b", re.I)
ADMIN = re.compile(r"행정(?:직|원|실무)|사무(?:직|원|보조)|시설직|조리원|간호사|생산관리|시험보조")
FIELD_LABEL = re.compile(r"모집\s*(?:분야|전공)|채용\s*분야|초빙\s*(?:분야|전공)|담당\s*(?:업무|연구)|직무\s*(?:내용|수행)|연구\s*분야|research area", re.I)
STOP_LABEL = re.compile(r"지원\s*자격|응시\s*자격|관련\s*학과|지원\s*가능\s*전공|우대\s*(?:사항|조건)|접수\s*기간|공통\s*자격|학력\s*(?:요건|조건)", re.I)
ROLE_HEADER = re.compile(r"^\s*(?:\[([A-Za-z가-힣]{0,6}[-_]?\d{1,3}(?:[-_]\d{1,3})?)\]|(?:직무|채용|분야)\s*코드\s*[:：]?\s*([A-Za-z가-힣]{0,6}[-_]?\d{1,3}(?:[-_]\d{1,3})?))", re.I)


def role_title_excluded(title):
    if EXECUTIVE.search(title):
        return True
    if not TEMP.search(title) and not re.search(r"계약직", title):
        return False
    # An explicit mixed call can contain useful roles; promotion promises cannot.
    mixed = bool((REGULAR.search(title) or TENURE.search(title)) and
                 re.search(r"및|[+/·,]|동시", title) and not re.search(r"전환|가능|예정", title))
    return not mixed


def field_context(title, body):
    """Prefer role duties. Degree eligibility lists do not establish job overlap."""
    chunks = [title]
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if FIELD_LABEL.search(line):
            part = line[FIELD_LABEL.search(line).end():]
            if len(part.strip()) < 3:
                part += " " + " ".join(lines[i+1:i+3])
            chunks.append(STOP_LABEL.split(part)[0])
    if len(chunks) == 1:
        chunks += [STOP_LABEL.split(line)[0] for line in lines
                   if not re.search(r"기관\s*소개|연구원\s*소개|우대사항|결격사유", line)]
    return "\n".join(chunks)


def qualifications(body):
    kept = []
    for line in body.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if re.search(r"허위|부정행위|결격|공란|위.?변조|시험을 무효", line):
            continue
        if re.search(r"박사|학위|경력|논문|주저자|SCIE|SCI급|학력|Ph\.?D", line, re.I):
            # Never present OCR-damaged experience as a verified requirement.
            if re.search(r"경력\s*년|후\s*년|이상\s*년", line):
                kept.append("경력 연수 추출 불완전: 원문 숫자 확인 필요")
            else:
                kept.append(line[:500])
        if len(kept) >= 3:
            break
    return " / ".join(kept) if kept else "학위·필수 경력·논문 요건 확인 필요"


def split_roles(raw):
    """Split explicit role-code blocks only. Do not infer PDF column alignment."""
    raw = replace(raw, title=re.sub(r"비\s+(?=정규|정년|전임)", "비", raw.title), text=re.sub(r"비\s+(?=정규|정년|전임)", "비", raw.text))
    lines = raw.text.splitlines()
    starts = [(i, ROLE_HEADER.match(line)) for i, line in enumerate(lines) if ROLE_HEADER.match(line)]
    if len(starts) < 2:
        return [raw]
    common = "\n".join(line for line in lines if re.search(r"접수\s*기간|접수\s*마감|제출\s*기한|온라인\s*접수", line))
    output = []
    for n, (i, match) in enumerate(starts):
        end = starts[n+1][0] if n+1 < len(starts) else len(lines)
        code = next(g for g in match.groups() if g)
        block = "\n".join(lines[i:end])
        # Each block must identify its own employment type; parent evidence must
        # not leak from administrative/permanent roles into a temporary role.
        heading = lines[i][match.end():].strip()
        output.append(replace(raw, title=heading + " 채용", text=block+"\n"+common,
                              role_id=code, parent_title=raw.title))
    return output


def uncertainty(raw):
    combined = raw.title + "\n" + raw.text
    notes = list(raw.review_notes)
    title = raw.title
    if raw.text.startswith("상세 페이지 접근 실패"):
        notes.append("상세 페이지 접근 실패")
    if TEMP.search(title) and (REGULAR.search(title) or TENURE.search(title)):
        notes.append("혼합 채용: 직무별 고용형태 분리 필요")
    if re.search(r"연구직", combined) and re.search(r"행정직|기술직|실무직", combined) and not raw.role_id:
        notes.append("통합 채용: 모집 분야·직무코드 확인 필요")
    if REGULAR.search(combined) and re.search(r"비\s*정규|무기계약|기간제", raw.text) and not raw.role_id:
        notes.append("복수 고용형태: 해당 연구직의 정규직 여부 확인 필요")
    if re.search(r"비\s*정년", combined) and TENURE.search(combined) and not raw.role_id:
        notes.append("복수 교원 트랙: 직무별 정년트랙 확인 필요")
    if FACULTY.search(combined) and not TENURE.search(combined):
        notes.append("정년트랙 여부 확인 필요")
    if not (REGULAR.search(combined) or TENURE.search(combined) or FACULTY.search(combined)):
        notes.append("정규 연구직 여부 확인 필요")
    start, deadline, evidence = application_period(raw.text, title)
    if not deadline and not re.search(r"상시|채용\s*시까지|until filled|rolling", combined, re.I):
        notes.append("접수 마감 미확인")
    fields, rank = job_relevance(field_context(title, raw.text))
    if not fields:
        notes.append("모집 분야·담당 업무의 연구 관련성 확인 필요")
    if not raw.role_id and re.search(r"\d+\s*개\s*분야|모집분야.*직무기술서.*참고", combined):
        notes.append("모집 분야별 직무기술서 확인 필요")
    return tuple(dict.fromkeys(notes))


def review_opportunity(raw, today, notes):
    fields, rank = job_relevance(field_context(raw.title, raw.text))
    _, deadline, _ = application_period(raw.text, raw.title)
    identity = canonical_url(raw.url) + ("|role:"+raw.role_id if raw.role_id else "")
    payload = "|".join((raw.title, str(deadline), *notes))
    return dict(kind="job", key=hashlib.sha256(identity.encode()).hexdigest()[:24],
        fingerprint=hashlib.sha256(payload.encode()).hexdigest(), title=raw.parent_title + " / " + raw.title if raw.parent_title else raw.title,
        institution=raw.institution, url=raw.url, role_id=raw.role_id,
        deadline=str(deadline) if deadline else None, priority="확인 필요",
        category="확인 필요 (정규직·지원 가능 판정 아님)", fields=list(fields),
        relevance="확인 필요", relevance_rank=3, eligibility=qualifications(raw.text),
        host="", amount="", action="; ".join(notes), errors=list(notes), review=True)


def classify_notice(raw, today, evaluator):
    accepted, reviews = [], []
    for role in split_roles(raw):
        if role_title_excluded(role.title):
            continue
        if not re.search(r"채용|초빙|모집|임용|recruit|position|opening", role.title, re.I):
            continue
        if re.search(r"합격자|선정결과|입찰|신규과제|지원사업", role.title):
            continue
        combined = role.title + "\n" + role.text
        if re.search(r"비\s*정년", combined) and not TENURE.search(combined):
            continue
        # Explicit nonregular role bodies with no competing permanent evidence.
        if re.search(r"(?:고용\s*형태|직종|직급)\s*[:：]?\s*(?:비\s*정규|기간제|계약직|무기계약|박사\s*후|석사\s*후|연수직)", role.text) and not (REGULAR.search(combined) or TENURE.search(combined)):
            continue
        if ADMIN.search(role.title) and not RESEARCH.search(role.title):
            continue
        _, end, _ = application_period(role.text, role.title)
        if end and end < today:
            continue
        fields, _ = job_relevance(field_context(role.title, role.text))
        # Generic faculty/institute research calls with unreadable fields must
        # remain discoverable, but unrelated explicit fields should not leak in.
        missing_document = bool(role.review_notes) or role.text.startswith("상세 페이지 접근 실패")
        generic = bool(FACULTY.search(role.title) or (REGULAR.search(role.title) and RESEARCH.search(role.title)))
        if not fields and not (generic and (missing_document or "첨부" in role.text)):
            continue
        notes = uncertainty(role)
        if notes:
            reviews.append(review_opportunity(role, today, notes))
            continue
        posting = evaluator(role, today)
        if posting:
            accepted.append(posting)
    return accepted, reviews
