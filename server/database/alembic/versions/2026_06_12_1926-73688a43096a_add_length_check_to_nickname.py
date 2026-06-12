"""Add length check to nickname

Revision ID: 73688a43096a
Revises: 655526612d8c
Create Date: 2026-06-12 19:26:14.617731

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from server.config.constants import MIN_USER_NAME_LENGTH, MAX_USER_NAME_LENGTH

# revision identifiers, used by Alembic.
revision: str = "73688a43096a"
down_revision: Union[str, Sequence[str], None] = "655526612d8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_check_constraint(
        "nickname_length_check",
        "users",
        f'LENGTH(nickname) BETWEEN {MIN_USER_NAME_LENGTH} AND {MAX_USER_NAME_LENGTH}'
    )

def downgrade():
    op.drop_constraint("nickname_length_check", "users", type_='check')
