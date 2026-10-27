import os

from werkzeug.utils import secure_filename

from util.errors import BadRequestError

DEFAULT_SUBMISSION_NAME = "solution.py"
MAX_SUBMISSION_FILES = 20


def normalize_submission_files(value):
    """Validate the instructor's required submission file names.

    Accepts a list or a comma-separated string. Returns a list of names, or
    None when nothing is required. Raises BadRequestError for a name the
    autograder could not rely on: one that secure_filename would change, one
    without an extension, or a duplicate.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        raise BadRequestError("submission_files must be a list of file names")

    names = []
    for raw in value:
        if not isinstance(raw, str):
            raise BadRequestError("submission_files must be a list of file names")
        name = raw.strip()
        if not name:
            continue
        safe = secure_filename(name)
        if safe != name:
            suggestion = f" Try {safe}." if safe else ""
            raise BadRequestError(f"Invalid file name: {name}.{suggestion}")
        if not os.path.splitext(name)[1]:
            raise BadRequestError(f"File name needs an extension: {name}")
        if name in names:
            raise BadRequestError(f"Duplicate file name: {name}")
        names.append(name)

    if len(names) > MAX_SUBMISSION_FILES:
        raise BadRequestError(f"At most {MAX_SUBMISSION_FILES} file names are allowed")
    return names or None


def required_submission_files(assignment):
    """The instructor's required file names, or an empty list."""
    files = getattr(assignment, "submission_files", None)
    return files if isinstance(files, list) else []


def required_submission_name(assignment):
    """The first required file name, or None."""
    files = required_submission_files(assignment)
    return files[0] if files else None


def resolve_submission_name(assignment, client_name):
    """The name a submission is saved and graded under.

    The instructor's required name wins over whatever the client sent. A
    client-supplied name is always passed through secure_filename, since it
    becomes a path on disk and inside the container.
    """
    required = required_submission_name(assignment)
    if required:
        return required
    return secure_filename(client_name or "") or DEFAULT_SUBMISSION_NAME
