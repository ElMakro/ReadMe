
from fastapi import HTTPException, status

from server.app.api.v1.exceptions import (
    BadRequestError,
    ConflictError,
    MediaTypeError,
    ObjectMissingError,
    OperationPermissionError,
)
from server.data.courses_resources.compilation_manager import CompilationError

HANDLED_EXCEPTIONS = (
    BadRequestError,
    CompilationError,
    OperationPermissionError,
    ObjectMissingError,
    ConflictError,
    MediaTypeError,
)

ExceptionHandlerMap = dict[type[Exception], int]

COMMON_HANDLERS: ExceptionHandlerMap = {
    CompilationError: status.HTTP_400_BAD_REQUEST,
    BadRequestError: status.HTTP_400_BAD_REQUEST,
    OperationPermissionError: status.HTTP_403_FORBIDDEN,
    ObjectMissingError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    MediaTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
}


def handle_exception_chain(
        exc: Exception,
) -> Exception:
    for exc_type, status_code in COMMON_HANDLERS.items():
        if isinstance(exc, exc_type):
            return HTTPException(status_code=status_code, detail=str(exc))
    return exc
