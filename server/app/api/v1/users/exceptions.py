class UserNotFoundError(
    ValueError,
):
    """
    Исключение, связанное с отсутствием пользователя.
    """
    pass


class NotUniqueFieldsError(
    ValueError,
):
    """
    Исключение, связанное с попыткой задать уже существующий никнейм или почту.
    """
    pass


class ApplicationFieldsMismatchError(
    ValueError,
):
    """
    Исключение, связанное с несоответствием полей id пользователя и заявки при обновлении статуса заявки.
    """
    pass


class ApplicationRefusedError(
    ValueError,
):
    """
    Исключение, связанное с отказом в подаче заявки: пользователь уже преподаватель или его заявка уже находится на
    рассмотрении.
    """
    pass
