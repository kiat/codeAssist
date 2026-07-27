from pathlib import Path, PurePosixPath
import zipfile


SUPPORTED_SOURCE_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".go",
    ".rs",
}

IGNORED_PATH_PARTS = {
    "__macosx",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
}

MAX_SOURCE_FILE_SIZE = 200_000
MAX_TOTAL_SOURCE_SIZE = 1_000_000
MAX_ARCHIVE_FILE_COUNT = 100
ZIP_READ_CHUNK_SIZE = 64 * 1024


class SourceExtractionError(Exception):
    """Raised when submitted source cannot be safely read for AI feedback."""


def is_safe_archive_member(name):
    normalized = (name or "").replace("\\", "/")
    path = PurePosixPath(normalized)

    if not path.parts or path.is_absolute():
        return False

    if ".." in path.parts:
        return False

    if any(":" in part for part in path.parts):
        return False

    if any(part.lower() in IGNORED_PATH_PARTS for part in path.parts):
        return False

    return True


def read_text_source_file(file_path):
    path = Path(file_path)

    if path.stat().st_size > MAX_SOURCE_FILE_SIZE:
        raise SourceExtractionError(
            "AI feedback could not be generated because the submitted source file is too large."
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SourceExtractionError(
            "AI feedback could not be generated because the submitted source file could not be read."
        ) from exc


def _format_zip_source(member_name, content):
    return f"File: {member_name}\n```\n{content}\n```"


def _read_zip_member_with_limits(archive, member, total_size):
    chunks = []
    member_size = 0

    try:
        with archive.open(member) as source:
            while True:
                chunk = source.read(ZIP_READ_CHUNK_SIZE)
                if not chunk:
                    break

                member_size += len(chunk)

                if member_size > MAX_SOURCE_FILE_SIZE:
                    raise SourceExtractionError(
                        "AI feedback could not be generated because a source file in the ZIP archive is too large."
                    )

                if total_size + member_size > MAX_TOTAL_SOURCE_SIZE:
                    raise SourceExtractionError(
                        "AI feedback could not be generated because the source files in the ZIP archive are too large."
                    )

                chunks.append(chunk)
    except RuntimeError as exc:
        raise SourceExtractionError(
            "AI feedback could not be generated because a source file in the ZIP archive could not be read."
        ) from exc

    return b"".join(chunks), total_size + member_size


def extract_source_from_zip(file_path):
    sections = []
    total_size = 0

    try:
        with zipfile.ZipFile(file_path) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]

            if len(members) > MAX_ARCHIVE_FILE_COUNT:
                raise SourceExtractionError(
                    "AI feedback could not be generated because the ZIP file contains too many files."
                )

            for member in members:
                if not is_safe_archive_member(member.filename):
                    continue

                extension = Path(member.filename).suffix.lower()
                if extension not in SUPPORTED_SOURCE_EXTENSIONS:
                    continue

                raw_content, total_size = _read_zip_member_with_limits(
                    archive,
                    member,
                    total_size,
                )
                try:
                    content = raw_content.decode("utf-8")
                except UnicodeDecodeError:
                    content = raw_content.decode("utf-8", errors="replace")

                sections.append(_format_zip_source(member.filename, content))
    except zipfile.BadZipFile as exc:
        raise SourceExtractionError(
            "AI feedback could not be generated because the uploaded ZIP file could not be read."
        ) from exc
    except OSError as exc:
        raise SourceExtractionError(
            "AI feedback could not be generated because the uploaded ZIP file could not be opened."
        ) from exc

    if not sections:
        raise SourceExtractionError(
            "AI feedback could not be generated because no supported source files were found in the uploaded ZIP file."
        )

    return "\n\n".join(sections)


def extract_submission_source(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == ".zip":
        return extract_source_from_zip(file_path)

    if extension in SUPPORTED_SOURCE_EXTENSIONS:
        return read_text_source_file(file_path)

    raise SourceExtractionError(
        "AI feedback could not be generated because the submitted file type is not supported."
    )
