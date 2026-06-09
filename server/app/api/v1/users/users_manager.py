import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, delete, desc, exists, insert, literal, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from server.app.api.v1.common_schemas import (
    APPLICATION_FIELDS_MISMATCH_ERROR_TEXT,
    APPLICATION_REFUSED_ERROR_TEXT,
    NOT_FOUND_ERROR_TEXT,
    NOT_UNIQUE_FIELDS_ERROR_TEXT,
    USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT,
)
from server.app.api.v1.users.exceptions import (
    ApplicationFieldsMismatchError,
    ApplicationRefusedError,
    NotUniqueFieldsError,
    UserMustBeInProfessorsTableError,
    UserNotFoundError,
)
from server.app.api.v1.users.users import (
    ApplicationById,
    ApplicationsList,
    ApplicationsUserList,
    SecretApplicationLink,
    UserInfo,
    UserProfile,
    UsersList,
    UserUpdatedInfo,
    UserVerification,
)
from server.config.db_dependency import DBDependency
from server.database.models import ApplicationLink, CoursesForStudents, ProfessorsApplications, ProfessorsDetails, Users
from server.enums.application_status import ApplicationStatus
from server.enums.role import Role


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
        self.application_link_model = ApplicationLink

    async def get_user_profile_info(self, user_id: uuid.UUID) -> UserProfile:
        async with self.db.db_session() as session:
            query = select(
                self.users_model.id,
                self.users_model.nickname,
                self.users_model.email,
                self.users_model.role,
            ).where(
                self.users_model.id == user_id,
            )
            result = await session.execute(query)
            user = result.mappings().one()
            return UserProfile.model_validate(user)

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

    async def search_users(self, pattern: str, offset: int, limit: int) -> UsersList:
        async with self.db.db_session() as session:
            query = select(
                self.users_model.id,
                self.users_model.nickname,
                self.users_model.email,
                self.users_model.role,
            ).order_by(
                self.users_model.nickname,
            ).where(
                self.users_model.nickname.ilike(
                    f"%{pattern}%"
                ),
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

    async def change_role_to_professor(self, id: uuid.UUID) -> None:
        async with (self.db.db_session() as session):
            query = update(
                self.users_model
            ).where(
                self.users_model.id == id
            ).where(
                exists(
                    select(
                        self.professors_model
                    ).where(
                        self.professors_model.id == id
                    )
                )
            ).values(
                role=Role.PROFESSOR
            )
            result = await session.execute(query)
            await session.commit()
            if not result.rowcount:
                raise UserMustBeInProfessorsTableError(USER_MUST_BE_IN_PROFESSORS_TABLE_ERROR_TEXT)
            return

    async def change_role_except_professors(self, id: uuid.UUID, role: Role) -> None:
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

    async def update_user_profile(self, user_id: uuid.UUID, updated_info: UserUpdatedInfo) -> UserProfile:
        async with self.db.db_session() as session:
            query = update(
                self.users_model
            ).where(
                self.users_model.id == user_id
            ).values(
                nickname=updated_info.nickname,
                email=updated_info.email,
            ).returning(
                self.users_model
            )
            try:
                result = await session.execute(query)
                await session.commit()
            except IntegrityError:
                raise NotUniqueFieldsError(NOT_UNIQUE_FIELDS_ERROR_TEXT)
            if not (updated_user := result.scalar_one_or_none()):
                raise UserNotFoundError(NOT_FOUND_ERROR_TEXT)
            return UserProfile.model_validate(updated_user)

    async def reg_professor_application(self, id: uuid.UUID, name: str, surname: str, patronymic: str | None) \
            -> ApplicationById:
        async with self.db.db_session() as session:
            conflict_exists = (
                select(1)
                .where(
                    or_(
                        self.professors_model.id == id,
                        and_(
                            self.professors_applications_model.user_id == id,
                            self.professors_applications_model.status == ApplicationStatus.PENDING.name
                        )
                    )
                )
                .exists()
            )
            query = insert(
                self.professors_applications_model
            ).from_select(
                ['name', 'surname', 'patronymic', 'user_id'],
                select(
                    literal(name), literal(surname), literal(patronymic), literal(id)
                ).where(~conflict_exists)
            ).returning(
                self.professors_applications_model.id
            )
            result = await session.execute(query)
            await session.commit()
            if (application_id := result.mappings().one_or_none()) is None:
                raise ApplicationRefusedError(APPLICATION_REFUSED_ERROR_TEXT)
            return ApplicationById.model_validate(application_id)

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

    async def get_user_applications(self, id: uuid.UUID, offset: int, limit: int) -> ApplicationsUserList:
        async with self.db.db_session() as session:
            query = select(
                self.professors_applications_model.id.label("application_id"),
                self.professors_applications_model.user_id,
                self.professors_applications_model.name,
                self.professors_applications_model.surname,
                self.professors_applications_model.patronymic,
                self.professors_applications_model.status,
                self.professors_applications_model.admin_comment,
                self.professors_applications_model.created_at,
                self.professors_applications_model.updated_at,
            ).where(
                self.professors_applications_model.user_id == id
            ).order_by(
                desc(self.professors_applications_model.updated_at)
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

    async def get_secret_application_link(self) -> SecretApplicationLink | None:
        async with self.db.db_session() as session:
            query = select(
                self.application_link_model,
            )
            result = await session.execute(query)
            link = result.scalar_one_or_none()
            print(link)
            if link is None:
                return None
            return SecretApplicationLink.model_validate(link)

    async def set_secret_application_link(self, new_link: str) -> SecretApplicationLink:
        async with self.db.db_session() as session:
            query = pg_insert(
                self.application_link_model,
            ).values(
                secret_part=new_link,
            )
            updated_query = query.on_conflict_do_update(
                index_elements=[self.application_link_model.single.key],
                set_={"secret_part": query.excluded.secret_part}
            ).returning(
                self.application_link_model,
            )
            result = await session.execute(updated_query)
            await session.commit()
            link = result.scalar_one()
            return SecretApplicationLink.model_validate(link)

    async def self_enroll_on_course(
            self,
            user_id: uuid.UUID,
            course_id: uuid.UUID,
    ) -> None:
        async with self.db.db_session() as session:
            record = CoursesForStudents(
                student_id=user_id,
                course_id=course_id,
            )
            session.add(
                record,
            )
            await session.commit()

    async def self_unenroll_from_course(
            self,
            user_id: uuid.UUID,
            course_id: uuid.UUID,
    ) -> None:
        async with self.db.db_session() as session:
            query = delete(
                CoursesForStudents,
            ).where(
                CoursesForStudents.student_id == user_id,
                CoursesForStudents.course_id == course_id,
            )

            await session.execute(
                query,
            )
            await session.commit()

    async def get_enrolled_users(self, course_id: UUID) -> UsersList:
        async with self.db.db_session() as session:
            filtered_students = (
                select(CoursesForStudents.student_id)
                .where(CoursesForStudents.course_id == course_id)
                .subquery()
            )

            query = (
                select(Users)
                .join(filtered_students, filtered_students.c.student_id == Users.id)
            )

            query = await session.execute(query)
            result = query.scalars().all()

        return UsersList.model_validate(result)
