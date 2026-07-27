import io
import zipfile

import pytest

from ai_feedback import source_extraction
from ai_feedback.source_extraction import (
    MAX_SOURCE_FILE_SIZE,
    MAX_TOTAL_SOURCE_SIZE,
    SourceExtractionError,
    extract_source_from_zip,
    extract_submission_source,
    is_safe_archive_member,
)


def test_extract_submission_source_reads_text_file(tmp_path):
    source_path = tmp_path / "solution.py"
    source_path.write_text("print('hello')\n", encoding="utf-8")

    assert extract_submission_source(source_path) == "print('hello')\n"


def test_extract_submission_source_reads_supported_files_from_zip(tmp_path):
    zip_path = tmp_path / "submission.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("main.py", "print('main')\n")
        archive.writestr("helpers/util.py", "def helper(): return 1\n")
        archive.writestr("README.md", "not source")
        archive.writestr("../evil.py", "print('evil')\n")

    extracted = extract_submission_source(zip_path)

    assert "File: main.py" in extracted
    assert "print('main')" in extracted
    assert "File: helpers/util.py" in extracted
    assert "def helper()" in extracted
    assert "README.md" not in extracted
    assert "evil" not in extracted


def test_extract_submission_source_rejects_zip_without_supported_sources(tmp_path):
    zip_path = tmp_path / "submission.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("README.md", "notes only")

    with pytest.raises(SourceExtractionError, match="no supported source files"):
        extract_submission_source(zip_path)


def test_extract_submission_source_rejects_too_many_zip_files(tmp_path):
    zip_path = tmp_path / "submission.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for index in range(101):
            archive.writestr(f"file_{index}.txt", "x")

    with pytest.raises(SourceExtractionError, match="too many files"):
        extract_submission_source(zip_path)


def test_extract_source_from_zip_enforces_actual_file_size_when_header_is_wrong(
    monkeypatch,
    tmp_path,
):
    class FakeMember:
        filename = "main.py"
        file_size = 1

        def is_dir(self):
            return False

    class FakeZip:
        def __init__(self, _file_path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def infolist(self):
            return [FakeMember()]

        def read(self, _member):
            return b"x" * (MAX_SOURCE_FILE_SIZE + 1)

        def open(self, _member):
            return io.BytesIO(b"x" * (MAX_SOURCE_FILE_SIZE + 1))

    monkeypatch.setattr(source_extraction.zipfile, "ZipFile", FakeZip)

    with pytest.raises(SourceExtractionError, match="source file in the ZIP archive is too large"):
        extract_source_from_zip(tmp_path / "submission.zip")


def test_extract_source_from_zip_enforces_actual_total_size_when_headers_are_wrong(
    monkeypatch,
    tmp_path,
):
    class FakeMember:
        file_size = 1

        def __init__(self, filename):
            self.filename = filename

        def is_dir(self):
            return False

    class FakeZip:
        def __init__(self, _file_path):
            self.members = [FakeMember(f"file_{index}.py") for index in range(6)]
            self.content = b"x" * (MAX_TOTAL_SOURCE_SIZE // 6 + 1)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def infolist(self):
            return self.members

        def read(self, _member):
            return self.content

        def open(self, _member):
            return io.BytesIO(self.content)

    monkeypatch.setattr(source_extraction.zipfile, "ZipFile", FakeZip)

    with pytest.raises(SourceExtractionError, match="source files in the ZIP archive are too large"):
        extract_source_from_zip(tmp_path / "submission.zip")


def test_is_safe_archive_member_rejects_path_traversal_and_drive_paths():
    assert is_safe_archive_member("src/main.py") is True
    assert is_safe_archive_member("../main.py") is False
    assert is_safe_archive_member("/main.py") is False
    assert is_safe_archive_member("C:/main.py") is False
    assert is_safe_archive_member("node_modules/package/index.js") is False
