import os
import subprocess
from pathlib import Path
from shutil import rmtree
from uuid import UUID

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.sections.sections_manager import SectionsManager
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
        if section_id is None:
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

    def convert_plantuml_to_png(
            self,
            plantuml_string: str,
            output_filename: str,
    ) -> Path:
        output_path = self.content_path / output_filename
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Используем фиксированное имя для временного файла
        temp_puml = output_path.parent / "temp_diagram.puml"
        with open(
                temp_puml,
                'w',
        ) as f:
            f.write(
                plantuml_string,
            )

        try:
            jar_path = os.environ.get(
                'PLANTUML_JAR_PATH',
                '/opt/plantuml.jar',
            )

            subprocess.run(
                ['java', '-jar', jar_path, '-tpng', str(
                    temp_puml,
                )],
                check=True,
                capture_output=True,
                text=True,
            )

            # Точно знаем, как будет называться выходной файл
            generated_png = temp_puml.with_suffix(
                '.png',
            )

            if not generated_png.exists():
                raise FileNotFoundError(
                    f"PNG file not generated: {generated_png}",
                )

            generated_png.rename(
                output_path,
            )
            return output_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"PlantUML conversion failed: {e.stderr}",
            ) from e
        finally:
            # Чистим временные файлы
            temp_puml.unlink(
                missing_ok=True,
            )
            # Удаляем возможный PNG файл, если он остался и не был переименован
            (temp_puml.with_suffix(
                '.png',
            )).unlink(
                missing_ok=True,
            )


if __name__ == "__main__":
    uml = """
@startuml
Alice -> Bob: Gay
Bob --> Alice: Hi!
@enduml
"""
    da = DataManager()
    da.convert_plantuml_to_png(
        uml,
        "output.png",
    )
