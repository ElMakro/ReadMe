from uuid import UUID

from fastapi import Depends

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.sections.sections import SectionIDMixin, SectionResponse, SectionsFullListResponse
from server.app.api.v1.sections.sections_manager import DifferentSourcesContentSwapError, SectionsManager
from server.app.api.v1.users.users import UserVerification
from server.enums.role import Role


class OrderNumberConflictError(
    ValueError,
):
    """Исключение, связанное с нарушением порядка элементов"""
    pass


class SectionsService:
    def __init__(
            self,
            sections_manager: SectionsManager = Depends(
                SectionsManager,
            ),
            courses_manager: CoursesManager = Depends(
                CoursesManager,
            ),
    ) -> None:
        self.sections_manager = sections_manager
        self.courses_manager = courses_manager

    async def create_section(
            self,
            user: UserVerification,
            course_id: UUID,
            name: str,
            description: str,
            order_number: int,
    ) -> SectionIDMixin:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if not (user.role == Role.ADMIN or course.professor_id == user.id):
            raise OperationPermissionError(
                "У пользователя, не являющегося владельцем курса или администратором, нет права "
                "создавать темы в курсе!",
            )

        if await self.sections_manager.check_course_have_section_with_order_number(
                course_id,
                order_number, ):
            raise OrderNumberConflictError(
                "Раздел с таким порядковым номером уже существует!",
            )

        return await self.sections_manager.create_section(
            course_id,
            name,
            description,
            order_number,
        )

    async def get_section_by_id(
            self,
            user: UserVerification,
            section_id: UUID,
    ) -> SectionResponse:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )
        course = await self.courses_manager.get_course_by_id(
            section.course_id,
        )

        if user.role == Role.ADMIN:
            return section

        if course.is_content_public:
            return section

        if course.professor_id == user.id:
            return section

        if await self.courses_manager.check_is_user_enrolled_on_course(
                user.id,
                course.id,
        ):
            return section

        raise OperationPermissionError(
            "Пользователь не имеет доступа к данному разделу!",
        )

    async def get_sections_by_course_id(
            self,
            user: UserVerification,
            course_id: UUID,
    ) -> SectionsFullListResponse:
        allow_return = False

        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if user.role == Role.ADMIN:
            allow_return = True

        if course.is_content_public:
            allow_return = True

        if course.professor_id == user.id:
            allow_return = True

        if not allow_return:
            if await self.courses_manager.check_is_user_enrolled_on_course(
                    user.id,
                    course_id,
            ):
                allow_return = True

        if allow_return:
            return await self.sections_manager.get_sections_by_course_id(
                course_id,
            )

        raise OperationPermissionError(
            "Пользователь не имеет прав доступа к разделам данного курса",
        )

    async def delete_section(
            self,
            user: UserVerification,
            section_id: UUID,
    ) -> None:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if user.role != Role.ADMIN:
            course = await self.courses_manager.get_course_by_id(
                section.course_id,
            )

            if not course.professor_id == user.id:
                raise OperationPermissionError(
                    "У пользователя нет прав на удаление данного раздела!",
                )

        await self.sections_manager.delete_section(
            section_id,
        )

    async def update_section(
            self,
            user: UserVerification,
            section_id: UUID,
            new_name: str | None,
            new_description: str | None,
    ) -> None:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if user.role != Role.ADMIN:
            course = await self.courses_manager.get_course_by_id(
                section.course_id,
            )
            if not course.professor_id == user.id:
                raise OperationPermissionError(
                    "У пользователя нет прав на изменение данного раздела!",
                )

        if new_name is None and new_description is None:
            return

        result_name = new_name if new_name is not None else section.name
        result_description = new_description if new_description is not None else section.description

        if section.name == result_name and section.description == result_description:
            return

        await self.sections_manager.update_section(
            section_id,
            result_name,
            result_description,
        )

    async def swap_sections(
            self,
            user: UserVerification,
            first_section_id: UUID,
            second_section_id: UUID,
    ) -> None:
        first_section = await self.sections_manager.get_section_by_id(
            first_section_id,
        )
        second_section = await self.sections_manager.get_section_by_id(
            second_section_id,
        )

        if first_section.course_id != second_section.course_id:
            raise DifferentSourcesContentSwapError(
                "Обменяться порядковыми номерами между разделами можно только в пределах одного курса!",
            )

        if user.role != Role.ADMIN:
            course = await self.courses_manager.get_course_by_id(
                first_section.course_id,
            )
            if not course.professor_id == user.id:
                raise OperationPermissionError(
                    "У пользователя нет прав на изменение курса!",
                )

        await self.sections_manager.swap_sections(
            first_section_id,
            second_section_id,
        )
