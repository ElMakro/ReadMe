from fastapi import APIRouter, status

students_router = APIRouter(
    prefix="/students",
    tags=["Взаимодействие со студентами"],
)


@students_router.post(
    "/enroll",
    summary="Записать другого студента на курс",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def enroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass


@students_router.post(
    "/unenroll",
    summary="Отписать другого студента от курса",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def unenroll_other_student():
    # TODO: Когда-нибудь дописать маршрут и схемы
    pass
