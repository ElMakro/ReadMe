import asyncio
from pathlib import Path
from shutil import copy2, rmtree
from tempfile import mkdtemp

from fastapi import Depends

from server.app.api.v1.topics.topics import (
    BlockCompilationError,
    ContentCompilationError,
    TopicContent,
    TopicContentBlock,
)
from server.data.courses_resources.compilers import CompilerFactory


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
    def __init__(self, compiler_factory: CompilerFactory = Depends(CompilerFactory)):
        self.compiler_factory = compiler_factory

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
            compiler = self.compiler_factory.get_compiler(block.type)
            result = await compiler.compile(block, content_path)
            return index, result, None
        except Exception as e:
            return index, None, str(e)
