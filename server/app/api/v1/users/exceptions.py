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


class UserIsAlreadyProfessor(
    ValueError,
):
    """
    Исключение, связанное с тем, что пользователь уже является преподавателем.
    """
    pass
