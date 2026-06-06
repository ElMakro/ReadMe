class UserNotFoundError(
    ValueError,
):
    """
    Исключение, связанное с отсутствием пользователя.
    """
    pass


class UserMustBeInProfessorsTableError(
    ValueError,
):
    """
    Исключение, связанное с невозможностью присвоить пользователю роль преподавателя вручную (так как его нет в таблице
    преподавателей).
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


class UpdatedLinkError(
    ValueError,
):
    """
    Исключение, связанное с использованием недопустимых символов для ссылки.
    """
    pass


class NotExistingLinkError(
    ValueError,
):
    """
    Исключение, связанное с отсутствием в базе данных секретной ссылки для подачи заявления на роль преподавателя.
    """
    pass
