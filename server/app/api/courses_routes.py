from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.params import Depends

from server.app.service.courses_service import CoursesService
from server.app.service.depends import get_current_user
from server.schemas.courses import CoursesList
from server.schemas.users import UserVerification

courses_router = APIRouter(prefix="/courses", tags=["courses"])


@courses_router.get(
    path="/my-courses",
    response_model=CoursesList,
    status_code=status.HTTP_200_OK
)
async def get_my_courses(user: Annotated[UserVerification, Depends(get_current_user)],
                         page: int = Query(1, ge=1),
                         size: int = Query(10, ge=1, le=20),
                         courses_service: CoursesService = Depends(CoursesService)) -> CoursesList:
    result = await courses_service.get_courses_for_user(user=user, page=page, size=size)
    return result
