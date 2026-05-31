class NoteAlreadyExistsError(
    ValueError,
):
    """
    Исключение, связанное с попыткой создать уже существующий конспект.
    """
    pass


class NoteFieldsMismatchError(
    ValueError,
):
    """
    Исключение, связанное с несоответствием полей id, student_id и topic_id при обновлении конспекта.
    """
    pass


class NoteNotFoundError(
    ValueError,
):
    """
    Исключение, связанное с отсутствием запрашиваемого конспекта.
    """
    pass


class CantChangeOwnRoleError(
    ValueError,
):
    """
    Исключение, связанное с невозможностью изменить собственную роль администратором.
    """
    pass


class CantDeleteOwnProfileError(
    ValueError,
):
    """
    Исключение, связанное с невозможностью удалить собственный профиль администратором.
    """
    pass
