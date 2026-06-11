#!/usr/bin/env python3
import asyncio
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import click
from sqlalchemy import or_, select, text

sys.path.insert(0, "/content")

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.config.db_dependency import DBDependency
from server.config.settings import settings
from server.database.models import Users
from server.enums.role import Role

BACKUP_DIR = Path("/backups")
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "false").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_KEEP_DAYS = int(os.getenv("BACKUP_KEEP_DAYS", "7"))


def wait_for_db():
    print("Checking database connection...")
    db_dependency = DBDependency()

    async def _check():
        try:
            async with db_dependency.db_session() as session:
                await session.execute(text("SELECT 1"))
                print("Database is ready!")
                return True
        except Exception as e:
            print(f"Waiting for PostgreSQL... ({str(e)})")
            return False

    while True:
        try:
            if asyncio.run(_check()):
                break
        except Exception:
            pass
        time.sleep(2)


def get_alembic_config():
    from alembic.config import Config
    config_path = os.getenv("ALEMBIC_CONFIG", "/content/alembic.ini")
    alembic_cfg = Config(config_path)
    sync_url = settings.db_settings.db_url.replace("+asyncpg", "")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    return alembic_cfg


async def create_admin_user(nickname: str = None, email: str = None, password: str = None):
    if nickname is None:
        nickname = os.getenv("DEFAULT_ADMIN_NICKNAME")
    if email is None:
        email = os.getenv("DEFAULT_ADMIN_EMAIL")
    if password is None:
        password = os.getenv("DEFAULT_ADMIN_PASSWORD")

    if not all([nickname, email, password]):
        print("Admin credentials not fully provided. Skipping admin creation.")
        return False

    auth_handler = AuthHandler()
    hashed_password = await auth_handler.get_hashed_password(password)

    db_dependency = DBDependency()
    async with db_dependency.db_session() as session:
        stmt = select(Users).where(or_(Users.nickname == nickname, Users.email == email))
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Admin user '{nickname}' already exists. Skipping creation.")
            return True

        admin_id = uuid.uuid4()
        now = datetime.now()

        admin_user = Users(
            id=admin_id,
            nickname=nickname,
            email=email,
            password=hashed_password,
            role=Role.ADMIN,
            created_at=now,
            updated_at=now
        )
        session.add(admin_user)
        await session.commit()
        print(f"Admin user '{nickname}' created successfully!")
        return True


