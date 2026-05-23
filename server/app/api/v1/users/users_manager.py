import uuid

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.common_schemas import (
    APPLICATION_FIELDS_MISMATCH_ERROR_TEXT,
    NOT_FOUND_ERROR_TEXT,
    USER_IS_ALREADY_PROFESSOR_ERROR_TEXT,
)
from server.app.api.v1.users.exceptions import ApplicationFieldsMismatchError, UserIsAlreadyProfessor, UserNotFoundError
from server.app.api.v1.users.users import ApplicationsList, ApplicationsUserList, UserInfo, UsersList, UserVerification
from server.config.db_dependency import DBDependency
from server.database.models import ProfessorsApplications, ProfessorsDetails, Users
from server.enums.application_status import ApplicationStatus
from server.enums.role import Role


class UserExistenceError(
    ValueError,
):
    """Исключение, связанное с существованием пользователя"""
    pass


class UsersManager:
    def __init__(
            self,
            db: DBDependency = Depends(
                DBDependency,
            ),
    ) -> None:
        self.db = db
        self.users_model = Users
        self.professors_applications_model = ProfessorsApplications
        self.professors_model = ProfessorsDetails

    async def get_user_by_nickname(
            self,
            nickname: str,
    ) -> UserInfo | None:
        async with self.db.db_session() as session:
            query = select(
                self.users_model.id,
                self.users_model.nickname,
                self.users_model.email,
                self.users_model.role,
                self.users_model.password,
            ).where(
                self.users_model.nickname == nickname,
            )

            result = await session.execute(
                query,
            )
            user = result.mappings().first()
            return UserInfo(
                **user,
            ) if user else None

    async def get_user_by_id(
            self,
            user_id: uuid.UUID,
    ) -> UserVerification | None:
        async with self.db.db_session() as session:
            query = select(
                self.users_model.id,
                self.users_model.nickname,
                self.users_model.role,
            ).where(
                self.users_model.id == user_id,
            )

            result = await session.execute(
                query,
            )
            user = result.mappings().one_or_none()
            return UserVerification(
                **user,
            ) if user else None

    async def get_all_users(self, offset: int, limit: int) -> UsersList:
        async with (self.db.db_session() as session):
            query = select(
                self.users_model.id,
                self.users_model.nickname,
                self.users_model.email,
                self.users_model.role,
            ).order_by(
                self.users_model.nickname,
            ).offset(
                offset,
            ).limit(
                limit,
            )
            result = await session.execute(
                query,
            )
            users = result.mappings().all()
            return UsersList.model_validate(
                users,
            )

    async def change_role(self, id: uuid.UUID, role: Role) -> None:
        async with (self.db.db_session() as session):
            query = update(
                self.users_model
            ).where(
                self.users_model.id == id
            ).values(
                role=role
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise UserNotFoundError(NOT_FOUND_ERROR_TEXT)
            return

    async def delete_user(self, id: uuid.UUID) -> None:
        async with (self.db.db_session() as session):
            query = delete(
                self.users_model
            ).where(
                self.users_model.id == id,
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise UserNotFoundError(NOT_FOUND_ERROR_TEXT)
            return

    async def reg_professor_application(self, id: uuid.UUID, name: str, surname: str, patronymic: str | None):
        async with self.db.db_session() as session:
            query = insert(
                self.professors_applications_model
            ).values(
                name=name,
                surname=surname,
                patronymic=patronymic,
                user_id=id,
            )
            await session.execute(query)
            await session.commit()
            return

    async def get_professor_applications(self, offset: int, limit: int) -> ApplicationsList:
        async with self.db.db_session() as session:
            query = select(
                self.professors_applications_model.id.label("application_id"),
                self.professors_applications_model.user_id,
                self.professors_applications_model.name,
                self.professors_applications_model.surname,
                self.professors_applications_model.patronymic,
                self.professors_applications_model.status,
                self.professors_applications_model.created_at,
                self.professors_applications_model.updated_at,
            ).where(
                self.professors_applications_model.status == ApplicationStatus.PENDING
            ).order_by(
                self.professors_applications_model.created_at
            ).offset(
                offset
            ).limit(
                limit
            )
            result = await session.execute(query)
            applications = result.mappings().all()
            return ApplicationsList.model_validate(
                applications,
            )

    async def change_application_status(self, id: uuid.UUID, user_id: uuid.UUID, status: ApplicationStatus,
                                        comment: str) -> None:
        async with self.db.db_session() as session:
            query = update(
                self.professors_applications_model
            ).where(
                self.professors_applications_model.id == id,
                self.professors_applications_model.user_id == user_id
            ).values(
                status=status,
                admin_comment=comment,
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise ApplicationFieldsMismatchError(APPLICATION_FIELDS_MISMATCH_ERROR_TEXT)
            return

    async def add_user_to_professors(self, id: uuid.UUID, name: str, surname: str, patronymic: str | None) -> None:
        async with self.db.db_session() as session:
            query = insert(
                self.professors_model
            ).values(
                id=id,
                name=name,
                surname=surname,
                patronymic=patronymic,
            )
            try:
                await session.execute(query)
                await session.commit()
            except IntegrityError:
                raise UserIsAlreadyProfessor(USER_IS_ALREADY_PROFESSOR_ERROR_TEXT)
            return

    async def get_user_applications(self, id: uuid.UUID, offset: int, limit: int) -> ApplicationsUserList:
        async with self.db.db_session() as session:
            query = select(
                self.professors_applications_model.id.label("application_id"),
                self.professors_applications_model.user_id,
                self.professors_applications_model.name,
                self.professors_applications_model.surname,
                self.professors_applications_model.patronymic,
                self.professors_applications_model.status,
                self.professors_applications_model.created_at,
                self.professors_applications_model.updated_at,
            ).where(
                self.professors_applications_model.user_id == id
            ).order_by(
                self.professors_applications_model.updated_at
            ).offset(
                offset
            ).limit(
                limit
            )
            result = await session.execute(query)
            applications = result.mappings().all()
            return ApplicationsUserList.model_validate(
                applications,
            )
