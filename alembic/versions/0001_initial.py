"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-08-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # talks
    op.create_table(
        "talks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("talk_type", sa.String(), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("speaker_names", sa.JSON(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("last_synced", sa.DateTime(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        sa.Column("type_specific_data", sa.JSON(), nullable=True),
        sa.Column("search_vector", sa.Text(), nullable=True, index=True),
        sa.Column("auto_tags", sa.JSON(), nullable=True),
        sa.UniqueConstraint("source_type", "source_id", name="uq_talk_source"),
    )

    # taxonomies
    op.create_table(
        "taxonomies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # taxonomy_values
    op.create_table(
        "taxonomy_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "taxonomy_id", sa.Integer(), sa.ForeignKey("taxonomies.id"), nullable=False
        ),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # talk_taxonomy_values association
    op.create_table(
        "talk_taxonomy_values",
        sa.Column("talk_id", sa.String(), sa.ForeignKey("talks.id"), primary_key=True),
        sa.Column(
            "taxonomy_value_id",
            sa.Integer(),
            sa.ForeignKey("taxonomy_values.id"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_talk_taxonomy_unique",
        "talk_taxonomy_values",
        ["talk_id", "taxonomy_value_id"],
        unique=True,
    )

    # sync_status
    op.create_table(
        "sync_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(), unique=True, nullable=False),
        sa.Column("last_sync_time", sa.DateTime()),
        sa.Column("last_successful_sync", sa.DateTime()),
        sa.Column("sync_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Optional PG-only GIN index on search
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_talks_search_vector_gin ON talks USING gin (to_tsvector('english', search_vector));"
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_talks_search_vector_gin;")

    op.drop_table("sync_status")
    op.drop_index("ix_talk_taxonomy_unique", table_name="talk_taxonomy_values")
    op.drop_table("talk_taxonomy_values")
    op.drop_table("taxonomy_values")
    op.drop_table("taxonomies")
    op.drop_table("talks")
