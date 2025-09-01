"""Drop user_request_relations table

Revision ID: drop_user_request_relations
Revises: 09b99111e548
Create Date: 2025-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_user_request_relations'
down_revision = '09b99111e548'
branch_labels = None
depends_on = None


def upgrade():
    """Drop user_request_relations table"""
    op.drop_table('user_request_relations')


def downgrade():
    """Recreate user_request_relations table"""
    op.create_table('user_request_relations',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('request_info_id', sa.INTEGER(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )