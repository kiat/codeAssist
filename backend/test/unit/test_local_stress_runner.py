import importlib.util
import sys
from pathlib import Path

import pytest


def load_runner():
    runner_path = (
        Path(__file__).resolve().parents[1]
        / "stress"
        / "run_local_stress_tests.py"
    )
    spec = importlib.util.spec_from_file_location("run_local_stress_tests", runner_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_stress_module(filename, module_name):
    module_path = Path(__file__).resolve().parents[1] / "stress" / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(module_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(module_path.parent))
    return module


def test_rejects_literal_course_id_placeholder():
    runner = load_runner()

    with pytest.raises(ValueError, match="Replace COURSE_ID"):
        runner.normalize_course_id("<course_id>", required=True)


def test_builds_assignment_creation_command_without_duplicate_course_id():
    runner = load_runner()
    case = runner.get_case("assignment_creation")
    script_dir = Path("backend/test/stress")

    command = runner.build_command(
        case=case,
        course_id="course-123",
        quick=True,
        script_dir=script_dir,
    )

    assert command == [
        runner.sys.executable,
        str(script_dir / "create_assignments.py"),
        "2",
        "course-123",
    ]


def test_safe_selection_excludes_known_incompatible_api_tests():
    runner = load_runner()

    selected_names = [case.name for case in runner.select_cases(run_safe=True)]

    assert "bulk_uploads" in selected_names
    assert "student_submissions" in selected_names
    assert "assignment_creation" in selected_names
    assert "concurrent_enrollment" not in selected_names
    assert "crud_operations" not in selected_names


def test_stress_utils_base_url_can_be_overridden(monkeypatch):
    monkeypatch.setenv("STRESS_BASE_URL", "http://localhost:5999")

    utils = load_stress_module("utils.py", "stress_utils_env_test")

    assert utils.BASE_URL == "http://localhost:5999"


def test_create_assignment_accepts_extra_submission_ready_fields(monkeypatch):
    utils = load_stress_module("utils.py", "stress_utils_payload_test")
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "assignment-123"}

    def fake_post(url, json):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(utils.requests, "post", fake_post)

    assignment_id = utils.create_assignment(
        "Submission Ready",
        "course-123",
        published=True,
        published_date=None,
        due_date=None,
    )

    assert assignment_id == "assignment-123"
    assert captured["json"] == {
        "name": "Submission Ready",
        "course_id": "course-123",
        "published": True,
        "published_date": None,
        "due_date": None,
    }


def test_assignment_creation_artifact_lives_under_results_folder():
    create_assignments = load_stress_module(
        "create_assignments.py",
        "stress_create_assignments_artifact_test",
    )

    artifact_path = Path(create_assignments.ASSIGNMENT_IDS_FILE)

    assert artifact_path.parent.name == "results"
    assert artifact_path.name == "generated_assignments.json"
