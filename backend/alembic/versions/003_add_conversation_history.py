"""Add conversation_history table

Revision ID: 003
Revises: 002
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create conversation_history table"""
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_history_user_id', 'conversation_history', ['user_id'])
    op.create_index('ix_conversation_history_created_at', 'conversation_history', ['created_at'])
    op.create_index(
        'ix_conversation_history_user_id_created_at',
        'conversation_history',
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )


def downgrade():
    """Drop conversation_history table"""
    op.drop_index('ix_conversation_history_user_id_created_at', table_name='conversation_history')
    op.drop_index('ix_conversation_history_created_at', table_name='conversation_history')
    op.drop_index('ix_conversation_history_user_id', table_name='conversation_history')
    op.drop_table('conversation_history')
