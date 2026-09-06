from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class Source:
    name: str
    institution: str
    url: str


SOURCES: Final = (
    Source(
        "JOB-ALIO", "JOB-ALIO", "https://job.alio.go.kr/mobile2021/recruit/recruit.do"
    ),
    Source("ALIO", "ALIO", "https://www.alio.go.kr/information/informationRecruit.do"),
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
    Source("KIMM", "한국기계연구원 (KIMM)", "https://www.kimm.re.kr/sub0502"),
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
    ),
    Source(
        "GIST",
        "광주과학기술원 (GIST)",
        "https://www.gist.ac.kr/kr/html/sub06/060103.html",
    ),
    Source(
        "UNIST",
        "울산과학기술원 (UNIST)",
        "https://admu-intl.unist.ac.kr/unist/etc/notification/employment.do?mode=list",
    ),
    Source(
        "KAIST",
        "한국과학기술원 (KAIST)",
        "https://www.kaist.ac.kr/kr/html/footer/0814.html",
    ),
)

# University boards and national university notices complement institute boards.
# Each page has its own health result; configured does not imply successful coverage.
SOURCES += (
    Source("SNU", "서울대학교", "https://www.snu.ac.kr/snunow/notice/job-openings"),
    Source("POSTECH", "포항공과대학교", "https://facultyapplication.postech.ac.kr/"),
    Source("KOREA", "고려대학교", "https://invite.korea.ac.kr/recruit/community/notice.do"),
    Source("YONSEI", "연세대학교", "https://www.yonsei.ac.kr/sc/212/subview.do"),
    Source("YONSEI-faculty", "연세대학교", "https://faculty.yonsei.ac.kr/recruit/index.php?lang=ko"),
    Source("SKKU", "성균관대학교", "https://faculty.skku.edu/faculty/invite_prof/board.do"),
    Source("HANYANG", "한양대학교", "https://site.hanyang.ac.kr/web/faculty/home"),
    Source("PUSAN", "부산대학교", "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN103"),
    Source("PKNU", "국립부경대학교", "https://www.pknu.ac.kr/main/163"),
    Source("KNU", "경북대학교", "https://prad.knu.ac.kr/"),
    *(Source(f"KCUE-{page}", "대교협 전국 대학", f"https://www.kcue.or.kr/notice/sub04.php?pagenumber={page}") for page in range(1, 11)),
    *(Source(f"NST-{page}", "NST 소관 출연연", f"https://www.nst.re.kr/www/selectBbsNttList.do?bbsNo=19&key=61&pageIndex={page}") for page in range(1, 7)),
    Source("KRIBB", "한국생명공학연구원 (KRIBB)", "https://www.kribb.re.kr/kor/sub03/sub03_01_01.jsp"),
    Source("KIGAM", "한국지질자원연구원 (KIGAM)", "https://www.kigam.re.kr/board.es?mid=a10705030000&bid=0029"),
    Source("KFRI", "한국식품연구원 (KFRI)", "https://www.kfri.re.kr/web/board/13/postList"),
)
