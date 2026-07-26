from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class KeywordCategory:
    name: str
    keywords: tuple[str, ...]
    explanation: str
    profile_emphasis: tuple[str, ...]


POSITION_KEYWORDS: Final = (
    "박사후연구원",
    "박사후 연구원",
    "postdoctoral researcher",
    "post-doctoral researcher",
    "post-doc",
    "postdoc",
    "연구교수",
    "research professor",
    "연구과제전담교수",
    "프로젝트교수",
    "project professor",
    "faculty track",
    "책임연구원",
    "principal researcher",
    "선임연구원",
    "senior researcher",
    "전임연구원",
    "정규직 연구",
    "연구직",
    "위촉연구원",
    "석사후연구원",
    "research scientist",
    "scientist",
    "researcher",
    "연구원",
)

ORGANIC_ELECTRONICS: Final = KeywordCategory(
    name="Organic semiconductor and organic electronics",
    keywords=(
        "organic semiconductor",
        "organic electronics",
        "organic optoelectronics",
        "organic photovoltaic",
        "organic photonics",
        "conjugated polymer",
        "conjugated polymers",
        "polymer semiconductor",
        "semiconducting polymer",
        "π-conjugated polymer",
        "pi-conjugated polymer",
        "small molecule semiconductor",
        "molecular semiconductor",
        "electronic materials",
        "functional organic materials",
        "유기반도체",
        "고분자 반도체",
        "유기전자",
        "유기전자소재",
        "유기광전자",
        "유기광전소자",
        "공액고분자",
        "공액계 고분자",
        "전자소재",
        "기능성 유기소재",
    ),
    explanation=(
        "Strong overlap with organic semiconductor, conjugated-polymer, "
        "and organic-electronics experience"
    ),
    profile_emphasis=(
        "Organic semiconductor synthesis",
        "Conjugated polymer design",
        "Organic optoelectronic materials",
    ),
)

POLYMER_AND_ORGANIC_SYNTHESIS: Final = KeywordCategory(
    name="Polymer chemistry and organic materials synthesis",
    keywords=(
        "polymer synthesis",
        "polymer chemistry",
        "polymer semiconductor",
        "functional polymer",
        "advanced polymer materials",
        "macromolecular chemistry",
        "organic synthesis",
        "molecular design",
        "functional molecules",
        "organic materials",
        "soft materials",
        "hybrid materials",
        "π-conjugated materials",
        "pi-conjugated materials",
        "monomer synthesis",
        "고분자 합성",
        "고분자 화학",
        "고분자 반도체",
        "고분자 소재",
        "기능성 고분자",
        "유기합성",
        "유기소재",
        "분자설계",
        "기능성 분자",
        "소프트 소재",
        "고분자 재료",
        "단량체 합성",
    ),
    explanation=(
        "Polymer-semiconductor synthesis and organic materials chemistry "
        "experience are directly applicable"
    ),
    profile_emphasis=(
        "Polymer semiconductor synthesis",
        "Organic synthesis",
        "Molecular and monomer design",
    ),
)

ADVANCED_MATERIALS: Final = KeywordCategory(
    name="Advanced materials chemistry",
    keywords=(
        "advanced materials",
        "functional materials",
        "smart materials",
        "nanomaterials",
        "surface engineering",
        "interface engineering",
        "thin film materials",
        "coating materials",
        "materials chemistry",
        "materials science",
        "첨단소재",
        "기능성 소재",
        "나노소재",
        "표면제어",
        "계면제어",
        "박막소재",
        "코팅소재",
        "소재화학",
        "재료화학",
        "신소재",
    ),
    explanation=(
        "Advanced functional-materials design and characterization experience "
        "transfer to this research area"
    ),
    profile_emphasis=(
        "Advanced functional materials",
        "Materials characterization",
        "Surface and interface characterization",
    ),
)

ENERGY_AND_ELECTROCHEMISTRY: Final = KeywordCategory(
    name="Energy materials and electrochemistry",
    keywords=(
        "energy materials",
        "energy conversion",
        "energy storage",
        "electrochemical materials",
        "electrochemistry",
        "electrocatalysis",
        "photocatalysis",
        "photoelectrochemistry",
        "solar fuel",
        "hydrogen production",
        "hydrogen sensor",
        "water splitting",
        "fuel cell",
        "battery materials",
        "electrode materials",
        "에너지 소재",
        "에너지 변환",
        "에너지 저장",
        "전기화학 소재",
        "전기화학",
        "전기촉매",
        "광촉매",
        "광전기화학",
        "수소 생산",
        "수소생산",
        "수소 센서",
        "수전해",
        "연료전지",
        "배터리 소재",
        "전극 소재",
    ),
    explanation=(
        "Photocatalytic, photoelectrochemical, hydrogen-energy, and "
        "electrochemical-device experience can be emphasized"
    ),
    profile_emphasis=(
        "Photocatalysis and hydrogen evolution",
        "Photoelectrochemistry",
        "Electrochemical device experience",
    ),
)

SEMICONDUCTOR_DEVICE_INTERFACE: Final = KeywordCategory(
    name="Semiconductor, device, sensor, and interface",
    keywords=(
        "semiconductor materials",
        "polymer semiconductor",
        "thin film transistor",
        "tft",
        "sensor materials",
        "chemical sensor",
        "gas sensor",
        "optoelectronic device",
        "electronic device",
        "device fabrication",
        "device physics",
        "thin-film device",
        "thin film device",
        "interface physics",
        "interface engineering",
        "charge transfer",
        "charge transport",
        "carrier mobility",
        "omiec",
        "oect",
        "n-type sam",
        "반도체 소재",
        "고분자 반도체",
        "박막트랜지스터",
        "센서 소재",
        "가스센서",
        "광전자 소자",
        "광전소자",
        "전자소자",
        "소자 제작",
        "소자물리",
        "계면 물리",
        "계면 전하이동",
        "계면 전하 이동",
        "전하 이동",
    ),
    explanation=(
        "Thin-film device physics, interface engineering, and charge-transport "
        "experience align with the role"
    ),
    profile_emphasis=(
        "Thin-film device fabrication",
        "Device physics",
        "Interface engineering and charge transport",
    ),
)

GENERAL_CHEMISTRY_MATERIALS: Final = KeywordCategory(
    name="General chemistry and materials",
    keywords=(
        "chemistry",
        "material",
        "materials",
        "nanomaterial",
        "molecule",
        "catalyst",
        "catalysis",
        "synthesis",
        "analysis",
        "thin film",
        "surface",
        "interface",
        "화학",
        "재료",
        "소재",
        "신소재",
        "나노",
        "분자",
        "촉매",
        "합성",
        "분석",
        "박막",
        "표면",
        "계면",
    ),
    explanation=(
        "General chemistry and materials skills provide a transferable "
        "foundation for the advertised research"
    ),
    profile_emphasis=(
        "Materials chemistry",
        "Chemical synthesis",
        "Materials characterization",
    ),
)

CATEGORY_RULES: Final = (
    ORGANIC_ELECTRONICS,
    POLYMER_AND_ORGANIC_SYNTHESIS,
    ADVANCED_MATERIALS,
    ENERGY_AND_ELECTROCHEMISTRY,
    SEMICONDUCTOR_DEVICE_INTERFACE,
    GENERAL_CHEMISTRY_MATERIALS,
)
