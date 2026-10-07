import io
import zipfile

from api.schemas import submission_code_as_text


def _zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_plain_source_is_returned_as_text():
    assert submission_code_as_text(b"print('hi')\n") == "print('hi')\n"


def test_none_and_str_pass_through():
    assert submission_code_as_text(None) is None
    assert submission_code_as_text("x = 1") == "x = 1"


def test_zip_submission_shows_source_files_instead_of_crashing():
    raw = _zip_bytes({"calculator.py": "def add(a, b):\n    return a + b\n", "notes.bin": b"\x00\x8a"})

    text = submission_code_as_text(raw)

    assert "File: calculator.py" in text
    assert "return a + b" in text
    assert "notes.bin" not in text


def test_zip_without_source_files_gets_placeholder():
    raw = _zip_bytes({"image.png": b"\x89PNG\x00\x8a"})

    assert submission_code_as_text(raw) == "[This submission is a binary file and cannot be displayed.]"


def test_undecodable_non_zip_bytes_get_placeholder():
    assert submission_code_as_text(b"\xff\xfe\x8a\x00") == "[This submission is a binary file and cannot be displayed.]"
