"""Checks the sandbox limits against real Docker. Skipped when Docker is not running."""
import json
import os
import shutil
import uuid

import pytest

docker = pytest.importorskip("docker")

from api import create_app  # noqa: E402
from util.sandbox import container_run_kwargs  # noqa: E402

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "assignment-examples")


def _docker_client():
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        return None


CLIENT = _docker_client()
pytestmark = pytest.mark.skipif(CLIENT is None, reason="Docker is not running")


@pytest.fixture
def app():
    app = create_app("config.TestConfig")
    with app.app_context():
        yield app


def _run_snippet(code, timeout=20):
    from routes import code_editor

    return code_editor._run_code_in_container("python:3.11-slim", code, "main.py", timeout)


def test_run_code_has_no_network(app):
    stdout, stderr, rc = _run_snippet(
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        "    print('CONNECTED')\n"
        "except OSError as e:\n"
        "    print('BLOCKED', type(e).__name__)\n"
    )
    assert "BLOCKED" in stdout, (stdout, stderr)


def test_run_code_runs_as_nobody(app):
    stdout, stderr, rc = _run_snippet("import os; print(os.getuid(), os.getgid())")
    assert stdout.strip() == "65534 65534", (stdout, stderr)


def test_run_code_process_limit_stops_fork_storm(app):
    stdout, stderr, rc = _run_snippet(
        "import os, time\n"
        "n = 0\n"
        "try:\n"
        "    for _ in range(2000):\n"
        "        if os.fork() == 0:\n"
        "            time.sleep(5)\n"
        "            os._exit(0)\n"
        "        n += 1\n"
        "except OSError:\n"
        "    print('LIMITED', n, flush=True)\n"
        "    os._exit(0)\n"
        "print('UNLIMITED', n)\n",
        timeout=30,
    )
    assert "LIMITED" in stdout, (stdout, stderr)


def test_run_code_memory_limit_kills_big_allocation(app):
    stdout, stderr, rc = _run_snippet("x = bytearray(2 * 1024 ** 3)\nprint('ALLOCATED')\n")
    assert "ALLOCATED" not in stdout
    assert rc != 0


@pytest.fixture(scope="module")
def a1_image(tmp_path_factory):
    build_dir = tmp_path_factory.mktemp("a1")
    shutil.copy(os.path.join(EXAMPLES, "A1", "A1.zip"), build_dir / "A1.zip")
    (build_dir / "Dockerfile").write_text(
        "FROM python:3.9-slim\n"
        "RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-dev unzip "
        "&& rm -rf /var/lib/apt/lists/*\n"
        "COPY *.zip /autograder/\n"
        "RUN unzip /autograder/*.zip -d /autograder/source && "
        "chmod +x /autograder/source/setup.sh && /autograder/source/setup.sh && "
        "chmod +x /autograder/source/run_autograder && mkdir -p /autograder/results /autograder/submission\n"
        "WORKDIR /autograder\n"
    )
    tag = f"codeassist-sandbox-it:{uuid.uuid4().hex[:8]}"
    CLIENT.images.build(path=str(build_dir), tag=tag)
    yield tag
    CLIENT.images.remove(tag, force=True)


def test_persistent_grading_container_still_grades_with_limits(app, a1_image, tmp_path):
    from routes import submission

    container = CLIENT.containers.run(
        image=a1_image,
        name=f"sandbox_it_{uuid.uuid4().hex[:8]}",
        detach=True,
        tty=True,
        command="tail -f /dev/null",
        **container_run_kwargs(),
    )
    try:
        code = tmp_path / "calculator.py"
        shutil.copy(os.path.join(EXAMPLES, "A1", "calculator.py"), code)
        proc = submission.run_grading(container, str(code), "calculator.py", 60)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        results = json.loads(proc.stdout)
        assert results["score"] > 0
    finally:
        container.remove(force=True)


def test_editor_autograder_run_grades_as_nobody(app, a1_image):
    from routes import code_editor

    with open(os.path.join(EXAMPLES, "A1", "calculator.py")) as f:
        content = f.read()
    results = code_editor._run_autograder_in_container(
        a1_image, content, "calculator.py", f"it-{uuid.uuid4().hex[:8]}", 60
    )
    assert results is not None
    assert results["score"] > 0


FORK_TO_THE_LIMIT = """
import os, time
for _ in range(2000):
    try:
        if os.fork() == 0:
            time.sleep(600)
            os._exit(0)
    except OSError:
        break
"""


def _sandbox_process_count(container):
    """Live (non-zombie) processes owned by the sandbox user."""
    cmd = "for f in /proc/[0-9]*/status; do grep -q '^Uid:[[:space:]]*65534' $f && ! grep -q '^State:[[:space:]]*Z' $f && echo x; done 2>/dev/null | wc -l"
    out = container.exec_run(["sh", "-c", cmd])
    return int(out.output.decode().strip() or 0)


def _zombie_count(container):
    out = container.exec_run(["sh", "-c", "grep -l '^State:[[:space:]]*Z' /proc/[0-9]*/status 2>/dev/null | wc -l"])
    return int(out.output.decode().strip() or 0)


def test_forking_submission_does_not_starve_the_next_one(app, a1_image, tmp_path):
    """A submission that forks to pids_limit must not leave zombies that eat
    the next students' process budget (found in review of #401: the next A1
    submissions scored 16/20 instead of 20/20)."""
    from types import SimpleNamespace

    from routes import submission

    assignment = SimpleNamespace(autograder_image_name=a1_image, id="it")
    container = submission._run_assignment_container(assignment, f"sandbox_it_{uuid.uuid4().hex[:8]}")
    try:
        good = tmp_path / "good" / "calculator.py"
        good.parent.mkdir()
        shutil.copy(os.path.join(EXAMPLES, "A1", "calculator.py"), good)
        bad = tmp_path / "bad" / "calculator.py"
        bad.parent.mkdir()
        bad.write_text(FORK_TO_THE_LIMIT)

        def grade(path):
            proc = submission.run_grading(container, str(path), "calculator.py", 60)
            assert proc.returncode == 0, proc.stderr.decode(errors="replace")
            return json.loads(proc.stdout)["score"]

        baseline = grade(good)
        grade(bad)
        assert _zombie_count(container) == 0
        assert _sandbox_process_count(container) == 0
        container.reload()
        assert container.status == "running"
        assert grade(good) == baseline
        assert grade(good) == baseline
    finally:
        container.remove(force=True)
