from server.schemas.users import UserProfile, UserVerification


class StudentsService:
    def __init__(self) -> None:
        pass

    def get_info_for_user_profile(self, user: UserVerification) -> UserProfile:
        return UserProfile(id=user.id, nickname=user.nickname, email=user.email, role=user.role)
