class UserNotFoundError(
    ValueError,
):
    """
    Исключение, связанное с отсутствием пользователя.
    """
    pass


class ApplicationFieldsMismatchError(
    ValueError,
):
    """
    Исключение, связанное с несоответствием полей id пользователя и заявки при обновлении статуса заявки.
    """
    pass