def list_backups():
    if not BACKUP_DIR.exists():
        print("Backup directory not found.")
        return []

    backups = sorted(BACKUP_DIR.glob("*.sql.gz"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not backups:
        print("No backups found.")
        return []

    print("\nAvailable backups:")
    print("-" * 60)
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {i}. {backup.name} ({size:.2f} MB) - {mtime}")
    print("-" * 60)
    return backups


def clean_old_backups():
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now() - timedelta(days=BACKUP_KEEP_DAYS)
    deleted_count = 0

    for backup in BACKUP_DIR.glob("*.sql.gz"):
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        if mtime < cutoff:
            backup.unlink()
            deleted_count += 1
            print(f"Deleted old backup: {backup.name}")

    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old backup(s)")


def create_backup(name: str = None, auto_cleanup: bool = True):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if name:
        filename = f"{name}.sql.gz"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.sql.gz"

    backup_path = BACKUP_DIR / filename
    print(f"Creating backup: {filename}")

    cmd = [
        "pg_dump",
        "-h", settings.db_settings.db_host,
        "-p", str(settings.db_settings.db_port),
        "-U", settings.db_settings.db_user,
        "-d", settings.db_settings.db_name,
        "-Fc"
    ]

    env = {**os.environ, "PGPASSWORD": settings.db_settings.db_password.get_secret_value()}

    try:
        with open(backup_path, "wb") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, check=False)

        if result.returncode == 0:
            size = backup_path.stat().st_size / (1024 * 1024)
            print(f"Backup created: {filename} ({size:.2f} MB)")

            if auto_cleanup:
                clean_old_backups()

            return True
        else:
            print(f"Backup failed: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"Backup failed: {e}")
        return False


async def run_scheduled_backups():
    if not BACKUP_ENABLED:
        print("Automatic backups are disabled (BACKUP_ENABLED=false)")
        return

    print(f"Automatic backups enabled. Interval: {BACKUP_INTERVAL_HOURS} hours")
    print(f"Backups will be kept for {BACKUP_KEEP_DAYS} days")

    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled backup...")
            create_backup(auto_cleanup=True)
            await asyncio.sleep(BACKUP_INTERVAL_HOURS * 3600)
        except asyncio.CancelledError:
            print("Scheduled backups stopped.")
            break
        except Exception as e:
            print(f"Error in scheduled backup: {e}")
            await asyncio.sleep(60)


def restore_backup(backup_name: str = None):
    if backup_name is None:
        backups = list_backups()
        if not backups:
            return False
        print("\nEnter backup number or name:")
        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                backup_name = backups[idx].name
            else:
                print("Invalid selection.")
                return False
        else:
            backup_name = choice

    backup_path = BACKUP_DIR / backup_name if not backup_name.startswith("/") else Path(backup_name)

    if not backup_path.exists():
        print(f"Backup not found: {backup_name}")
        return False

    print(f"Restoring from backup: {backup_path.name}")
    print("WARNING: This will OVERWRITE the current database!")
    print("All existing data will be lost.")

    response = input("Are you sure? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return False

    temp_db = f"restore_temp_{uuid.uuid4().hex[:8]}"
    env = {**os.environ, "PGPASSWORD": settings.db_settings.db_password.get_secret_value()}

    try:
        subprocess.run([
            "createdb", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user, temp_db
        ], env=env, check=True, capture_output=True)

        subprocess.run([
            "pg_restore", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            "-d", temp_db, "-c", str(backup_path)
        ], env=env, check=True, capture_output=True)

        subprocess.run([
            "dropdb", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user, settings.db_settings.db_name
        ], env=env, check=True, capture_output=True)

        subprocess.run([
            "createdb", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user, settings.db_settings.db_name
        ], env=env, check=True, capture_output=True)

        subprocess.run([
            "pg_restore", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            "-d", settings.db_settings.db_name, str(backup_path)
        ], env=env, check=True, capture_output=True)

        subprocess.run([
            "dropdb", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user, temp_db
        ], env=env, check=True, capture_output=True)

        print("Backup restored successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"Restore failed: {e}")
        return False


def do_status():
    from alembic import command
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg, verbose=True)


def do_upgrade():
    from alembic import command
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully!")
    asyncio.run(create_admin_user())


def do_downgrade(revision=None):
    from alembic import command
    alembic_cfg = get_alembic_config()
    target = revision if revision else "-1"
    command.downgrade(alembic_cfg, target)
    print(f"Rolled back to {target}")


def do_revision(message=None):
    from alembic import command
    alembic_cfg = get_alembic_config()
    msg = message if message else "auto_generated"
    command.revision(alembic_cfg, autogenerate=True, message=msg)
    print(f"Created new migration: {msg}")


def do_history():
    from alembic import command
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg, verbose=True)


def do_check():
    from alembic import command
    alembic_cfg = get_alembic_config()
    try:
        command.check(alembic_cfg)
        print("Database is up to date")
    except Exception as e:
        print(f"Migrations are needed: {e}")


@click.group()
def cli():
    pass


@cli.command()
def wait():
    wait_for_db()


@cli.command()
def shell():
    subprocess.call([
        "psql", "-h", settings.db_settings.db_host,
        "-p", str(settings.db_settings.db_port),
        "-U", settings.db_settings.db_user,
        "-d", settings.db_settings.db_name
    ], env={**os.environ, "PGPASSWORD": settings.db_settings.db_password.get_secret_value()})


@cli.command()
@click.option("--nickname", prompt=True, help="Admin nickname")
@click.option("--email", prompt=True, help="Admin email")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Admin password")
def create_admin(nickname, email, password):
    asyncio.run(create_admin_user(nickname, email, password))


@cli.command()
def status():
    do_status()


@cli.command()
def upgrade():
    do_upgrade()


@cli.command()
@click.argument("revision", required=False)
def downgrade(revision):
    do_downgrade(revision)


@cli.command()
@click.argument("message", required=False)
def revision(message):
    do_revision(message)


@cli.command()
def history():
    do_history()


@cli.command()
def check():
    do_check()


@cli.command()
def auto():
    wait_for_db()
    do_upgrade()


async def _async_auto_backup():
    backup_task = asyncio.create_task(run_scheduled_backups())

    interactive_thread = threading.Thread(target=interactive_mode, daemon=True)
    interactive_thread.start()

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("\nShutting down scheduled backups...")
        backup_task.cancel()
        await asyncio.gather(backup_task, return_exceptions=True)


@cli.command()
def auto_backup():
    wait_for_db()
    try:
        asyncio.run(_async_auto_backup())
    except KeyboardInterrupt:
        print("\nGoodbye!")


@cli.group()
def backup():
    pass


@backup.command()
def list():
    list_backups()


@backup.command()
@click.argument("name", required=False)
def create(name):
    create_backup(name)


@backup.command()
@click.argument("backup_name", required=False)
def restore(backup_name):
    restore_backup(backup_name)


@backup.command()
def clean():
    clean_old_backups()


def interactive_mode():
    while True:
        print("\n" + "=" * 50)
        print("     Database Administration Menu")
        print("=" * 50)
        print("\n  1) Migration Management")
        print("  2) Backup Management")
        print("  3) Create Admin User")
        print("  4) Connect to Database")
        print("  5) Backup Status")
        print("  0) Exit")
        print()

        choice = input("Select option [0-5]: ").strip()

        if choice == "1":
            while True:
                print("\n=== Migration Management ===")
                print("  1) Show current status")
                print("  2) Apply all pending migrations")
                print("  3) Create new migration")
                print("  4) Rollback to a revision")
                print("  5) Show migration history")
                print("  6) Check if migrations needed")
                print("  0) Return")

                subchoice = input("\nSelect option [0-6]: ").strip()

                if subchoice == "1":
                    do_status()
                    input("\nPress Enter to continue...")
                elif subchoice == "2":
                    do_upgrade()
                    input("\nPress Enter to continue...")
                elif subchoice == "3":
                    msg = input("Migration message (optional): ").strip()
                    do_revision(msg if msg else None)
                    input("\nPress Enter to continue...")
                elif subchoice == "4":
                    rev = input("Revision to rollback to (optional): ").strip()
                    do_downgrade(rev if rev else None)
                    input("\nPress Enter to continue...")
                elif subchoice == "5":
                    do_history()
                    input("\nPress Enter to continue...")
                elif subchoice == "6":
                    do_check()
                    input("\nPress Enter to continue...")
                elif subchoice == "0":
                    break
                else:
                    print("Invalid option!")
                    input("\nPress Enter to continue...")

        elif choice == "2":
            while True:
                print("\n=== Backup Management ===")
                print("  1) List backups")
                print("  2) Create backup")
                print("  3) Restore backup")
                print("  4) Clean old backups")
                print("  0) Return")

                subchoice = input("\nSelect option [0-4]: ").strip()

                if subchoice == "1":
                    list_backups()
                    input("\nPress Enter to continue...")
                elif subchoice == "2":
                    name = input("Backup name (optional): ").strip()
                    create_backup(name if name else None)
                    input("\nPress Enter to continue...")
                elif subchoice == "3":
                    restore_backup()
                    input("\nPress Enter to continue...")
                elif subchoice == "4":
                    clean_old_backups()
                    input("\nPress Enter to continue...")
                elif subchoice == "0":
                    break
                else:
                    print("Invalid option!")
                    input("\nPress Enter to continue...")

        elif choice == "3":
            print("\n=== Create Admin User ===")
            nickname = input("Nickname: ").strip()
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            asyncio.run(create_admin_user(nickname, email, password))
            input("\nPress Enter to continue...")

        elif choice == "4":
            shell()

        elif choice == "5":
            print("\n=== Backup Status ===")
            print(f"Automatic backups: {'ENABLED' if BACKUP_ENABLED else 'DISABLED'}")
            print(f"Backup interval: {BACKUP_INTERVAL_HOURS} hours")
            print(f"Backup retention: {BACKUP_KEEP_DAYS} days")
            print(f"Backup directory: {BACKUP_DIR}")

            backups = list(BACKUP_DIR.glob("*.sql.gz"))
            if backups:
                sizes = [b.stat().st_size for b in backups]
                total_size = sum(sizes) / (1024 * 1024)
                print(f"Total backups: {len(backups)}")
                print(f"Total size: {total_size:.2f} MB")
            else:
                print("No backups found")
            input("\nPress Enter to continue...")

        elif choice in ["0", "q", "Q"]:
            print("\nGoodbye!")
            os._exit(0)

        else:
            print("Invalid option!")
            input("\nPress Enter to continue...")


def main():
    if len(sys.argv) > 1:
        cli()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
