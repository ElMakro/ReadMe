"""Add_trigger_for_approved_application

Revision ID: bcb481288096
Revises: 159ba5b4da76
Create Date: 2026-05-24 17:03:41.091587

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from server.enums.application_status import ApplicationStatus

# revision identifiers, used by Alembic.
revision: str = "bcb481288096"
down_revision: Union[str, Sequence[str], None] = "159ba5b4da76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        CREATE OR REPLACE FUNCTION add_professor_if_application_approved()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = '{ApplicationStatus.APPROVED.name}' AND OLD.status != '{ApplicationStatus.APPROVED.name}' THEN
                INSERT INTO professors_details (id, name, surname, patronymic)
                VALUES (NEW.id, NEW.name, NEW.surname, NEW.patronymic)
                ON CONFLICT (id) DO NOTHING;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER add_professor_on_application_approval
        AFTER UPDATE OF status ON professors_applications
        FOR EACH ROW
        EXECUTE FUNCTION add_professor_if_application_approved();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS add_professor_on_application_approval ON professors_applications")
    op.execute("DROP FUNCTION IF EXISTS add_professor_if_application_approved()")
