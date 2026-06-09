import asyncio
import os
import subprocess
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from server.app.api.v1.topics.topics import FileItem, TopicContentBlock


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
    async def compile(self, block: TopicContentBlock, content_path: Path) -> TopicContentBlock:
        image_path = await self._compile_plantuml(block.content[0], content_path)
        return TopicContentBlock.model_construct(
            type="image",
            content=[image_path.name],
        )

    async def _compile_plantuml(self, plantuml_code: str, content_path: Path) -> Path:
        image_filename = f"{uuid.uuid4()}.png"
        image_path = content_path / image_filename

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.convert_plantuml_to_png,
            plantuml_code,
            image_path,
        )

        return image_path

    @staticmethod
    def convert_plantuml_to_png(
            plantuml_string: str,
            output_filepath: Path,
    ) -> None:
        file_stem = output_filepath.stem

        temp_plantuml = output_filepath.parent / f"{file_stem}.puml"
        with open(temp_plantuml, 'w') as temp_plantuml_file:
            temp_plantuml_file.write(plantuml_string)

        try:
            jar_path = os.environ.get(
                'PLANTUML_JAR_PATH',
                '/opt/plantuml.jar',
            )

            subprocess.run(
                ['java', '-jar', jar_path, '-tpng', str(
                    temp_plantuml,
                )],
                check=True,
                capture_output=True,
                text=True,
            )

            generated_png = temp_plantuml.with_suffix(
                '.png',
            )

            if not generated_png.exists():
                raise FileNotFoundError(
                    f"Не найден файл PNG: {generated_png}",
                )

            generated_png.rename(
                output_filepath,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Ошибка компиляции PlantUML: {e.stderr}",
            ) from e
        finally:
            temp_plantuml.unlink(
                missing_ok=True,
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
            content=[FileItem.model_construct(
                original_filename=element.original_filename,
                server_filename=element.server_filename,
            ) for element in block.content],
        )


class CompilerFactory:
    _compilers = {
        "markdown": MarkdownCompiler(),
        "plantuml": PlantUMLCompiler(),
        "latex": LaTeXCompiler(),
        "files": FilesCompiler(),
    }

    @classmethod
    def get_compiler(cls, block_type: str) -> BlockCompiler:
        compiler = cls._compilers.get(block_type)
        if not compiler:
            raise ValueError(f"Неизвестный тип блока: {block_type}")
        return compiler
