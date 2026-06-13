import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "/home/alexander/PycharmProjects/ReadMe")

import database_manager.database_manager as dbm

pytestmark = pytest.mark.asyncio


class TestGetAlembicConfig:
    def test_returns_config_with_sync_url(self):
        with patch.object(dbm, "settings") as mock_settings:
            mock_settings.db_settings.db_url = "postgresql+asyncpg://user:pass@localhost:5432/db"
            with patch("database_manager.database_manager.Config") as mock_config:
                magic_mock_config = MagicMock()
                mock_config.return_value = magic_mock_config

                result = dbm.get_alembic_config()

                mock_config.assert_called_once()
                magic_mock_config.set_main_option.assert_called_once_with(
                    "sqlalchemy.url", "postgresql://user:pass@localhost:5432/db"
                )
                assert result == magic_mock_config


class TestWaitForDb:
    @patch("database_manager.database_manager.DBDependency")
    @patch("database_manager.database_manager.time.sleep")
    def test_wait_for_db_success(self, mock_sleep, mock_db_dependency):
        mock_db = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_db_dependency.return_value = mock_db
        mock_db.db_session.return_value.__aenter__.return_value = mock_session

        with patch("database_manager.database_manager.asyncio.run") as mock_run:
            mock_run.return_value = True
            dbm.wait_for_db()
            assert mock_run.called


class TestCreateUserDirectories:
    def test_creates_user_directories_success(self, tmp_path):
        users_volume = tmp_path / "volumes" / "readme-users-resources"
        users_volume.mkdir(parents=True)

        with patch("database_manager.database_manager.Path") as mock_path:
            mock_path.return_value = users_volume
            result = dbm.create_user_directories(uuid.uuid4(), "testuser")
            assert result is True

    def test_returns_false_when_volume_not_mounted(self):
        with patch("database_manager.database_manager.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            result = dbm.create_user_directories(uuid.uuid4(), "test")
            assert result is False


class TestCreateAdminUser:
    @patch("database_manager.database_manager.create_user_directories")
    @patch("database_manager.database_manager.AuthHandler")
    @patch("database_manager.database_manager.DBDependency")
    async def test_creates_admin_user_success(
            self, mock_db_dependency, mock_auth_handler, mock_create_dirs
    ):
        mock_auth = AsyncMock()
        mock_auth.get_hashed_password.return_value = "hashed_pass"
        mock_auth_handler.return_value = mock_auth

        mock_session = AsyncMock()
        mock_db = MagicMock()
        mock_db.db_session.return_value.__aenter__.return_value = mock_session
        mock_db_dependency.return_value = mock_db

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("database_manager.database_manager.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda x, default=None: {
                "DEFAULT_ADMIN_NICKNAME": "admin",
                "DEFAULT_ADMIN_EMAIL": "admin@test.com",
                "DEFAULT_ADMIN_PASSWORD": "password123"
            }.get(x, default)

            result = await dbm.create_admin_user()
            assert result is True


class TestBackupDatabase:
    @patch.object(dbm, "settings")
    @patch("subprocess.run")
    def test_backup_database_success(self, mock_subprocess, mock_settings):
        mock_settings.db_settings.db_host = "localhost"
        mock_settings.db_settings.db_port = 5432
        mock_settings.db_settings.db_user = "user"
        mock_settings.db_settings.db_name = "testdb"
        mock_settings.db_settings.db_password.get_secret_value.return_value = "pass"

        mock_subprocess.return_value = MagicMock(returncode=0)

        backup_path = Path("/tmp/backup.sql.gz")
        result = dbm.backup_database(backup_path)
        assert result is True


class TestCreateBackup:
    @patch("database_manager.database_manager.backup_database")
    @patch("database_manager.database_manager.backup_volume")
    def test_create_backup_success(self, mock_backup_volume, mock_backup_db, tmp_path):
        mock_backup_db.return_value = True
        mock_backup_volume.return_value = True

        with patch("database_manager.database_manager.BACKUP_DIR", tmp_path):
            with patch("database_manager.database_manager.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
                result = dbm.create_backup(name="test_backup", auto_cleanup=False)
                assert result is True


class TestRestoreDatabaseFromBackup:
    @patch.object(dbm, "settings")
    @patch("subprocess.run")
    def test_restore_database_success(self, mock_subprocess, mock_settings):
        mock_settings.db_settings.db_host = "localhost"
        mock_settings.db_settings.db_port = 5432
        mock_settings.db_settings.db_user = "user"
        mock_settings.db_settings.db_name = "testdb"
        mock_settings.db_settings.db_password.get_secret_value.return_value = "pass"

        mock_subprocess.return_value = MagicMock(returncode=0)

        backup_path = Path("/tmp/backup.sql.gz")
        result = dbm.restore_database_from_backup(backup_path)
        assert result is True


class TestListBackups:
    def test_list_backups_when_directory_empty(self, tmp_path):
        with patch("database_manager.database_manager.BACKUP_DIR", tmp_path):
            result = dbm.list_backups()
            assert result == []

    def test_list_backups_returns_list(self, tmp_path):
        backup1 = tmp_path / "backup1.tar.gz"
        backup2 = tmp_path / "backup2.tar.gz"
        backup1.touch()
        backup2.touch()

        with patch("database_manager.database_manager.BACKUP_DIR", tmp_path):
            with patch("builtins.print"):
                result = dbm.list_backups()
                assert len(result) == 2


class TestCleanOldBackups:
    def test_cleans_backups(self, tmp_path):
        with patch("database_manager.database_manager.BACKUP_DIR", tmp_path):
            dbm.clean_old_backups()


class TestDoUpgrade:
    @patch("database_manager.database_manager.command")
    @patch("database_manager.database_manager.asyncio.run")
    @patch("database_manager.database_manager.get_alembic_config")
    def test_do_upgrade_calls_migrations(self, mock_config, mock_asyncio, mock_command):
        mock_config.return_value = MagicMock()
        dbm.do_upgrade()
        mock_command.upgrade.assert_called_once()
        mock_asyncio.assert_called_once()


class TestCLICommands:
    @patch("sys.argv", ["database_manager.py", "wait"])
    def test_wait_command(self):
        with patch("database_manager.database_manager.wait_for_db") as _:
            with patch("database_manager.database_manager.cli") as mock_cli:
                dbm.main()
                mock_cli.assert_called_once()

    @patch("sys.argv", ["database_manager.py", "shell"])
    def test_shell_command(self):
        with patch.object(dbm.settings, "db_settings") as mock_settings:
            mock_settings.db_host = "localhost"
            mock_settings.db_port = 5432
            mock_settings.db_user = "user"
            mock_settings.db_name = "testdb"
            with patch("subprocess.call") as _:
                with patch("database_manager.database_manager.cli") as mock_cli:
                    dbm.main()
                    mock_cli.assert_called_once()

    @patch("sys.argv",
           ["database_manager.py", "create-admin", "--nickname", "admin", "--email", "admin@test.com", "--password",
            "pass"])
    def test_create_admin_command(self):
        with patch("database_manager.database_manager.asyncio.run") as _:
            with patch("database_manager.database_manager.cli") as mock_cli:
                dbm.main()
                mock_cli.assert_called_once()
