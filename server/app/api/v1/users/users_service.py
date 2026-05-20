

from server.app.api.v1.users.users import UserProfile, UserVerification


class UsersService:
    def __init__(
            self,
    ) -> None:
        pass

    def get_info_for_user_profile(
            self,
            user: UserVerification,
    ) -> UserProfile:
        print(user, "HEREEEEEEEEEEEEEEE")
        return UserProfile(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            role=user.role,
        )


