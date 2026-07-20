"""add newsletter, trending, api key tables and columns

Revision ID: a1b2c3d4e5f6
Revises: c8519a37f567
Create Date: 2026-07-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c8519a37f567'
branch_labels = None
depends_on = None


def upgrade():
    # Phase 5: Trending Topics
    op.create_table('trending_topic',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('article_count', sa.Integer(), server_default='0'),
        sa.Column('score', sa.Float(), server_default='0'),
        sa.Column('is_flagged', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('trending_topic', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_trending_topic_topic'), ['topic'], unique=False)
        batch_op.create_index(batch_op.f('ix_trending_topic_is_flagged'), ['is_flagged'], unique=False)

    # Phase 6: Newsletter log
    op.create_table('newsletter_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_url', sa.String(length=512), nullable=False),
        sa.Column('article_title', sa.String(length=512)),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('status', sa.String(length=20), server_default='success'),
        sa.Column('error_message', sa.Text()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('newsletter_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_newsletter_log_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_newsletter_log_article_url'), ['article_url'], unique=False)

    # Phase 6: Add newsletter columns to user_preference
    with op.batch_alter_table('user_preference', schema=None) as batch_op:
        batch_op.add_column(sa.Column('newsletter_opt_in', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        batch_op.add_column(sa.Column('digest_frequency', sa.String(length=20), server_default='daily'))

    # Phase 7: API Keys
    op.create_table('api_key',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=100)),
        sa.Column('rate_limit_tier', sa.String(length=20), server_default='free', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_key_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_api_key_key_hash'), ['key_hash'], unique=True)

    # Phase 7: API Key Usage log
    op.create_table('api_key_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=255)),
        sa.Column('method', sa.String(length=10)),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_key.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('api_key_usage', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_key_usage_api_key_id'), ['api_key_id'], unique=False)


def downgrade():
    with op.batch_alter_table('api_key_usage', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_key_usage_api_key_id'))
    op.drop_table('api_key_usage')

    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_key_key_hash'))
        batch_op.drop_index(batch_op.f('ix_api_key_user_id'))
    op.drop_table('api_key')

    with op.batch_alter_table('user_preference', schema=None) as batch_op:
        batch_op.drop_column('digest_frequency')
        batch_op.drop_column('newsletter_opt_in')

    with op.batch_alter_table('newsletter_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_newsletter_log_article_url'))
        batch_op.drop_index(batch_op.f('ix_newsletter_log_user_id'))
    op.drop_table('newsletter_log')

    with op.batch_alter_table('trending_topic', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_trending_topic_is_flagged'))
        batch_op.drop_index(batch_op.f('ix_trending_topic_topic'))
    op.drop_table('trending_topic')
