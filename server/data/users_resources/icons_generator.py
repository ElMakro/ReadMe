from hashlib import sha1
from pathlib import Path

from pydenticon import Generator

from server.app.api.v1.users.users import CreatedUserInfo


class IconsGenerator:
    def __init__(self):
        foreground = ["rgb(45,79,255)",
                      "rgb(254,180,44)",
                      "rgb(226,121,234)",
                      "rgb(30,179,253)",
                      "rgb(232,77,65)",
                      "rgb(49,203,115)",
                      "rgb(141,69,170)"]

        background = "rgb(224,224,224)"

        self.generator = Generator(5, 5, digest=sha1, background=background, foreground=foreground)

    def generate_icon(self, created_user_info: CreatedUserInfo, user_directory_path: Path) -> None:
        icon = self.generator.generate(f"{created_user_info.id}-{created_user_info.nickname}-"
                                       f"{created_user_info.created_at}-{created_user_info.updated_at}", 240, 240)

        with open(user_directory_path / "icon.png", "wb") as icon_file:
            icon_file.write(icon)
