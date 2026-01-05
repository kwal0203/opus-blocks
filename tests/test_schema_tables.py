from opus_blocks.db.base import Base
import opus_blocks.models  # noqa: F401


def test_expected_tables_are_registered() -> None:
    expected = {
        "users",
        "documents",
        "spans",
        "facts",
        "manuscripts",
        "manuscript_documents",
        "paragraphs",
        "sentences",
        "sentence_fact_links",
        "runs",
        "jobs",
    }

    assert set(Base.metadata.tables.keys()) == expected
