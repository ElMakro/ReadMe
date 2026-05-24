from uuid import UUID

from fastapi import Depends

from server.app.api.v1.courses.courses_manager import CoursesManager
from server.app.api.v1.courses.courses_service import OperationPermissionError
from server.app.api.v1.sections.sections import SectionIDMixin, SectionResponse, SectionsFullListResponse
from server.app.api.v1.sections.sections_manager import DifferentSourcesContentSwapError, SectionsManager
from server.app.api.v1.users.enums.access_permissions import AccessPermissions
from server.app.api.v1.users.users import UserVerification
from server.app.api.v1.users.users_service import UsersService
from server.data.data_manager import DataManager


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
            users_service: UsersService = Depends(
                UsersService,
            ),
            data_manager: DataManager = Depends(
                DataManager,
            ),
    ) -> None:
        self.sections_manager = sections_manager
        self.courses_manager = courses_manager
        self.users_service = users_service
        self.data_manager = data_manager

    async def create_section(
            self,
            user: UserVerification,
            course_id: UUID,
            name: str,
            description: str,
            order_number: int,
            tags: list[str],
    ) -> SectionIDMixin:
        course = await self.courses_manager.get_course_by_id(
            course_id,
        )

        if await self.users_service.check_course_access(
                user,
                course=course,
        ) < AccessPermissions.EDIT_ACCESS:
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

        section = await self.sections_manager.create_section(
            course_id,
            name,
            description,
            order_number,
            tags,
        )

        await self.data_manager.create_section(
            section.id,
            course_id,
        )

        return section

    async def get_section_by_id(
            self,
            user: UserVerification | None,
            section_id: UUID,
    ) -> SectionResponse:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if await self.users_service.check_course_access(
                user,
                course_id=section.course_id,
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет доступа к данному разделу!",
            )

        return section

    async def get_sections_by_course_id(
            self,
            user: UserVerification | None,
            course_id: UUID,
    ) -> SectionsFullListResponse:
        if await self.users_service.check_course_access(
                user,
                course_id=course_id,
        ) < AccessPermissions.CONTENT_ACCESS:
            raise OperationPermissionError(
                "Пользователь не имеет прав доступа к разделам данного курса",
            )

        return await self.sections_manager.get_sections_by_course_id(
            course_id,
        )

    async def delete_section(
            self,
            user: UserVerification,
            section_id: UUID,
    ) -> None:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if await self.users_service.check_course_access(
                user,
                section.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на удаление данного раздела!",
            )

        await self.sections_manager.delete_section(
            section_id,
        )

        await self.data_manager.delete_section(
            section_id,
            section.course_id,
        )

    async def update_section(
            self,
            user: UserVerification,
            section_id: UUID,
            new_name: str | None,
            new_description: str | None,
            new_tags: list[str] | None,
    ) -> None:
        section = await self.sections_manager.get_section_by_id(
            section_id,
        )

        if await self.users_service.check_course_access(
                user,
                section.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на удаление данного раздела!",
            )

        if new_name is None and new_description is None and new_tags is None:
            return

        result_name = new_name if new_name is not None else section.name
        result_description = new_description if new_description is not None else section.description
        result_tags = new_tags if new_tags is not None else section.tags

        if section.name == result_name and section.description == result_description and section.tags == result_tags:
            return

        await self.sections_manager.update_section(
            section_id,
            result_name,
            result_description,
            result_tags,
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

        if await self.users_service.check_course_access(
                user,
                first_section.course_id,
        ) < AccessPermissions.EDIT_ACCESS:
            raise OperationPermissionError(
                "У пользователя нет прав на удаление данного раздела!",
            )

        await self.sections_manager.swap_sections(
            first_section_id,
            second_section_id,
        )
