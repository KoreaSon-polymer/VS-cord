"""Check clearly stated qualifications against the known completed doctorate."""

import re
from typing import Final

QUALIFICATION: Final = re.compile(
    r"^(?:\d+[.)]\s*)?(?:공통\s*)?(?:지원\s*(?:자격|요건)|응시\s*자격|"
    r"공통\s*자격|학위\s*요건|필수\s*(?:요건|자격|조건)?|"
    r"minimum\s+qualifications?|eligibility|required\s+qualifications?)"
    r"\s*[:\uFF1A]?\s*",
    re.IGNORECASE,
)
END_SECTION: Final = re.compile(
    r"^(?:\d+[.)]\s*)?(?:접수\s*(?:기간|일정|방법|마감)|지원\s*기간|제출\s*서류|전형|채용\s*(?:기간|분야)|"
    r"모집\s*분야|담당\s*업무|직무\s*내용|근무\s*(?:조건|형태)|"
    r"application\s+(?:period|procedure))",
    re.IGNORECASE,
)
PREFERRED: Final = re.compile(
    r"우대|가점|선호|\bpreferred\b|\bdesirable\b|advantage",
    re.IGNORECASE,
)
MANDATORY: Final = re.compile(
    r"필수|반드시|최소|\bmust\b|\brequired\b|한함|(?:자|사람)만\s*지원",
    re.IGNORECASE,
)
DOCTORATE: Final = re.compile(
    r"(?:\(?\s*(?:관련|해당)\s*(?:연구\s*)?(?:분야|전공)\s*\)?\s*(?:의\s*)?)?"
    r"(?:박사\s*학위\s*(?:소지자?|보유자?|취득자?|이상)|"
    r"(?:a\s+)?(?:ph\.?\s?d\.?|doctorate|doctoral\s+degree)"
    r"(?:\s+in\s+(?:a|the)\s+(?:relevant|related)\s+(?:field|discipline))?)"
    r"[\s.]*",
    re.IGNORECASE,
)
RESTRICTION: Final = re.compile(
    r"경력|경험|실적|논문|학술지|게재|국적|병역|면제|보훈|장애인|"
    r"자격증|자격\s*소지|면허|재직|소속|거주|어학|토익|TOEIC|TOEFL|"
    r"\d+\s*(?:세|년|개월|편|점)|experience|publications?|papers?|citizenship|licen[cs]e",
    re.IGNORECASE,
)
EXCLUSION: Final = re.compile(
    r"지원(?:을)?\s*(?:불가|할\s*수\s*없)|(?:취득|졸업)\s*예정자\s*(?:에\s*한함|만)",
)


def eligibility_notes(text: str) -> tuple[str, ...]:
    """Hold unknown mandatory criteria for review instead of assuming they are met."""
    in_requirements = False
    in_preferences = False
    doctorate_found = False
    additional_conditions = False
    for raw_line in text.splitlines():
        line = raw_line.strip(" \t•○●ㆍ-")
        if not line:
            continue
        label = QUALIFICATION.match(line)
        if label:
            in_requirements, in_preferences = True, False
            line = line[label.end() :]
        if END_SECTION.search(line):
            in_requirements, in_preferences = False, False
        preference = PREFERRED.search(line)
        if preference and preference.start() == 0:
            in_requirements, in_preferences = False, True
            continue
        if in_preferences and not MANDATORY.search(line):
            continue
        if preference:
            prefix = line[: preference.start()]
            parts = re.split(r"[,;(]|\s+\|\s+", prefix)
            line = " ".join(parts[:-1]) if len(parts) > 1 else ""
        line = line.strip()
        if DOCTORATE.fullmatch(line):
            doctorate_found = True
        elif (
            (line and in_requirements)
            or EXCLUSION.search(line)
            or (MANDATORY.search(line) and RESTRICTION.search(line))
        ):
            additional_conditions = True
    if not doctorate_found:
        return ("지원자격에서 관련 박사학위 요건을 확인하지 못함",)
    if additional_conditions:
        return ("별도 필수 경력·연구실적·지원 제한을 대조해야 함",)
    return ()
