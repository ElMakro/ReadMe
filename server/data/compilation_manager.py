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
    async def compile_content(
            self,
            topic_path: Path,
            topic_raw_content: TopicRawContent,
    ) -> TopicRenderedContent:
        backup_dir = None
        old_rendered_files = []

        for file_path in topic_path.iterdir():
            if file_path.suffix in ['.png', '.pdf'] and file_path.name != "raw_content.json":
                old_rendered_files.append(
                    file_path,
                )

        if old_rendered_files:
            backup_dir = Path(
                mkdtemp(),
            )
            for old_file in old_rendered_files:
                copy2(
                    old_file,
                    backup_dir / old_file.name,
                )

        topic_raw_content_root = topic_raw_content.root
        compilation_errors = []

        tasks = [
            self.process_block(
                i,
                block,
                topic_path,
            )
            for i, block in enumerate(
                topic_raw_content_root,
            )
        ]

        results = await asyncio.gather(
            *tasks,
        )

        results.sort(
            key=lambda
                x: x[0],
        )

        topic_rendered_content = []
        for index, result, error in results:
            if error:
                compilation_errors.append(
                    BlockCompilationError(
                        block_index=index,
                        error=error,
                    ),
                )
            elif result is not None:
                topic_rendered_content.append(
                    result,
                )

        if compilation_errors:
            if backup_dir and backup_dir.exists():
                for backup_file in backup_dir.iterdir():
                    target_file = topic_path / backup_file.name
                    copy2(
                        backup_file,
                        target_file,
                    )
                rmtree(
                    backup_dir,
                    ignore_errors=True,
                )

            raise CompilationError(
                ContentCompilationError.model_validate(
                    compilation_errors,
                ),
            )

        for file_path in old_rendered_files:
            if file_path.exists():
                file_path.unlink()

        if backup_dir and backup_dir.exists():
            rmtree(
                backup_dir,
                ignore_errors=True,
            )

        return TopicRenderedContent.model_validate(
            topic_rendered_content,
        )

    async def process_block(
            self,
            index: int,
            block: TopicBlockRawContent,
            content_path: Path,
    ) -> tuple[int, TopicBlockRenderedContent | None, str | None]:
        try:
            if block.type == "markdown":
                return index, TopicBlockRenderedContent.model_construct(
                    type="markdown",
                    rendered_content=block.raw_content,
                ), None

            elif block.type == "uml":
                block_rendered_content_filename = f"{uuid.uuid4()}.png"
                block_rendered_content_path = content_path / block_rendered_content_filename

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.convert_plantuml_to_png,
                    block.raw_content,
                    block_rendered_content_path,
                )

                return index, TopicBlockRenderedContent.model_construct(
                    type="file",
                    rendered_content=block_rendered_content_filename,
                ), None

            elif block.type == "latex":
                return index, TopicBlockRenderedContent.model_construct(
                    type="latex",
                    rendered_content=block.raw_content,
                ), None

            else:
                return index, None, f"Неизвестный тип блока: {block.type}"

        except Exception as e:
            return index, None, str(
                e,
            )

    @staticmethod
    def convert_plantuml_to_png(
            plantuml_string: str,
            output_filepath: Path,
    ) -> None:
        file_stem = output_filepath.stem

        temp_plantuml = output_filepath.parent / f"{file_stem}.puml"
        with open(
                temp_plantuml,
                'w',
        ) as temp_plantuml_file:
            temp_plantuml_file.write(
                plantuml_string,
            )

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
