"""Initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2024-09-20 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("users_email_uq", "users", ["email"], unique=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_type IN ('PDF')", name="documents_source_type_check"),
        sa.CheckConstraint(
            "status IN ('UPLOADED','EXTRACTING_FACTS','FACTS_READY','FAILED_PARSE','FAILED_EXTRACTION')",
            name="documents_status_check",
        ),
    )
    op.create_index("documents_owner_idx", "documents", ["owner_id"], unique=False)
    op.create_index("documents_owner_hash_uq", "documents", ["owner_id", "content_hash"], unique=True)

    op.create_table(
        "spans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(start_char IS NULL AND end_char IS NULL) OR (start_char <= end_char)",
            name="spans_char_bounds_check",
        ),
    )
    op.create_index("spans_document_page_idx", "spans", ["document_id", "page"], unique=False)

    op.create_table(
        "facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "span_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("spans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "qualifiers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_uncertain", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_type IN ('PDF','MANUAL')", name="facts_source_type_check"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="facts_confidence_check"),
        sa.CheckConstraint(
            "created_by IN ('LIBRARIAN','USER')",
            name="facts_created_by_check",
        ),
        sa.CheckConstraint(
            "(source_type = 'PDF' AND document_id IS NOT NULL) OR (source_type = 'MANUAL')",
            name="facts_pdf_document_check",
        ),
    )
    op.create_index("facts_owner_idx", "facts", ["owner_id"], unique=False)
    op.create_index("facts_document_idx", "facts", ["document_id"], unique=False)
    op.create_index("facts_source_type_idx", "facts", ["source_type"], unique=False)

    op.create_table(
        "manuscripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("manuscripts_owner_idx", "manuscripts", ["owner_id"], unique=False)

    op.create_table(
        "manuscript_documents",
        sa.Column(
            "manuscript_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("manuscripts.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    op.create_table(
        "paragraphs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "manuscript_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("manuscripts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("intent", sa.Text(), nullable=False),
        sa.Column("spec_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "allowed_fact_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("latest_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "section IN ('Introduction','Methods','Results','Discussion')",
            name="paragraphs_section_check",
        ),
        sa.CheckConstraint(
            "status IN ('CREATED','GENERATING','NEEDS_REVISION','VERIFIED','PENDING_VERIFY','FAILED_GENERATION')",
            name="paragraphs_status_check",
        ),
    )
    op.create_index("paragraphs_manuscript_idx", "paragraphs", ["manuscript_id"], unique=False)
    op.create_index("paragraphs_status_idx", "paragraphs", ["status"], unique=False)

    op.create_table(
        "sentences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "paragraph_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paragraphs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("sentence_type", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_user_edited", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("supported", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "verifier_failure_modes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("verifier_explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("\"order\" >= 1", name="sentences_order_check"),
        sa.CheckConstraint(
            "sentence_type IN ('topic','evidence','conclusion','transition')",
            name="sentences_type_check",
        ),
        sa.UniqueConstraint("paragraph_id", "order", name="sentences_paragraph_order_uq"),
    )
    op.create_index("sentences_paragraph_idx", "sentences", ["paragraph_id"], unique=False)
    op.create_index("sentences_supported_idx", "sentences", ["supported"], unique=False)

    op.create_table(
        "sentence_fact_links",
        sa.Column(
            "sentence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sentences.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "fact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("facts.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="sentence_fact_links_score_check",
        ),
    )
    op.create_index("sentence_fact_links_fact_idx", "sentence_fact_links", ["fact_id"], unique=False)

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "paragraph_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paragraphs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("run_type", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("input_hash", sa.Text(), nullable=False),
        sa.Column("inputs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("outputs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("token_prompt", sa.Integer(), nullable=True),
        sa.Column("token_completion", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "run_type IN ('LIBRARIAN','WRITER','VERIFIER','REWRITER')",
            name="runs_type_check",
        ),
    )
    op.create_index("runs_paragraph_idx", "runs", ["paragraph_id"], unique=False)
    op.create_index("runs_document_idx", "runs", ["document_id"], unique=False)
    op.create_index("runs_type_idx", "runs", ["run_type"], unique=False)
    op.create_index("runs_trace_idx", "runs", ["trace_id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "progress",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "job_type IN ('EXTRACT_FACTS','GENERATE_PARAGRAPH','VERIFY_PARAGRAPH','REGENERATE_SENTENCES')",
            name="jobs_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')",
            name="jobs_status_check",
        ),
    )
    op.create_index("jobs_target_idx", "jobs", ["target_id"], unique=False)
    op.create_index("jobs_status_idx", "jobs", ["status"], unique=False)

    op.create_foreign_key(
        "paragraphs_latest_run_fk",
        "paragraphs",
        "runs",
        ["latest_run_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("paragraphs_latest_run_fk", "paragraphs", type_="foreignkey")

    op.drop_index("jobs_status_idx", table_name="jobs")
    op.drop_index("jobs_target_idx", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("runs_trace_idx", table_name="runs")
    op.drop_index("runs_type_idx", table_name="runs")
    op.drop_index("runs_document_idx", table_name="runs")
    op.drop_index("runs_paragraph_idx", table_name="runs")
    op.drop_table("runs")

    op.drop_index("sentence_fact_links_fact_idx", table_name="sentence_fact_links")
    op.drop_table("sentence_fact_links")

    op.drop_index("sentences_supported_idx", table_name="sentences")
    op.drop_index("sentences_paragraph_idx", table_name="sentences")
    op.drop_table("sentences")

    op.drop_index("paragraphs_status_idx", table_name="paragraphs")
    op.drop_index("paragraphs_manuscript_idx", table_name="paragraphs")
    op.drop_table("paragraphs")

    op.drop_table("manuscript_documents")

    op.drop_index("manuscripts_owner_idx", table_name="manuscripts")
    op.drop_table("manuscripts")

    op.drop_index("facts_source_type_idx", table_name="facts")
    op.drop_index("facts_document_idx", table_name="facts")
    op.drop_index("facts_owner_idx", table_name="facts")
    op.drop_table("facts")

    op.drop_index("spans_document_page_idx", table_name="spans")
    op.drop_table("spans")

    op.drop_index("documents_owner_hash_uq", table_name="documents")
    op.drop_index("documents_owner_idx", table_name="documents")
    op.drop_table("documents")

    op.drop_index("users_email_uq", table_name="users")
    op.drop_table("users")
