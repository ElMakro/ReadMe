from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from server.app.service.courses_service import CoursesService
from server.app.service.depends import  get_current_user
from server.schemas.courses import CoursesList
from server.schemas.users import UserVerification

courses_router = APIRouter(prefix="/courses", tags=["courses"])


@courses_router.get(
    path="/my-courses",
    response_model=CoursesList,
    status_code=status.HTTP_200_OK
)
async def get_my_courses(user: Annotated[UserVerification, Depends(get_current_user)],
                         courses_service: CoursesService = Depends(CoursesService)) -> CoursesList:
    return await courses_service.get_courses_for_user(user=user)
