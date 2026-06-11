from typing import NamedTuple


class CreatedTokenTuple(NamedTuple):
    encoded_jwt: str
    session_id: str
