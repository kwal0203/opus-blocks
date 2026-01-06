import opus_blocks.models  # noqa: F401
from opus_blocks.db.base import Base


def test_expected_tables_are_registered() -> None:
    expected = {
        "dead_letters",
        "alert_events",
        "metrics_snapshots",
        "users",
        "documents",
        "spans",
        "facts",
        "fact_embeddings",
        "manuscripts",
        "manuscript_documents",
        "paragraphs",
        "sentences",
        "sentence_fact_links",
        "runs",
        "jobs",
    }

    assert set(Base.metadata.tables.keys()) == expected
