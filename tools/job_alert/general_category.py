from typing import Final

from .taxonomy_models import KeywordCategory

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
    tier=6,
)
