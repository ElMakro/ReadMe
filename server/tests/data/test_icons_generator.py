from server.data.icons_generator import IconsGenerator


class TestIconsGenerator:
    def test_generate_icon_returns_bytes(self):
        generator = IconsGenerator()
        data = "test_user_12345"

        result = generator.generate_icon(data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_icon_different_input_produces_different_output(self):
        generator = IconsGenerator()

        icon1 = generator.generate_icon("user1")
        icon2 = generator.generate_icon("user2")

        assert icon1 != icon2

    def test_generate_icon_same_input_produces_same_output(self):
        generator = IconsGenerator()
        data = "same_user_123"

        icon1 = generator.generate_icon(data)
        icon2 = generator.generate_icon(data)

        assert icon1 == icon2

    def test_generate_icon_handles_empty_string(self):
        generator = IconsGenerator()

        result = generator.generate_icon("")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_icon_handles_long_string(self):
        generator = IconsGenerator()
        long_data = "x" * 1000

        result = generator.generate_icon(long_data)

        assert isinstance(result, bytes)
        assert len(result) > 0
