from quarry.web.utils import valid_dbname


PROJECTS = [
    "wiki",
    "wikibooks",
    "wikinews",
    "wikiquote",
    "wikisource",
    "wikiversity",
    "wikivoyage",
    "wiktionary",
]


def test_valid():
    """Assert that expected valid dbnames are valid."""
    for project in PROJECTS:
        for language in ["en", "de", "fr", "nds_nl", "zh_min_nan"]:
            dbname = "{}{}".format(language, project)
            assert valid_dbname(dbname) is True
            assert valid_dbname("{}_p".format(dbname)) is True

    assert valid_dbname("wikimania2005wiki") is True

    assert valid_dbname("test2wiki") is True

    assert valid_dbname("centralauth") is True
    assert valid_dbname("centralauth_p") is True

    assert valid_dbname("meta") is True
    assert valid_dbname("meta_p") is True

    assert valid_dbname("quarry") is True


def test_invalid():
    """Assert that expected invalid dbnames are invalid."""
    assert valid_dbname("") is False
    assert valid_dbname(None) is False

    assert valid_dbname("enwiki quarry") is False

    assert valid_dbname("quarry_p") is False
