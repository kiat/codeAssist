"""Tests for util.submission_files."""
from types import SimpleNamespace

import pytest

from util.errors import BadRequestError
from util.submission_files import (
    normalize_submission_files,
    required_submission_files,
    resolve_submission_name,
)


@pytest.mark.parametrize("value, expected", [
    (None, None),
    ([], None),
    ("", None),
    (["calculator.py"], ["calculator.py"]),
    ([" calculator.py ", ""], ["calculator.py"]),
    ("Main.java, Helper.java", ["Main.java", "Helper.java"]),
])
def test_normalize_submission_files(value, expected):
    assert normalize_submission_files(value) == expected


@pytest.mark.parametrize("value, message", [
    (["../calc.py"], "Invalid file name: ../calc.py. Try calc.py."),
    (["my calc.py"], "Invalid file name: my calc.py. Try my_calc.py."),
    (["calculator"], "File name needs an extension: calculator"),
    (["a.py", "a.py"], "Duplicate file name: a.py"),
    ({"name": "a.py"}, "submission_files must be a list of file names"),
    ([3], "submission_files must be a list of file names"),
])
def test_normalize_submission_files_rejects(value, message):
    with pytest.raises(BadRequestError) as exc:
        normalize_submission_files(value)
    assert str(exc.value) == message


def test_normalize_submission_files_limits_count():
    with pytest.raises(BadRequestError):
        normalize_submission_files([f"f{i}.py" for i in range(21)])


def test_required_submission_files_ignores_non_list():
    assert required_submission_files(SimpleNamespace(submission_files=None)) == []
    assert required_submission_files(SimpleNamespace()) == []
    assert required_submission_files(SimpleNamespace(submission_files=["a.py"])) == ["a.py"]


@pytest.mark.parametrize("required, client_name, expected", [
    (["calculator.py"], "a2.py", "calculator.py"),
    (["Main.java", "Helper.java"], "x.java", "Main.java"),
    (None, "answer.py", "answer.py"),
    (None, "../../etc/evil.py", "etc_evil.py"),
    (None, "", "solution.py"),
    (None, None, "solution.py"),
])
def test_resolve_submission_name(required, client_name, expected):
    assignment = SimpleNamespace(submission_files=required)
    assert resolve_submission_name(assignment, client_name) == expected
