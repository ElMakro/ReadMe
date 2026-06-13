#!/usr/bin/env python3
import asyncio
import os
import shutil
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

from alembic import command
from alembic.config import Config

from server.app.api.v1.auth.auth_handler import AuthHandler
from server.config.db_dependency import DBDependency
from server.config.settings import settings
from server.database.models import Users
from server.enums.role import Role

BACKUP_DIR = Path("/backups")
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "false").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_KEEP_DAYS = int(os.getenv("BACKUP_KEEP_DAYS", "7"))

BACKUP_VOLUMES = {}
for vol in os.getenv("BACKUP_VOLUMES", "readme-courses-resources,readme-users-resources").split(","):
    vol = vol.strip()
    if vol:
        BACKUP_VOLUMES[vol] = Path(f"/volumes/{vol}")


def get_alembic_config():
    config_path = os.getenv("ALEMBIC_CONFIG", "/content/alembic.ini")
    alembic_cfg = Config(config_path)
    sync_url = settings.db_settings.db_url.replace("+asyncpg", "")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    return alembic_cfg


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


def create_user_directories(user_id: uuid.UUID, nickname: str) -> bool:
    users_volume = Path("/volumes/readme-users-resources")

    if not users_volume.exists():
        print(f"  ✗ Users volume not mounted at {users_volume}")
        return False

    user_dir = users_volume / str(user_id)
    files_dir = user_dir / "files"

    try:
        user_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created user directory: {user_dir}")
        print(f"  ✓ Created files directory: {files_dir}")

        from server.data.icons_generator import IconsGenerator
        icons_generator = IconsGenerator()
        data = f"{user_id}-{nickname}"
        icon_path = user_dir / "icon.png"
        icon_path.write_bytes(icons_generator.generate_icon(data))
        print(f"  ✓ Created icon: {icon_path}")

        return True
    except Exception as e:
        print(f"  ✗ Failed to create directories: {e}")
        return False


async def create_admin_user(nickname: str = None, email: str = None, password: str = None):
    print("\n=== Creating admin user ===")

    if nickname is None:
        nickname = os.getenv("DEFAULT_ADMIN_NICKNAME")
    if email is None:
        email = os.getenv("DEFAULT_ADMIN_EMAIL")
    if password is None:
        password = os.getenv("DEFAULT_ADMIN_PASSWORD")

    if not all([nickname, email, password]):
        print("Admin credentials not fully provided. Skipping admin creation.")
        return False

    print(f"  Nickname: {nickname}")
    print(f"  Email: {email}")

    auth_handler = AuthHandler()
    hashed_password = await auth_handler.get_hashed_password(password)

    db_dependency = DBDependency()
    async with db_dependency.db_session() as session:
        stmt = select(Users).where(or_(Users.nickname == nickname, Users.email == email))
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"  Admin user '{nickname}' already exists. Skipping creation.")
            return True

        admin_id = uuid.uuid4()
        now = datetime.now()
        try:
            admin_user = Users(
                id=admin_id,
                nickname=nickname,
                email=email,
                password=hashed_password,
                role=Role.ADMIN,
                created_at=now,
                updated_at=now
            )
        except ValueError as error:
            print(f"Constraint violation: {str(error)}")
            return False

        session.add(admin_user)
        await session.commit()
        print(f"  Admin user '{nickname}' created successfully with ID: {admin_id}")

        create_user_directories(admin_id, nickname)

        return True


