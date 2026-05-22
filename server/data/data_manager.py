import asyncio
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from shutil import rmtree
from uuid import UUID

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.sections.sections_manager import SectionsManager
from server.app.api.v1.topics.topics import TopicBlockRenderedContent, TopicRawContent, TopicRenderedContent
from server.app.api.v1.topics.topics_manager import TopicsManager


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
        topic_raw_content_root = topic_raw_content.root

        async def process_block(
                index: int,
                block,
        ) -> tuple[int, TopicBlockRenderedContent]:
            if block.type == "markdown":
                return index, TopicBlockRenderedContent.model_construct(
                    type="html-compatible text",
                    rendered_content=block.raw_content,
                )

            elif block.type == "uml":
                block_rendered_content_filename = f"{uuid.uuid4()}.png"
                block_rendered_content_path = topic_path / block_rendered_content_filename

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.convert_plantuml_to_png,
                    block.raw_content,
                    block_rendered_content_path,
                )

                return index, TopicBlockRenderedContent.model_construct(
                    type="png",
                    rendered_content=block_rendered_content_filename,
                )

            elif block.type == "latex":
                block_rendered_content_filename = f"{uuid.uuid4()}.pdf"
                block_rendered_content_path = topic_path / block_rendered_content_filename

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.compile_latex_to_pdf,
                    block.raw_content,
                    block_rendered_content_path,
                )

                return index, TopicBlockRenderedContent.model_construct(
                    type="pdf",
                    rendered_content=block_rendered_content_filename,
                )

            else:
                raise ValueError(
                    f"Неизвестный тип блока: {block.type}",
                )

        # Создаём все задачи с сохранением индексов
        tasks = [
            process_block(
                i,
                block,
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

        topic_rendered_content = [result[1] for result in results]

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
            (temp_plantuml.with_suffix(
                '.png',
            )).unlink(
                missing_ok=True,
            )

    @staticmethod
    def _extract_missing_packages(
            error_output: str,
    ) -> set[str]:
        missing_packages = set()

        patterns = [
            r"! LaTeX Error: File `([^']+)' not found",
            r"! LaTeX Error: No file `([^']+)'",
            r"Package.*?Error:.*?`([^']+)' not found",
            r"! I can't find file `([^']+)'",
        ]

        for pattern in patterns:
            matches = re.findall(
                pattern,
                error_output,
                re.IGNORECASE,
            )
            for match in matches:
                package = match.replace(
                    '.sty',
                    '',
                ).replace(
                    '.cls',
                    '',
                )
                # Очищаем от лишних символов
                package = re.sub(
                    r'[^\w\-]',
                    '',
                    package,
                )
                if package and len(
                        package,
                ) > 1:
                    missing_packages.add(
                        package,
                    )

        return missing_packages

    @staticmethod
    def _install_latex_packages(
            packages: list[str],
    ) -> None:
        if not packages:
            return

        subprocess.run(
            ['tlmgr', 'update', '--list'],
            capture_output=True,
            text=True,
        )

        for package in packages:
            try:
                subprocess.run(
                    ['tlmgr', 'install', package],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(
                        ['tlmgr', 'install', f'texlive-{package}'],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except subprocess.CalledProcessError:
                    pass

    def compile_latex_to_pdf(
            self,
            latex_string: str,
            output_filepath: Path,
            max_retries: int = 3,
    ) -> None:
        tex_file = output_filepath.with_suffix(
            '.tex',
        )
        with open(
                tex_file,
                'w',
                encoding='utf-8',
        ) as f:
            f.write(
                latex_string,
            )

        attempt = 0
        success = False
        generated_pdf = None

        try:
            while attempt < max_retries and not success:
                try:
                    result = subprocess.run(
                        [
                            'pdflatex',
                            '-interaction=nonstopmode',
                            '-halt-on-error',
                            tex_file.name,
                        ],
                        cwd=tex_file.parent,
                        check=False,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        generated_pdf = tex_file.with_suffix(
                            '.pdf',
                        )
                        if generated_pdf.exists():
                            success = True
                            break
                        else:
                            raise FileNotFoundError(
                                "PDF файл не был сгенерирован",
                            )

                    missing_packages = self._extract_missing_packages(
                        result.stderr,
                    )

                    if missing_packages:
                        self._install_latex_packages(
                            list(
                                missing_packages,
                            ),
                        )
                        attempt += 1
                        continue
                    else:
                        raise ValueError(
                            f"Ошибка компиляции LaTeX:\n{result.stderr}",
                        )

                except subprocess.CalledProcessError as e:
                    raise RuntimeError(
                        f"Ошибка выполнения pdflatex: {e.stderr}",
                    )

        finally:
            files_to_clean = [
                tex_file,
                tex_file.with_suffix(
                    '.aux',
                ),
                tex_file.with_suffix(
                    '.log',
                ),
                tex_file.with_suffix(
                    '.out',
                ),
                tex_file.with_suffix(
                    '.toc',
                ),
                tex_file.with_suffix(
                    '.lof',
                ),
                tex_file.with_suffix(
                    '.lot',
                ),
                tex_file.with_suffix(
                    '.pdf',
                ),
            ]

            for file_path in files_to_clean:
                file_path.unlink(
                    missing_ok=True,
                )

        if success and generated_pdf and generated_pdf.exists():
            generated_pdf.rename(
                output_filepath,
            )
        else:
            raise RuntimeError(
                f"Не удалось скомпилировать документ после {max_retries} попыток",
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
