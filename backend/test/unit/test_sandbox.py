import subprocess
from types import SimpleNamespace

import pytest

from api import create_app
from util import sandbox
from util.sandbox import (
    SANDBOX_LABEL,
    SANDBOX_USER,
    SANDBOX_VERSION,
    SUPERVISOR_CAPS,
    container_run_kwargs,
    container_sandbox_is_stale,
    run_autograder_command,
)


@pytest.fixture
def app():
    app = create_app("config.TestConfig")
    with app.app_context():
        yield app


def test_defaults_without_app_context():
    kwargs = container_run_kwargs()
    assert kwargs["network_disabled"] is True
    assert kwargs["mem_limit"] == sandbox.DEFAULT_MEM_LIMIT
    assert kwargs["memswap_limit"] == kwargs["mem_limit"]
    assert kwargs["nano_cpus"] == 1_000_000_000
    assert kwargs["pids_limit"] == sandbox.DEFAULT_PIDS_LIMIT
    assert kwargs["cap_drop"] == ["ALL"]
    assert kwargs["security_opt"] == ["no-new-privileges"]
    assert kwargs["cap_add"] == SUPERVISOR_CAPS
    assert kwargs["labels"] == {SANDBOX_LABEL: SANDBOX_VERSION}


def test_java_gets_more_memory():
    assert container_run_kwargs("java")["mem_limit"] == sandbox.DEFAULT_JAVA_MEM_LIMIT


def test_no_supervisor_keeps_no_capabilities():
    kwargs = container_run_kwargs(supervisor=False)
    assert "cap_add" not in kwargs
    assert kwargs["cap_drop"] == ["ALL"]


def test_config_overrides(app):
    app.config.update(
        SANDBOX_NETWORK_DISABLED=False,
        SANDBOX_MEM_LIMIT="256m",
        SANDBOX_CPUS=0.5,
        SANDBOX_PIDS_LIMIT=64,
    )
    kwargs = container_run_kwargs()
    assert kwargs["network_disabled"] is False
    assert kwargs["mem_limit"] == "256m"
    assert kwargs["nano_cpus"] == 500_000_000
    assert kwargs["pids_limit"] == 64


def test_capabilities_do_not_include_dangerous_ones():
    for cap in ("SYS_ADMIN", "NET_ADMIN", "NET_RAW", "SYS_PTRACE", "MKNOD"):
        assert cap not in SUPERVISOR_CAPS


@pytest.mark.parametrize(
    "labels,stale",
    [
        ({SANDBOX_LABEL: SANDBOX_VERSION}, False),
        ({SANDBOX_LABEL: "0"}, True),
        ({}, True),
        (None, True),
    ],
)
def test_container_sandbox_is_stale(labels, stale):
    assert container_sandbox_is_stale(SimpleNamespace(labels=labels)) is stale


def test_container_sandbox_is_stale_ignores_unknown_label_types(mocker):
    # A mock container (no real labels dict) must not be treated as stale.
    assert container_sandbox_is_stale(mocker.Mock()) is False


def test_run_autograder_command_drops_to_nobody():
    argv = run_autograder_command("box")
    assert argv[:5] == ["docker", "exec", "box", "sh", "-c"]
    script = argv[5]
    assert "setpriv --reuid=65534 --regid=65534 --clear-groups" in script
    assert "/autograder/source/run_autograder" in script
    assert f"chown -R {SANDBOX_USER}" in script


def _fake_client(mocker):
    client = mocker.Mock()
    container = mocker.Mock()
    container.exec_run.return_value = SimpleNamespace(exit_code=0, output=b'{"score": 1}')
    client.containers.run.return_value = container
    return client


def test_run_code_container_runs_as_nobody_without_capabilities(app, mocker, tmp_path):
    from routes import code_editor

    client = _fake_client(mocker)
    mocker.patch("routes.code_editor.get_docker_client", return_value=client)
    mocker.patch(
        "routes.code_editor.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, b"hi\n", b""),
    )

    code_editor._run_code_in_container("python:3.11-slim", "print('hi')", "main.py", 5)

    kwargs = client.containers.run.call_args.kwargs
    assert kwargs["user"] == SANDBOX_USER
    assert kwargs["network_disabled"] is True
    assert kwargs["cap_drop"] == ["ALL"]
    assert "cap_add" not in kwargs


def test_editor_autograder_run_is_sandboxed(app, mocker):
    from routes import code_editor

    client = _fake_client(mocker)
    mocker.patch("routes.code_editor.get_docker_client", return_value=client)
    run = mocker.patch(
        "routes.code_editor.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, b"", b""),
    )

    code_editor._run_autograder_in_container("img", "x = 1", "main.py", "assignment-1", 5)

    kwargs = client.containers.run.call_args.kwargs
    assert kwargs["network_disabled"] is True
    assert kwargs["pids_limit"] == sandbox.DEFAULT_PIDS_LIMIT
    argv = run.call_args.args[0]
    assert "setpriv --reuid=65534" in argv[-1]


def test_assignment_container_is_sandboxed(app, mocker):
    from routes import submission

    client = _fake_client(mocker)
    mocker.patch("routes.submission.get_docker_client", return_value=client)

    submission._run_assignment_container(SimpleNamespace(autograder_image_name="img"), "name")

    kwargs = client.containers.run.call_args.kwargs
    assert kwargs["network_disabled"] is True
    assert kwargs["cap_drop"] == ["ALL"]
    assert kwargs["cap_add"] == SUPERVISOR_CAPS
    assert kwargs["labels"] == {SANDBOX_LABEL: SANDBOX_VERSION}
