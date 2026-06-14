from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse

from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    MediaTypeError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.app.api.v1.notes.exceptions import (
    CantChangeOwnRoleError,
    CantDeleteOwnProfileError,
    NoteAlreadyExistsError,
    NoteFieldsMismatchError,
    NoteNotFoundError,
    TopicNotFoundError,
)
from server.app.api.v1.users.exceptions import (
    ApplicationFieldsMismatchError,
    ApplicationRefusedError,
    NotExistingLinkError,
    NotUniqueFieldsError,
    UpdatedLinkError,
    UserMustBeInProfessorsTableError,
    UserNotFoundError,
)
from server.data.courses_resources.compilation_manager import CompilationError

ExceptionHandlerMap = dict[type[Exception], int]

COMMON_HANDLERS: ExceptionHandlerMap = {
    CompilationError: status.HTTP_400_BAD_REQUEST,
    BadRequestError: status.HTTP_400_BAD_REQUEST,
    OperationPermissionError: status.HTTP_403_FORBIDDEN,
    ObjectMissingError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    MediaTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    NotUniqueFieldsError: status.HTTP_409_CONFLICT,
    UserMustBeInProfessorsTableError: status.HTTP_409_CONFLICT,
    CantChangeOwnRoleError: status.HTTP_409_CONFLICT,
    CantDeleteOwnProfileError: status.HTTP_409_CONFLICT,
    NotExistingLinkError: status.HTTP_409_CONFLICT,
    UpdatedLinkError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ApplicationRefusedError: status.HTTP_409_CONFLICT,
    ApplicationFieldsMismatchError: status.HTTP_409_CONFLICT,
    NoteAlreadyExistsError: status.HTTP_409_CONFLICT,
    NoteFieldsMismatchError: status.HTTP_409_CONFLICT,
    NoteNotFoundError: status.HTTP_404_NOT_FOUND,
    TopicNotFoundError: status.HTTP_404_NOT_FOUND,
}


def create_exception_handler(status_code: int):
    async def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
        )

    return custom_exception_handler


async def compilation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, CompilationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.content_error.model_dump()},
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


def register_global_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CompilationError, compilation_error_handler)

    for exc_type, status_code in COMMON_HANDLERS.items():
        if exc_type is not CompilationError:
            handler = create_exception_handler(status_code)
            app.add_exception_handler(exc_type, handler)
