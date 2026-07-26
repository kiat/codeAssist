import zipfile

import pytest

from ai_feedback.source_extraction import (
    SourceExtractionError,
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


def test_is_safe_archive_member_rejects_path_traversal_and_drive_paths():
    assert is_safe_archive_member("src/main.py") is True
    assert is_safe_archive_member("../main.py") is False
    assert is_safe_archive_member("/main.py") is False
    assert is_safe_archive_member("C:/main.py") is False
    assert is_safe_archive_member("node_modules/package/index.js") is False
