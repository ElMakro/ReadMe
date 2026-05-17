from enum import Enum


class CourseState(
    Enum,
):
    """Состояние курса относительно пользователя"""
    ENROLLED = "enrolled"
    ENROLLABLE = "enrollable"
    CONTROLLED = "controlled"
