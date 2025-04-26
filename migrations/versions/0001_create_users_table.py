"""create users table

Revision ID: 0001
Revises: None
Create Date: 2023-10-10 12:00:00

"""

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, unique=True),
        sa.Column('google_id', sa.String, nullable=False, unique=True),
        sa.Column('email', sa.String, nullable=False),
        sa.Column('name', sa.String),
        sa.Column('profile_picture', sa.String),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )


def downgrade() -> None:
    op.drop_table('users')
