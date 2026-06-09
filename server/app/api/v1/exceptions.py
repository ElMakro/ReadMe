class BadRequestError(
    ValueError,
):
    """Исключение, связанное с некорректной формой запроса"""


class OperationPermissionError(
    ValueError,
):
    """Исключение, связанное с наличием у пользователя прав на операцию над объектом"""


class ObjectMissingError(
    ValueError,
):
    """Исключение, связанное с отсутствием объекта"""
    pass


class ConflictError(
    ValueError,
):
    """Исключение, связанное с нарушением целостности данных"""
    pass


class MediaTypeError(
    ValueError,
):
    """Исключение, связанное с типом загружаемого файла"""
