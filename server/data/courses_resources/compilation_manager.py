import asyncio
import os
import subprocess
import uuid
from pathlib import Path
from shutil import copy2, rmtree
from tempfile import mkdtemp

from fastapi import UploadFile

from server.app.api.v1.topics.topics import (
    BlockCompilationError,
    ContentCompilationError,
    TopicBlockRawContent,
    TopicBlockRenderedContent,
    TopicRawContent,
    TopicRenderedContent,
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
                    old_topic_rendered_content: TopicRenderedContent | None) -> Path | None:
        old_rendered_files = []
        backup_directory = None

        if old_topic_rendered_content is not None:
            for block in old_topic_rendered_content.root:
                if block.type in ["files", "image"]:
                    old_rendered_files.extend(
                        block.rendered_content,
                    )

        if old_rendered_files:
            backup_directory = Path(
                mkdtemp(),
            )
            for old_file in old_rendered_files:
                old_file_path = full_topic_directory_path / Path(
                    old_file,
                )
                copy2(
                    old_file_path,
                    backup_directory / old_file_path.name,
                )

            for file_path in old_rendered_files:
                full_file_path = full_topic_directory_path / file_path
                if full_file_path.exists():
                    full_file_path.unlink()

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

    async def compile_topic_content(
            self,
            full_topic_directory_path: Path,
            topic_raw_content: TopicRawContent,
            topic_files: list[UploadFile],
            old_topic_rendered_content: TopicRenderedContent | None = None,
    ) -> TopicRenderedContent:
        backup_directory = self.make_backup(full_topic_directory_path, old_topic_rendered_content)

        topic_raw_content_root = topic_raw_content.root
        compilation_errors = []

        tasks = []
        files_slice_start_index = 0
        for index, block in enumerate(topic_raw_content_root):
            if block.type in ["files"]:
                files_slice_end_index = files_slice_start_index + len(block.raw_content)
                block_files = topic_files[files_slice_start_index:files_slice_end_index]
            else:
                block_files = []

            tasks.append(
                self.process_block(index, block, block_files, full_topic_directory_path)
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

        return TopicRenderedContent.model_validate(
            topic_rendered_content,
        )

    async def process_block(
            self,
            index: int,
            block: TopicBlockRawContent,
            block_files: list[UploadFile],
            content_path: Path,
    ) -> tuple[int, TopicBlockRenderedContent | None, str | None]:
        try:
            if block.type not in ["files"] and len(block.raw_content) > 1:
                return index, None, (f"Для типа блока {block.type} ожидается один элемент в списке "
                                     f"raw_content! Получено - {len(block.raw_content)}")

            if block.type == "markdown":
                return index, TopicBlockRenderedContent.model_construct(
                    type="markdown",
                    rendered_content=block.raw_content,
                ), None

            elif block.type == "uml":
                block_rendered_content_filename = f"{uuid.uuid4()}.png"
                block_rendered_content_path = content_path / block_rendered_content_filename

                loop = asyncio.get_event_loop()
                # noinspection PyTypeChecker,PyUnresolvedReferences
                await loop.run_in_executor(
                    None,
                    self.convert_plantuml_to_png,
                    block.raw_content[0],
                    block_rendered_content_path,
                )

                return index, TopicBlockRenderedContent.model_construct(
                    type="image",
                    rendered_content=block_rendered_content_filename,
                ), None

            elif block.type == "latex":
                return index, TopicBlockRenderedContent.model_construct(
                    type="latex",
                    rendered_content=block.raw_content,
                ), None

            elif block.type == "files":
                rendered_block = self.save_files_block(content_path, block.raw_content, block_files)
                return index, rendered_block[0], rendered_block[1]

            else:
                return index, None, f"Неизвестный тип блока: {block.type}"

        except Exception as e:
            return index, None, str(
                e,
            )

    def save_files_block(self, content_path: Path, filenames: list[str], block_files: list[UploadFile]) -> tuple[
        TopicBlockRenderedContent | None, str | None]:
        result_filenames = []

        for index, filename in enumerate(filenames):
            if block_files[index].filename != filename:
                return None, (f"Названия переданных файлов должны совпадать с названиями файлов в блоке! "
                              f"Ожидалось {block_files[index].filename}, получено - {filename}")

            result_filenames.append(self.save_file(content_path, block_files[index]))

        return TopicBlockRenderedContent.model_construct(type="files", rendered_content=result_filenames), None

    def save_file(self, content_path: Path, upload_file: UploadFile) -> str:
        assert upload_file.filename is not None
        safe_filepath = self.resolve_safe_filepath(content_path, upload_file.filename)
        with open(safe_filepath, 'wb') as result_file:
            result_file.write(upload_file.file.read())

        return safe_filepath.name

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
