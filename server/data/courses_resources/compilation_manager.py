import asyncio
from pathlib import Path

from fastapi import Depends

from server.app.api.v1.topics.topics import (
    BlockCompilationError,
    ContentCompilationError,
    TopicContent,
    TopicContentBlock,
)
from server.data.courses_resources.compilers import CompilerFactory
from server.data.resource_storage import IResourceStorage, get_courses_resource_storage


class CompilationError(RuntimeError):

    def __init__(self, content_error: ContentCompilationError):
        self.content_error = content_error


class CompilationManager:
    def __init__(
            self,
            compiler_factory: CompilerFactory = Depends(CompilerFactory),
            storage: IResourceStorage = Depends(get_courses_resource_storage)
    ):
        self.compiler_factory = compiler_factory
        self.storage = storage

    def _make_backup_sync(
            self,
            full_topic_directory_path: Path,
            new_raw_content: TopicContent
    ) -> Path | None:
        remaining_files = set()
        for block in new_raw_content.root:
            if getattr(block, 'type', None) == "files":
                for file_item in getattr(block, 'content', []):
                    server_filename = getattr(file_item, 'server_filename', None)
                    if server_filename:
                        remaining_files.add(server_filename)

        if not self.storage.file_exists(full_topic_directory_path):
            return None

        backup_directory = self.storage.create_temp_directory()

        for filepath in self.storage.list_files(full_topic_directory_path):
            if filepath.name not in remaining_files:
                self.storage.copy_file(filepath, backup_directory / filepath.name)
                self.storage.delete_file(filepath)

        return backup_directory

    def _restore_backup_sync(
            self,
            full_topic_directory_path: Path,
            backup_directory: Path
    ) -> None:
        if not backup_directory or not self.storage.file_exists(backup_directory):
            return

        for backup_file in self.storage.list_files(backup_directory):
            target_file = full_topic_directory_path / backup_file.name
            self.storage.copy_file(backup_file, target_file)

    async def compile_topic(
            self,
            full_topic_directory_path: Path,
            topic_raw_content: TopicContent
    ) -> TopicContent:
        topic_raw_content_root = topic_raw_content.root

        backup_directory = await asyncio.to_thread(
            self._make_backup_sync,
            full_topic_directory_path,
            topic_raw_content
        )

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

        try:
            if compilation_errors:
                if backup_directory:
                    await asyncio.to_thread(
                        self._restore_backup_sync,
                        full_topic_directory_path,
                        backup_directory
                    )
                raise CompilationError(
                    ContentCompilationError.model_validate(compilation_errors)
                )

            return TopicContent.model_validate(topic_rendered_content)
        finally:
            if backup_directory and self.storage.file_exists(backup_directory):
                await asyncio.to_thread(
                    lambda: self.storage.delete_directory(backup_directory)
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
