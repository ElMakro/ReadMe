import asyncio
import os
import subprocess
import uuid
from pathlib import Path
from shutil import copy2, rmtree
from tempfile import mkdtemp

from server.app.api.v1.topics.topics import (
    BlockCompilationError,
    ContentCompilationError,
    FileItem,
    TopicContent,
    TopicContentBlock,
)


class CompilationError(
    RuntimeError,
):
    """Исключение, связанное с ошибкой компиляции контента"""

    def __init__(
            self,
            content_error: ContentCompilationError,
    ):
        self.content_error = content_error


class CompilationManager:
    @staticmethod
    def make_backup(full_topic_directory_path: Path,
                    new_raw_content: TopicContent) -> Path | None:
        remaining_files = []

        for block in new_raw_content.root:
            if block.type in ["files"]:
                for file_item in block.content:
                    if file_item.server_filename:
                        remaining_files.append(file_item.server_filename)

        backup_directory = Path(
            mkdtemp(),
        )

        for filename in full_topic_directory_path.iterdir():
            if filename.name not in remaining_files:
                copy2(
                    filename,
                    backup_directory / filename.name,
                )
                filename.unlink()

        return backup_directory

    @staticmethod
    def restore_backup(full_topic_directory_path: Path, backup_directory: Path) -> None:
        if backup_directory and backup_directory.exists():
            for backup_file in backup_directory.iterdir():
                target_file = full_topic_directory_path / backup_file.name
                copy2(
                    backup_file,
                    target_file,
                )
            rmtree(
                backup_directory,
                ignore_errors=True,
            )

    async def compile_topic(
            self,
            full_topic_directory_path: Path,
            topic_raw_content: TopicContent
    ) -> TopicContent:
        topic_raw_content_root = topic_raw_content.root
        backup_directory = self.make_backup(full_topic_directory_path, topic_raw_content)

        compilation_errors = []

        tasks = []
        for index, block in enumerate(topic_raw_content_root):
            tasks.append(
                self.process_block(index, block, full_topic_directory_path)
            )

        results = await asyncio.gather(*tasks)

        results.sort(key=lambda x: x[0])

        topic_rendered_content = []
        for index, result, error in results:
            if error:
                compilation_errors.append(BlockCompilationError(block_index=index, error=error))
            elif result is not None:
                topic_rendered_content.append(result)

        if compilation_errors:
            if backup_directory:
                self.restore_backup(full_topic_directory_path, backup_directory)

            raise CompilationError(
                ContentCompilationError.model_validate(
                    compilation_errors,
                ),
            )

        if backup_directory and backup_directory.exists():
            rmtree(
                backup_directory,
                ignore_errors=True,
            )

        return TopicContent.model_validate(
            topic_rendered_content,
        )

    async def process_block(
            self,
            index: int,
            block: TopicContentBlock,
            content_path: Path,
    ) -> tuple[int, TopicContentBlock | None, str | None]:
        try:
            if block.type not in ["files"] and len(block.content) > 1:
                return index, None, (f"Для типа блока {block.type} ожидается один элемент в списке "
                                     f"raw_content! Получено - {len(block.content)}")

            if block.type == "markdown":
                return index, TopicContentBlock.model_construct(
                    type="markdown",
                    content=block.content,
                ), None

            elif block.type == "plantuml":
                return index, TopicContentBlock.model_construct(
                    type="image",
                    content=[(await self.compile_plantuml(block.content[0], content_path)).name],
                ), None

            elif block.type == "latex":
                return index, TopicContentBlock.model_construct(
                    type="latex",
                    content=block.content,
                ), None

            elif block.type == "files":
                return index, TopicContentBlock.model_construct(
                    type="files",
                    content=[FileItem.model_construct(
                        original_filename=element.original_filename,
                        server_filename=element.server_filename,
                    ) for element in block.content],
                ), None

            else:
                return index, None, f"Неизвестный тип блока: {block.type}"

        except Exception as e:
            return index, None, str(
                e,
            )

    async def compile_plantuml(self, plantuml_code: str, content_path: Path) -> Path:
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
    def resolve_safe_filepath(content_path: Path, filename: str) -> Path:
        index = 1
        filename_path = Path(filename)
        result_filepath = content_path / filename
        while True:
            if not result_filepath.exists():
                break

            result_filepath = content_path / f"{filename_path.stem} ({index}){filename_path.suffix}"

        return result_filepath

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
