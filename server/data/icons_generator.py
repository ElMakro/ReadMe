from hashlib import sha1

from pydenticon import Generator


class IconsGenerator:
    def __init__(self):
        foreground = [
            "rgb(45,79,255)", "rgb(254,180,44)", "rgb(226,121,234)",
            "rgb(30,179,253)", "rgb(232,77,65)", "rgb(49,203,115)", "rgb(141,69,170)"
        ]
        background = "rgb(224,224,224)"

        self.generator = Generator(5, 5, digest=sha1, background=background, foreground=foreground)

    def generate_icon(self, data: str) -> bytes:
        return self.generator.generate(data,240, 240)
