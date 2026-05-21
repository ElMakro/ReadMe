from enum import IntEnum


class AccessLevels(
    IntEnum,
):
    NO_ACCESS = 0
    HEADER_ACCESS = 1
    CONTENT_ACCESS = 2
    EDIT_ACCESS = 3
