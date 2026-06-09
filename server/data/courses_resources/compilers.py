import os
import subprocess
import tempfile
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import Depends

from server.app.api.v1.topics.topics import FileItem, TopicContentBlock
from server.data.resource_storage import IResourceStorage, get_courses_resource_storage


class BlockCompiler(ABC):
    @abstractmethod
    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        pass


class MarkdownCompiler(BlockCompiler):
    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        return TopicContentBlock.model_construct(
            type="markdown",
            content=block.content,
        )


class PlantUMLCompiler(BlockCompiler):
    def __init__(self, storage: IResourceStorage):
        self.storage = storage

    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        plantuml_code = block.content[0]
        image_filename = f"{uuid.uuid4()}.png"
        target_image_path = content_path / image_filename

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_puml = temp_dir_path / "diagram.puml"
            temp_png = temp_dir_path / "diagram.png"

            temp_puml.write_text(plantuml_code, encoding="utf-8")

            jar_path = os.environ.get('PLANTUML_JAR_PATH', '/opt/plantuml.jar')

            try:
                subprocess.run(
                    ['java', '-jar', jar_path, '-tpng', str(temp_puml)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Ошибка компиляции PlantUML: {e.stderr}") from e

            if not temp_png.exists():
                raise FileNotFoundError(f"PlantUML не сгенерировал PNG файл: {temp_png}")

            png_bytes = temp_png.read_bytes()
            self.storage.save_file(target_image_path, png_bytes)

        return TopicContentBlock.model_construct(
            type="image",
            content=[image_filename],
        )


class LaTeXCompiler(BlockCompiler):
    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        return TopicContentBlock.model_construct(
            type="latex",
            content=block.content,
        )


class FilesCompiler(BlockCompiler):
    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        return TopicContentBlock.model_construct(
            type="files",
            content=[
                FileItem.model_construct(
                    original_filename=element.original_filename,
                    server_filename=element.server_filename,
                )
                for element in block.content
            ],
        )


class CompilerFactory:
    def __init__(self, storage: IResourceStorage = Depends(get_courses_resource_storage)):
        self._compilers: dict[str, BlockCompiler] = {
            "markdown": MarkdownCompiler(),
            "plantuml": PlantUMLCompiler(storage=storage),
            "latex": LaTeXCompiler(),
            "files": FilesCompiler(),
        }

    def get_compiler(self, block_type: str) -> BlockCompiler:
        clean_type = block_type.strip().lower()
        compiler = self._compilers.get(clean_type)

        if compiler is None:
            raise ValueError(f"Неизвестный тип блока: '{block_type}'")
        return compiler
