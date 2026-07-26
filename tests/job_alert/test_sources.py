from tools.job_alert.sources import SOURCES, SourceKind


def test_university_and_company_monitoring_sources_are_present() -> None:
    # Given
    names = {source.name for source in SOURCES}

    # When
    required = {
        "Hibrain",
        "POSTECH",
        "SNU",
        "Korea University",
        "Yonsei University",
        "Sungkyunkwan University",
        "Hanyang University",
        "Samsung Careers",
        "LG Careers",
        "SK Materials Careers",
        "Hanwha Careers",
        "Lotte Careers",
    }

    # Then
    assert required <= names


def test_source_inventory_has_all_career_intelligence_categories() -> None:
    # Given
    kinds = {source.kind for source in SOURCES}

    # When
    names = [source.name for source in SOURCES]
    urls = [source.url.rstrip("/").casefold() for source in SOURCES]

    # Then
    assert kinds == {
        SourceKind.GOVERNMENT,
        SourceKind.UNIVERSITY,
        SourceKind.COMPANY,
        SourceKind.AGGREGATOR,
    }
    assert len(names) == len(set(names))
    assert len(urls) == len(set(urls))
