from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from server.app.api.v1.topics.topics import FileItem, TopicContentBlock
from server.data.courses_resources.compilers import (
    CompilerFactory,
    FilesCompiler,
    LaTeXCompiler,
    MarkdownCompiler,
    PlantUMLCompiler,
)


class TestMarkdownCompiler:
    @pytest.mark.asyncio
    async def test_compile_returns_same_block(self):
        compiler = MarkdownCompiler()
        block = TopicContentBlock(type="markdown", content=["# Hello"])

        result = await compiler.compile(block, Path("/tmp"))

        assert result.type == "markdown"
        assert result.content == ["# Hello"]


class TestPlantUMLCompiler:
    @pytest.fixture
    def mock_storage(self):
        storage = MagicMock()
        storage.save_file = MagicMock()
        return storage

    @pytest.mark.asyncio
    async def test_compile_success(self, mock_storage, tmp_path):
        compiler = PlantUMLCompiler(storage=mock_storage)
        block = TopicContentBlock(type="plantuml", content=["@startuml\nA->B\n@enduml"])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_bytes", return_value=b"fake_png"):
                    result = await compiler.compile(block, tmp_path)

        assert result.type == "image"
        assert len(result.content) == 1
        assert result.content[0].endswith(".png")
        mock_storage.save_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_compile_raises_error_on_subprocess_failure(self, mock_storage, tmp_path):
        compiler = PlantUMLCompiler(storage=mock_storage)
        block = TopicContentBlock(type="plantuml", content=["bad code"])

        with patch("subprocess.run", side_effect=CalledProcessError(1, "java", stderr="Compilation error")):
            with pytest.raises(RuntimeError, match="Ошибка компиляции PlantUML"):
                await compiler.compile(block, tmp_path)

    @pytest.mark.asyncio
    async def test_compile_raises_error_when_png_not_generated(self, mock_storage, tmp_path):
        compiler = PlantUMLCompiler(storage=mock_storage)
        block = TopicContentBlock(type="plantuml", content=["@startuml\nA->B\n@enduml"])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(FileNotFoundError, match="PlantUML не сгенерировал PNG файл"):
                    await compiler.compile(block, tmp_path)


class TestLaTeXCompiler:
    @pytest.mark.asyncio
    async def test_compile_returns_same_block(self):
        compiler = LaTeXCompiler()
        block = TopicContentBlock(type="latex", content=["E = mc^2"])

        result = await compiler.compile(block, Path("/tmp"))

        assert result.type == "latex"
        assert result.content == ["E = mc^2"]


class TestFilesCompiler:
    @pytest.mark.asyncio
    async def test_compile_converts_to_file_items(self):
        compiler = FilesCompiler()
        block = TopicContentBlock(
            type="files",
            content=[
                FileItem(original_filename="test.txt", server_filename="uuid.txt")
            ]
        )

        result = await compiler.compile(block, Path("/tmp"))

        assert result.type == "files"
        assert len(result.content) == 1
        assert result.content[0].original_filename == "test.txt"
        assert result.content[0].server_filename == "uuid.txt"


class TestCompilerFactory:
    @pytest.fixture
    def mock_storage(self):
        return MagicMock()

    def test_get_compiler_returns_markdown_compiler(self, mock_storage):
        factory = CompilerFactory(storage=mock_storage)
        compiler = factory.get_compiler("markdown")
        assert isinstance(compiler, MarkdownCompiler)

    def test_get_compiler_returns_plantuml_compiler(self, mock_storage):
        factory = CompilerFactory(storage=mock_storage)
        compiler = factory.get_compiler("plantuml")
        assert isinstance(compiler, PlantUMLCompiler)

    def test_get_compiler_returns_latex_compiler(self, mock_storage):
        factory = CompilerFactory(storage=mock_storage)
        compiler = factory.get_compiler("latex")
        assert isinstance(compiler, LaTeXCompiler)

    def test_get_compiler_returns_files_compiler(self, mock_storage):
        factory = CompilerFactory(storage=mock_storage)
        compiler = factory.get_compiler("files")
        assert isinstance(compiler, FilesCompiler)

    def test_get_compiler_raises_error_for_unknown_type(self, mock_storage):
        factory = CompilerFactory(storage=mock_storage)
        with pytest.raises(ValueError, match="Неизвестный тип блока:"):
            factory.get_compiler("unknown")
