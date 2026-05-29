class ObjectMissingError(
    ValueError,
):
    """Исключение, связанное с отсутствием объекта"""
    pass


class OperationPermissionError(
    ValueError,
):
    """Исключение, связанное с наличием у пользователя прав на операцию над объектом информационной системы"""


class ContentTypeError(
    ValueError,
):
    """Исключение, связанное с типом загружаемого файла"""
