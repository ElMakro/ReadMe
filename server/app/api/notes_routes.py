from fastapi import APIRouter

notes_router = APIRouter(
    prefix="/notes",
    tags=["Взаимодействие с заметками"],
)

# @notes_router.post(
#     "/create-note",
#     summary="Создать новую заметку",
#     response_description="Новая заметка успешно создана",
#     status_code=status.HTTP_201_CREATED,
#     response_model=TopicIDMixin,
#     responses={
#         status.HTTP_403_FORBIDDEN            : {
#             "description": "У пользователя нет прав на создание темы в данном разделе",
#         },
#         status.HTTP_404_NOT_FOUND            : {
#             "description": "Раздела с таким идентификатором не существует",
#         },
#         status.HTTP_409_CONFLICT             : {
#             "description": "Тема с таким порядковым номером уже существует в этом разделе",
#         },
#         status.HTTP_422_UNPROCESSABLE_CONTENT: {
#             "description": UNPROCESSABLE_ENTITY_ERROR_TEXT,
#         },
#     },
#     openapi_extra=openapi_extra_authorization_cookie,
# )
# async def create_topic(
#         user: Annotated[UserVerification, Depends(
#             get_current_user,
#         )],
#         topic_data: TopicCreation,
#         topics_service: TopicsService = Depends(
#             TopicsService,
#         ),
# ) -> TopicIDMixin:
#     """
#     Создать новую тему в разделе.
#     Порядковый номер определяет отображение тем в разделе.
#     """
#     pass
