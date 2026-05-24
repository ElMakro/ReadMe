"""Add trigger for role update

Revision ID: 159ba5b4da76
Revises: 8cc6eb13ad1e
Create Date: 2026-05-24 14:52:17.448001

"""

from typing import Sequence, Union

from alembic import op

from server.enums.role import Role

# revision identifiers, used by Alembic.
revision: str = "159ba5b4da76"
down_revision: Union[str, Sequence[str], None] = "8cc6eb13ad1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        CREATE OR REPLACE FUNCTION set_user_role_to_professor()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (SELECT role FROM users WHERE id = NEW.id) = '{Role.STUDENT.name}' THEN
                UPDATE users
                SET role = '{Role.PROFESSOR.name}'
                WHERE id = NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_user_role
        AFTER INSERT ON professors_details
        FOR EACH ROW
        EXECUTE FUNCTION set_user_role_to_professor();
    """)

    op.execute(f"""
        CREATE OR REPLACE FUNCTION reset_user_role_from_professor()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (SELECT role FROM users WHERE id = OLD.id) = '{Role.PROFESSOR.name}' THEN
                UPDATE users
                SET role = '{Role.STUDENT.name}'
                WHERE id = OLD.id;
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER downgrade_user_role
        AFTER DELETE ON professors_details
        FOR EACH ROW
        EXECUTE FUNCTION reset_user_role_from_professor();
    """)

    op.execute(f"""
        CREATE OR REPLACE FUNCTION delete_professor_if_role_changed()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.role = '{Role.STUDENT.name}' AND OLD.role != '{Role.STUDENT.name}' THEN
                DELETE FROM professors_details
                WHERE id = NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER delete_professor_on_role_change
        AFTER UPDATE OF role ON users
        FOR EACH ROW
        EXECUTE FUNCTION delete_professor_if_role_changed();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS downgrade_user_role ON professors_details")
    op.execute("DROP FUNCTION IF EXISTS reset_user_role_from_professor()")

    op.execute("DROP TRIGGER IF EXISTS update_user_role ON professors_details")
    op.execute("DROP FUNCTION IF EXISTS set_user_role_to_professor()")

    op.execute("DROP TRIGGER IF EXISTS delete_professor_on_role_change ON users")
    op.execute("DROP FUNCTION IF EXISTS delete_professor_if_role_changed()")