def backup_volume(volume_name: str, mount_path: Path, backup_path: Path) -> bool:
    print(f"  Backing up volume: {volume_name}")

    if not mount_path.exists():
        print(f"    ✗ Volume {volume_name} not mounted at {mount_path}")
        return False

    try:
        cmd = ["tar", "czf", str(backup_path), "-C", str(mount_path), "."]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            size = backup_path.stat().st_size / (1024 * 1024)
            print(f"    ✓ Volume {volume_name} backed up successfully ({size:.2f} MB)")
            return True
        else:
            print(f"    ✗ Failed to backup volume {volume_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"    ✗ Exception backing up {volume_name}: {e}")
        return False


def backup_database(backup_path: Path) -> bool:
    print("  Backing up database...")

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
            print(f"    ✓ Database backed up successfully ({size:.2f} MB)")
            return True
        else:
            print(f"    ✗ Database backup failed: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"    ✗ Database backup exception: {e}")
        return False


def create_backup(name: str = None, auto_cleanup: bool = True) -> bool:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_prefix = f"{name}_{timestamp}"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_prefix = f"backup_{timestamp}"

    backup_root = BACKUP_DIR / backup_prefix
    backup_root.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Creating full backup: {backup_prefix}")
    print(f"{'=' * 60}")

    success = True

    db_backup_path = backup_root / "database.sql.gz"
    if not backup_database(db_backup_path):
        success = False

    for volume_name, mount_path in BACKUP_VOLUMES.items():
        volume_backup_path = backup_root / f"volume_{volume_name}.tar.gz"
        if not backup_volume(volume_name, mount_path, volume_backup_path):
            success = False

    manifest_path = backup_root / "manifest.txt"
    with open(manifest_path, "w") as f:
        f.write(f"Backup created: {datetime.now().isoformat()}\n")
        f.write(f"Backup name: {backup_prefix}\n")
        f.write("Database backup: database.sql.gz\n")
        f.write(f"Volumes backed up: {', '.join(BACKUP_VOLUMES.keys())}\n")

    archive_path = BACKUP_DIR / f"{backup_prefix}.tar.gz"
    print(f"\n  Creating archive: {archive_path.name}")

    cmd = ["tar", "czf", str(archive_path), "-C", str(BACKUP_DIR), backup_prefix]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            size = archive_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ Archive created ({size:.2f} MB)")
            shutil.rmtree(backup_root)
        else:
            print(f"  ✗ Archive creation failed: {result.stderr}")
            success = False
    except Exception as e:
        print(f"  ✗ Archive creation exception: {e}")
        success = False

    if success:
        print(f"\n✓ Full backup completed successfully: {archive_path.name}")
    else:
        print("\n✗ Backup completed with errors")

    if auto_cleanup:
        clean_old_backups()

    return success


def restore_volume(volume_name: str, mount_path: Path, backup_path: Path) -> bool:
    print(f"  Restoring volume: {volume_name}")

    if not mount_path.exists():
        print(f"    ✗ Volume {volume_name} not mounted at {mount_path}")
        return False

    try:
        for item in mount_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    except Exception as e:
        print(f"    ✗ Failed to clean volume {volume_name}: {e}")
        return False

    cmd = ["tar", "xzf", str(backup_path), "-C", str(mount_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✓ Volume {volume_name} restored successfully")
            return True
        else:
            print(f"    ✗ Failed to restore volume {volume_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"    ✗ Exception restoring {volume_name}: {e}")
        return False


def restore_database_from_backup(backup_path: Path) -> bool:
    env = {**os.environ, "PGPASSWORD": settings.db_settings.db_password.get_secret_value()}

    try:
        print(f"    Terminating all connections to database {settings.db_settings.db_name}...")

        terminate_cmd = [
            "psql", "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            "-d", "postgres",
            "-c",
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{settings.db_settings.db_name}' "
            f"AND pid <> pg_backend_pid();"
        ]

        result = subprocess.run(terminate_cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print("    ✓ All connections terminated")
        else:
            print(f"    Warning when terminating connections: {result.stderr}")

        print(f"    Dropping database {settings.db_settings.db_name}...")
        result = subprocess.run([
            "dropdb", "--if-exists",
            "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            settings.db_settings.db_name
        ], env=env, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"    Warning when dropping DB: {result.stderr}")

        print(f"    Creating database {settings.db_settings.db_name}...")
        result = subprocess.run([
            "createdb",
            "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            settings.db_settings.db_name
        ], env=env, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"    ✗ Failed to create database: {result.stderr}")
            return False

        print("    Restoring from backup...")
        cmd = [
            "pg_restore",
            "-h", settings.db_settings.db_host,
            "-p", str(settings.db_settings.db_port),
            "-U", settings.db_settings.db_user,
            "-d", settings.db_settings.db_name,
            "-c",
            "--if-exists",
            str(backup_path)
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print("    ✓ Database restored successfully")
            return True
        else:
            print(f"    ✗ Database restore failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"    ✗ Database restore exception: {e}")
        return False


def restore_backup(backup_name: str = None) -> bool:
    if backup_name is None:
        backup_files = list_backups()
        if not backup_files:
            return False
        print("\nEnter backup number or name:")
        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(backup_files):
                backup_name = backup_files[idx].name
            else:
                print("Invalid selection.")
                return False
        else:
            backup_name = choice

    backup_path = BACKUP_DIR / backup_name if not backup_name.startswith("/") else Path(backup_name)

    if not backup_path.exists():
        print(f"Backup not found: {backup_name}")
        return False

    print(f"\n{'=' * 60}")
    print(f"Restoring from backup: {backup_path.name}")
    print(f"{'=' * 60}")
    print("WARNING: This will OVERWRITE the current database and volumes!")
    print("All existing data will be lost.")

    response = input("\nAre you sure? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return False

    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print("\n  Extracting archive...")
        cmd = ["tar", "xzf", str(backup_path), "-C", str(temp_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"  Failed to extract archive: {e}")
            return False

        items = os.listdir(temp_path)
        if not items:
            print("  No files found in archive")
            return False

        backup_root = temp_path / items[0]

        db_backup = backup_root / "database.sql.gz"
        if db_backup.exists():
            print("\n  Restoring database...")
            if not restore_database_from_backup(db_backup):
                print("  Database restore failed!")
                return False

        for volume_name, mount_path in BACKUP_VOLUMES.items():
            volume_backup = backup_root / f"volume_{volume_name}.tar.gz"
            if volume_backup.exists():
                print(f"\n  Restoring volume: {volume_name}")
                if not restore_volume(volume_name, mount_path, volume_backup):
                    print(f"  Failed to restore volume: {volume_name}")
                    return False

    print("\n✓ Backup restored successfully!")
    return True


def list_backups():
    if not BACKUP_DIR.exists():
        print("Backup directory not found.")
        return []

    backup_files = sorted(BACKUP_DIR.glob("*.tar.gz"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not backup_files:
        print("No backups found.")
        return []

    print("\nAvailable backups:")
    print("-" * 70)
    for i, backup_file in enumerate(backup_files, 1):
        size = backup_file.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {i}. {backup_file.name} ({size:.2f} MB) - {mtime}")
    print("-" * 70)
    return backup_files


def clean_old_backups():
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now() - timedelta(days=BACKUP_KEEP_DAYS)
    deleted_count = 0

    for backup_file in BACKUP_DIR.glob("*.tar.gz"):
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if mtime < cutoff:
            backup_file.unlink()
            deleted_count += 1
            print(f"Deleted old backup: {backup_file.name}")

    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old backup(s)")


async def run_scheduled_backups():
    if not BACKUP_ENABLED:
        print("Automatic backups are disabled (BACKUP_ENABLED=false)")
        return

    print(f"Automatic backups enabled. Interval: {BACKUP_INTERVAL_HOURS} hours")
    print(f"Backups will be kept for {BACKUP_KEEP_DAYS} days")
    print(f"Volumes to backup: {', '.join(BACKUP_VOLUMES.keys())}")

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


def do_status():
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg, verbose=True)


def do_upgrade():
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully!")
    asyncio.run(create_admin_user())


def do_downgrade(revision=None):
    alembic_cfg = get_alembic_config()
    target = revision if revision else "-1"
    command.downgrade(alembic_cfg, target)
    print(f"Rolled back to {target}")


def do_revision(message=None):
    alembic_cfg = get_alembic_config()
    msg = message if message else "auto_generated"
    command.revision(alembic_cfg, autogenerate=True, message=msg)
    print(f"Created new migration: {msg}")


def do_history():
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg, verbose=True)


def do_check():
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
            print(f"Volumes to backup: {', '.join(BACKUP_VOLUMES.keys())}")

            backup_files = list(BACKUP_DIR.glob("*.tar.gz"))
            if backup_files:
                sizes = [b.stat().st_size for b in backup_files]
                total_size = sum(sizes) / (1024 * 1024)
                print(f"Total backups: {len(backup_files)}")
                print(f"Total size: {total_size:.2f} MB")
            else:
                print("No backups found")
            input("\nPress Enter to continue...")

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
