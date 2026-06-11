from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.app.api.v1.topics.topics import (
    ContentCompilationError,
    TopicContent,
    TopicContentBlock,
)
from server.data.courses_resources.compilation_manager import CompilationError, CompilationManager


class TestCompilationManager:
    @pytest.fixture
    def mock_compiler_factory(self):
        factory = MagicMock()
        mock_compiler = AsyncMock()
        mock_compiler.compile.return_value = TopicContentBlock(type="markdown", content=["compiled"])
        factory.get_compiler.return_value = mock_compiler
        return factory

    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.file_exists = MagicMock(return_value=True)
        storage.list_files = MagicMock(return_value=[])
        storage.create_temp_directory = MagicMock(return_value=Path("/tmp/backup"))
        storage.delete_directory = MagicMock()
        storage.copy_file = MagicMock()
        storage.delete_file = MagicMock()
        return storage

    @pytest.fixture
    def manager(self, mock_compiler_factory, mock_storage):
        return CompilationManager(
            compiler_factory=mock_compiler_factory,
            storage=mock_storage,
        )

    @pytest.mark.asyncio
    async def test_compile_topic_success(self, manager, mock_compiler_factory, mock_storage):
        content = TopicContent(root=[
            TopicContentBlock(type="markdown", content=["# Hello"]),
            TopicContentBlock(type="latex", content=["E=mc^2"]),
        ])

        with patch("asyncio.to_thread", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            result = await manager.compile_topic(Path("/topic"), content)

        assert len(result.root) == 2
        mock_compiler_factory.get_compiler.assert_called()

    @pytest.mark.asyncio
    async def test_compile_topic_with_compilation_error(self, manager, mock_compiler_factory, mock_storage):
        mock_compiler = AsyncMock()
        mock_compiler.compile.side_effect = Exception("Compilation failed")
        mock_compiler_factory.get_compiler.return_value = mock_compiler

        content = TopicContent(root=[
            TopicContentBlock(type="plantuml", content=["@startuml\nA->B\n@enduml"])
        ])

        with patch("asyncio.to_thread", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            with pytest.raises(CompilationError) as exc_info:
                await manager.compile_topic(Path("/topic"), content)

            assert isinstance(exc_info.value.content_error, ContentCompilationError)

    @pytest.mark.asyncio
    async def test_compile_topic_with_backup_restore_on_error(self, manager, mock_compiler_factory, mock_storage):
        mock_compiler = AsyncMock()
        mock_compiler.compile.side_effect = Exception("Compilation failed")
        mock_compiler_factory.get_compiler.return_value = mock_compiler
        mock_storage.file_exists.return_value = True

        content = TopicContent(root=[
            TopicContentBlock(type="files", content=[])
        ])

        with patch("asyncio.to_thread", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            with pytest.raises(CompilationError):
                await manager.compile_topic(Path("/topic"), content)

    @pytest.mark.asyncio
    async def test_process_block_success(self, manager, mock_compiler_factory):
        mock_compiler = AsyncMock()
        expected_result = TopicContentBlock(type="markdown", content=["compiled"])
        mock_compiler.compile.return_value = expected_result
        mock_compiler_factory.get_compiler.return_value = mock_compiler

        block = TopicContentBlock(type="markdown", content=["# Hello"])

        index, result, error = await manager.process_block(0, block, Path("/topic"))

        assert index == 0
        assert result == expected_result
        assert error is None

    @pytest.mark.asyncio
    async def test_process_block_failure(self, manager, mock_compiler_factory):
        mock_compiler = AsyncMock()
        mock_compiler.compile.side_effect = Exception("Something went wrong")
        mock_compiler_factory.get_compiler.return_value = mock_compiler

        block = TopicContentBlock(type="markdown", content=["# Hello"])

        index, result, error = await manager.process_block(0, block, Path("/topic"))

        assert index == 0
        assert result is None
        assert error == "Something went wrong"
