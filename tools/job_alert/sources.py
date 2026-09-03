from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class SourceKind(StrEnum):
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    COMPANY = "company"
    AGGREGATOR = "aggregator"


@dataclass(frozen=True, slots=True)
class Source:
    name: str
    institution: str
    url: str
    kind: SourceKind = SourceKind.GOVERNMENT


SOURCES: Final = (
    Source(
        "JOB-ALIO",
        "JOB-ALIO",
        "https://job.alio.go.kr/mobile2021/recruit/recruit.do",
        SourceKind.AGGREGATOR,
    ),
    Source("ALIO", "ALIO", "https://www.alio.go.kr", SourceKind.AGGREGATOR),
    Source(
        "KRICT",
        "한국화학연구원 (KRICT)",
        "https://www.krict.re.kr/prog/jobOffer/kor/sub04_04_02_01/list.do",
    ),
    Source(
        "KIST",
        "한국과학기술연구원 (KIST)",
        "https://www.kist.re.kr/ko/notice/employment-announcement.do",
    ),
    Source(
        "KIMS",
        "한국재료연구원 (KIMS)",
        "https://www.kims.re.kr/v17/bbx/board.php?bx_table=03_05&page=1",
    ),
    Source(
        "KIER",
        "한국에너지기술연구원 (KIER)",
        "https://www.kier.re.kr/board?menuId=MENU00459&pageNum=1&rowCnt=20",
    ),
    Source("KIMM", "한국기계연구원 (KIMM)", "https://www.kimm.re.kr"),
    Source("ETRI", "한국전자통신연구원 (ETRI)", "https://etri.fairy.im"),
    Source(
        "KRISS",
        "한국표준과학연구원 (KRISS)",
        "https://www.kriss.re.kr/board.es?bid=0006&mid=a10502020000",
    ),
    Source(
        "KBSI",
        "한국기초과학지원연구원 (KBSI)",
        "https://www.kbsi.re.kr/board?boardId=BOARD00086&menuId=MENU002051102000000",
    ),
    Source(
        "KISTI",
        "한국과학기술정보연구원 (KISTI)",
        "https://www.kisti.re.kr/notifications/post/recruit",
    ),
    Source(
        "KITECH",
        "한국생산기술연구원 (KITECH)",
        "https://www.kitech.re.kr/communication/recruit",
    ),
    Source(
        "KERI",
        "한국전기연구원 (KERI)",
        "https://www.keri.re.kr/kor/contents/open-01.do?etc1=663",
    ),
    Source(
        "KICT",
        "한국건설기술연구원 (KICT)",
        "https://www.kict.re.kr/announcementRecruitWeb/getAnnouncementRecruitList.es?mid=a10503020000",
    ),
    Source(
        "KAERI",
        "한국원자력연구원 (KAERI)",
        "https://kaeri.re.kr/board?menuId=MENU00428&pageNum=1&rowCnt=20",
    ),
    Source(
        "IBS",
        "기초과학연구원 (IBS)",
        "https://www.ibs.re.kr/prog/recruit/kor/sub04_01/list.do",
    ),
    Source(
        "DGIST",
        "대구경북과학기술원 (DGIST)",
        "https://www.dgist.ac.kr/kr/html/sub05/050106.html",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "GIST",
        "광주과학기술원 (GIST)",
        "https://www.gist.ac.kr/kr/html/sub06/060103.html",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "UNIST",
        "울산과학기술원 (UNIST)",
        "https://admu-intl.unist.ac.kr/unist/etc/notification/employment.do?mode=list",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "KAIST",
        "한국과학기술원 (KAIST)",
        "https://www.kaist.ac.kr/kr/html/footer/0814.html",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Hibrain",
        "Hibrain academic recruitment",
        "https://www.hibrain.net/recruitment/recruits",
        SourceKind.AGGREGATOR,
    ),
    Source(
        "POSTECH",
        "포항공과대학교 (POSTECH)",
        "https://chem.postech.ac.kr/",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "SNU",
        "서울대학교 (Seoul National University)",
        "https://www.snu.ac.kr/",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Korea University",
        "고려대학교 (Korea University)",
        "https://www.korea.ac.kr/bbs/ko/55/artclList.do",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Yonsei University",
        "연세대학교 (Yonsei University)",
        "https://graduate.yonsei.ac.kr/research/index.do",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Sungkyunkwan University",
        "성균관대학교 (Sungkyunkwan University)",
        "https://www.skku.edu/",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Hanyang University",
        "한양대학교 (Hanyang University)",
        "https://site.hanyang.ac.kr/web/faculty",
        SourceKind.UNIVERSITY,
    ),
    Source(
        "Samsung Careers",
        "Samsung Electronics / SAIT / Samsung SDI",
        "https://www.samsungcareers.com/",
        SourceKind.COMPANY,
    ),
    Source(
        "LG Careers",
        "LG Chem / LG Energy Solution",
        "https://careers.lg.com/",
        SourceKind.COMPANY,
    ),
    Source(
        "SK Materials Careers",
        "SK materials",
        "https://careers.sk-materials.com/",
        SourceKind.COMPANY,
    ),
    Source(
        "OCI Careers",
        "OCI",
        "https://www.oci.co.kr/",
        SourceKind.COMPANY,
    ),
    Source(
        "Hanwha Careers",
        "Hanwha Solutions",
        "https://www.hanwhain.com/web/index.do",
        SourceKind.COMPANY,
    ),
    Source(
        "Kolon Careers",
        "Kolon",
        "https://dream.kolon.com/",
        SourceKind.COMPANY,
    ),
    Source(
        "Lotte Careers",
        "Lotte Chemical",
        "https://recruit.lotte.co.kr/",
        SourceKind.COMPANY,
    ),
)
