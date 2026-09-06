"""Broad chemistry discovery; research overlap orders notices, never eligibility."""
from tools.notice_utils import CORE_FIELDS, ADJACENT_FIELDS, matches

# Do not require the literal word chemistry: departments often advertise only
# their discipline, device, or material. Keep this expansion specific to jobs.
CHEMISTRY_FIELDS = (
    '유기화학', '무기화학', '물리화학', '분석화학', '생화학', '이론화학',
    '계산화학', '응용화학', '환경화학', '의약화학', '화학교육', '화학생물학',
    '생명화학', '에너지공학', '재료공학', '재료과학', '금속재료', '세라믹',
    '환경공학', '생물공학', '바이오소재', '생체재료', '섬유', '촉매',
    '태양전지', '광전소자', '광전자', '유기전자소자', '디스플레이', '전자재료',
    '반도체소자', '배터리', '이차전지', '전지소재', '표면과학',
    'organic chemistry', 'inorganic chemistry', 'physical chemistry',
    'analytical chemistry', 'biochemistry', 'chemical biology',
    'theoretical chemistry', 'computational chemistry', 'medicinal chemistry',
    'materials engineering', 'catalysis', 'photovoltaic', 'photovoltaics',
    'solar cell', 'solar cells', 'optoelectronics', 'OFET', 'organic transistor',
    'organic transistors', 'battery', 'batteries', 'biomaterials', 'surface science',
    'macromolecular', 'conjugated polymer', 'conjugated polymers',
)
DIRECT_FIELDS = tuple(k for k in CORE_FIELDS if k not in ('계면', 'interface')) + (
    '유기화학', 'organic chemistry', '광전소자', '광전자', '유기전자소자',
    'optoelectronics', 'OFET', 'organic transistor', 'organic transistors',
    'macromolecular', 'conjugated polymer', 'conjugated polymers',
)
RELATED_FIELDS = (
    '화공', '화학공학', '신소재', '재료', '반도체', '에너지소재', '에너지 소재',
    '계면', 'interface', '센서', 'sensor', '촉매', 'catalysis', '표면과학',
    'surface science', '태양전지', 'photovoltaic', 'photovoltaics', 'solar cell',
    'solar cells', '배터리', '이차전지', 'battery', 'batteries', '디스플레이',
    'chemical engineering', 'materials science', 'materials engineering',
)
LABELS = ('전공 직접 관련', '인접·응용 분야', '화학 관련 폭넓은 검토')


def job_relevance(text):
    fields = tuple(dict.fromkeys(matches(text, CORE_FIELDS + ADJACENT_FIELDS + CHEMISTRY_FIELDS)))
    if not fields:
        return (), None
    rank = 0 if matches(text, DIRECT_FIELDS) else 1 if matches(text, RELATED_FIELDS) else 2
    return fields, rank
