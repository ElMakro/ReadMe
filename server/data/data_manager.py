import asyncio
import json
import os
import subprocess
import uuid
from pathlib import Path
from shutil import rmtree, copy2
from tempfile import mkdtemp
from uuid import UUID

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import TopicBlockRenderedContent, TopicRawContent, TopicRenderedContent, \
    ContentCompilationError, BlockCompilationError, TopicBlockRawContent
from server.app.api.v1.topics.topics_manager import TopicsManager


class CompilationError(
    RuntimeError,
):
    """Исключение, связанное с ошибкой компиляции контента"""

    def __init__(
            self,
            content_error: ContentCompilationError,
    ):
        self.content_error = content_error


# noinspection PyStringConversionWithoutDunderMethod
class DataManager:
    def __init__(
            self,
    ):
        self.content_path = Path(
            __file__,
        ).parent / "content"

        self.courses_manager = CoursesManager()
        self.sections_manager = SectionsManager()
        self.topics_manager = TopicsManager()

    def get_course_path(
            self,
            course_id: UUID,
    ) -> Path:
        return self.content_path / str(
            course_id,
        )

    async def get_section_path(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> Path:
        if course_id is None:
            section = await self.sections_manager.get_section_by_id(
                section_id,
            )
            course_id = section.course_id

        return self.content_path / str(
            course_id,
        ) / str(
            section_id,
        )

    async def get_topic_path(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> Path:
        if section_id is None or course_id is None:
            topic = await self.topics_manager.get_topic_by_id(
                topic_id,
            )
            section_id = topic.section_id
            course_id = topic.course_id

        return self.content_path / str(
            course_id,
        ) / str(
            section_id,
        ) / str(
            topic_id,
        )

    def create_course(
            self,
            course_id: UUID,
    ) -> None:
        course_path = self.get_course_path(
            course_id,
        )
        course_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def delete_course(
            self,
            course_id: UUID,
    ) -> None:
        course_path = self.get_course_path(
            course_id,
        )

        rmtree(
            course_path,
            ignore_errors=True,
        )

    async def create_section(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
            course_id,
        )
        section_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def delete_section(
            self,
            section_id: UUID,
            course_id: UUID | None = None,
    ) -> None:
        section_path = await self.get_section_path(
            section_id,
            course_id,
        )
        rmtree(
            section_path,
            ignore_errors=True,
        )

    async def create_topic(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        topic_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        topic_raw_content_json_path = topic_path / "raw_content.json"
        topic_raw_content_json_path.touch(
            exist_ok=True,
        )
        with open(
                topic_raw_content_json_path,
                "w",
                encoding="utf-8",
        ) as raw_content_file:
            json.dump(
                [],
                raw_content_file,
                ensure_ascii=False,
                indent=4,
            )

        topic_rendered_content_json_path = topic_path / "rendered_content.json"
        topic_rendered_content_json_path.touch(
            exist_ok=True,
        )
        with open(
                topic_rendered_content_json_path,
                "w",
                encoding="utf-8",
        ) as rendered_content_file:
            json.dump(
                [],
                rendered_content_file,
                ensure_ascii=False,
                indent=4,
            )

    async def delete_topic(
            self,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )

        rmtree(
            topic_path,
            ignore_errors=True,
        )

    async def update_topic_content(
            self,
            topic_raw_content: TopicRawContent,
            topic_id: UUID,
            section_id: UUID | None = None,
            course_id: UUID | None = None,
    ) -> None:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )

        backup_dir = None
        old_rendered_files = []

        for file_path in topic_path.iterdir():
            if file_path.suffix in ['.png', '.pdf'] and file_path.name != "raw_content.json":
                old_rendered_files.append(
                    file_path
                    )

        if old_rendered_files:
            backup_dir = Path(
                mkdtemp()
                )
            for old_file in old_rendered_files:
                copy2(
                    old_file,
                    backup_dir / old_file.name
                    )

        topic_raw_content_root = topic_raw_content.root
        compilation_errors = []

        tasks = [
            self.process_block(
                i,
                block,
                topic_path
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
                        target_file
                        )
                rmtree(
                    backup_dir,
                    ignore_errors=True
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
                ignore_errors=True
                )

        topic_rendered_content_obj = TopicRenderedContent.model_validate(
            topic_rendered_content,
        )

        topic_raw_content_json_path = topic_path / "raw_content.json"
        topic_rendered_content_json_path = topic_path / "rendered_content.json"

        with open(
                topic_raw_content_json_path,
                "w",
                encoding="utf-8",
        ) as topic_raw_content_json_file:
            json.dump(
                topic_raw_content.model_dump(),
                topic_raw_content_json_file,
                indent=4,
                ensure_ascii=False,
            )

        with open(
                topic_rendered_content_json_path,
                "w",
                encoding="utf-8",
        ) as topic_rendered_content_json_file:
            json.dump(
                topic_rendered_content_obj.model_dump(),
                topic_rendered_content_json_file,
                indent=4,
                ensure_ascii=False,
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

    async def get_topic_raw_content(
            self,
            topic_id: UUID,
            section_id: UUID | None,
            course_id: UUID | None,
    ) -> TopicRawContent:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        raw_content_file_path = topic_path / "raw_content.json"
        with open(
                raw_content_file_path,
                encoding="utf-8",
        ) as raw_content_file:
            raw_content = json.load(
                raw_content_file,
            )

        return TopicRawContent.model_validate(
            raw_content,
        )

    async def get_topic_rendered_content(
            self,
            topic_id: UUID,
            section_id: UUID | None,
            course_id: UUID | None,
    ) -> TopicRenderedContent:
        topic_path = await self.get_topic_path(
            topic_id,
            section_id,
            course_id,
        )
        rendered_content_file_path = topic_path / "rendered_content.json"
        with open(
                rendered_content_file_path,
                encoding="utf-8",
        ) as rendered_content_file:
            rendered_content = json.load(
                rendered_content_file,
            )

        return TopicRenderedContent.model_validate(
            rendered_content,
        )
