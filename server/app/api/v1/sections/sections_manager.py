from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select

from server.app.api.v1.exceptions import BadRequestError, ObjectMissingError
from server.app.api.v1.sections.sections import SectionIDMixin, SectionResponse, SectionsFullListResponse
from server.config.constants import MAX_SECTION_DESCRIPTION_LENGTH
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

    async def create_section(
            self,
            course_id: UUID,
            name: str,
            description: str,
            order_number: int,
            tags: list[str],
    ) -> SectionIDMixin:
        async with self.db.db_session() as session:
            try:
                new_section = Sections(
                    course_id=course_id,
                    name=name,
                    description=description,
                    order_number=order_number,
                    tags=tags,
                )
            except ValueError:
                raise BadRequestError(f"Описание раздела не может превышать {MAX_SECTION_DESCRIPTION_LENGTH} символов!")

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
            ).order_by(Sections.order_number)

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
            raise ObjectMissingError(
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

            if section is None:
                raise ObjectMissingError("Раздела с таким идентификатором не найдено!")

            await session.delete(
                section,
            )
            await session.commit()

    async def update_section(
            self,
            section_id: UUID,
            name: str,
            description: str,
            tags: list[str],
    ) -> None:
        async with self.db.db_session() as session:
            section = await session.get(
                Sections,
                section_id,
                with_for_update=True,
            )

            section.name = name

            try:
                section.description = description
            except ValueError:
                raise BadRequestError(f"Описание раздела не может превышать {MAX_SECTION_DESCRIPTION_LENGTH} символов!")

            section.tags = tags

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
