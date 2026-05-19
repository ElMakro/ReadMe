from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select

from server.app.api.v1.courses.courses_manager import ObjectExistenceError
from server.app.api.v1.sections.sections import SectionIDMixin, SectionResponse, SectionsFullListResponse
from server.config.db_dependency import DBDependency
from server.database.models import Sections


class DifferentSourcesContentSwapError(
    ValueError,
):
    """Ошибка, связанная с обменом порядковыми номерами между элементами разных объектов"""


class SectionsManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ) -> None:
        self.db = db
        # self.sections_model = Sections

    async def create_section(
            self,
            course_id: UUID,
            name: str,
            description: str,
            order_number: int,
    ) -> SectionIDMixin:
        async with self.db.db_session() as session:
            new_section = Sections(
                course_id=course_id,
                name=name,
                description=description,
                order_number=order_number,
            )
            session.add(
                new_section,
            )
            await session.commit()

        return SectionIDMixin.model_construct(
            id=new_section.id,
        )

    async def check_course_have_section_with_order_number(
            self,
            course_id: UUID,
            order_number: int,
    ) -> bool:
        async with self.db.db_session() as session:
            query = select(
                Sections,
            ).where(
                and_(
                    Sections.course_id == course_id,
                    Sections.order_number == order_number,
                ),
            )

            result = await session.execute(
                query,
            )

        return bool(
            result.one_or_none(),
        )

    async def get_sections_by_course_id(
            self,
            course_id: UUID,
    ) -> SectionsFullListResponse:
        async with self.db.db_session() as session:
            query = select(
                Sections,
            ).where(
                Sections.course_id == course_id,
            )

            result = await session.execute(
                query,
            )

            sections = result.scalars().all()

        return SectionsFullListResponse.model_validate(
            sections,
        )

    async def get_section_by_id(
            self,
            section_id: UUID,
    ) -> SectionResponse:
        async with self.db.db_session() as session:
            section = await session.get(
                Sections,
                section_id,
            )

        if not section:
            raise ObjectExistenceError(
                "Раздела курса с таким идентификатором не существует!",
            )

        return SectionResponse.model_validate(
            section,
        )

    async def delete_section(
            self,
            section_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            section = await session.get(
                Sections,
                section_id,
                with_for_update=True,
            )

            await session.delete(
                section,
            )
            await session.commit()

    async def update_section(
            self,
            section_id: UUID,
            name: str,
            description: str,
    ) -> None:
        async with self.db.db_session() as session:
            section = await session.get(
                Sections,
                section_id,
                with_for_update=True,
            )

            section.name = name
            section.description = description

            await session.commit()

    async def swap_sections(
            self,
            first_section_id: UUID,
            second_section_id: UUID,
    ) -> None:
        async with self.db.db_session() as session:
            first_section = await session.get(
                Sections,
                first_section_id,
                with_for_update=True,
            )
            second_section = await session.get(
                Sections,
                second_section_id,
                with_for_update=True,
            )

            assert first_section is not None
            assert second_section is not None

            if first_section.course_id != second_section.course_id:
                raise DifferentSourcesContentSwapError(
                    "Обменяться порядковыми номерами между разделами можно только в пределах одного курса!",
                )

            first_section.order_number, second_section.order_number = second_section.order_number, \
                first_section.order_number

            await session.commit()
