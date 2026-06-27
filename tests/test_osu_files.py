import unittest

from app.usecases import osu_files


class OsuFilesTestCase(unittest.TestCase):
    def test_valid_osu_file_data(self) -> None:
        data = b"""osu file format v14

[General]
AudioFilename: audio.mp3

[Metadata]
Title: Test
"""

        self.assertTrue(osu_files._is_valid_osu_file_data(data))

    def test_html_error_page_is_invalid_osu_file_data(self) -> None:
        data = b"""<!doctype html>
<html>
<body>403 Forbidden</body>
</html>
"""

        self.assertFalse(osu_files._is_valid_osu_file_data(data))

    def test_empty_osu_file_data_is_invalid(self) -> None:
        self.assertFalse(osu_files._is_valid_osu_file_data(b""))


if __name__ == "__main__":
    unittest.main()
