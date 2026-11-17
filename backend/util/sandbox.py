"""Resource and privilege limits for every container that runs student code.

Every `containers.run` call that can execute student or autograder code takes
its limits from `container_run_kwargs`, so the sandbox is set in one place.
"""
from flask import current_app, has_app_context

# Student and autograder code runs as nobody, never as root.
SANDBOX_UID = 65534
SANDBOX_USER = f"{SANDBOX_UID}:{SANDBOX_UID}"

# Bumped whenever the limits below change, so persistent assignment containers
# created with older limits get recreated (see routes/submission.py).
SANDBOX_VERSION = "2"
SANDBOX_LABEL = "codeassist.sandbox"

DEFAULT_MEM_LIMIT = "512m"
DEFAULT_JAVA_MEM_LIMIT = "1g"
DEFAULT_CPUS = 1.0
DEFAULT_PIDS_LIMIT = 256

# What a root `docker exec` needs to reset a container and drop to nobody:
# chown/delete files nobody created (CHOWN, DAC_OVERRIDE, FOWNER), switch user
# with setpriv (SETUID, SETGID) and kill leftover processes (KILL). Everything
# else, e.g. NET_RAW, MKNOD and SYS_CHROOT, stays dropped.
SUPERVISOR_CAPS = ["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID", "KILL"]


def _config(name, default):
    if has_app_context():
        return current_app.config.get(name, default)
    return default


def container_run_kwargs(language="python", supervisor=True):
    """Keyword arguments for docker's `containers.run`.

    supervisor=True keeps the few capabilities a root `docker exec` needs to
    run the autograder as nobody (see RUN_AUTOGRADER_AS_NOBODY). Use False for
    containers whose processes all run as nobody, together with
    `user=SANDBOX_USER`.
    """
    mem_limit = (
        _config("SANDBOX_JAVA_MEM_LIMIT", DEFAULT_JAVA_MEM_LIMIT)
        if language == "java"
        else _config("SANDBOX_MEM_LIMIT", DEFAULT_MEM_LIMIT)
    )
    cpus = float(_config("SANDBOX_CPUS", DEFAULT_CPUS))
    kwargs = {
        "network_disabled": bool(_config("SANDBOX_NETWORK_DISABLED", True)),
        "mem_limit": mem_limit,
        # Same as mem_limit: no extra swap on top of the memory limit.
        "memswap_limit": mem_limit,
        "nano_cpus": int(cpus * 1_000_000_000),
        "pids_limit": int(_config("SANDBOX_PIDS_LIMIT", DEFAULT_PIDS_LIMIT)),
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "labels": {SANDBOX_LABEL: SANDBOX_VERSION},
        # Docker's init (tini) as PID 1 reaps orphaned processes. Without it,
        # PID 1 is `tail -f /dev/null`, which never reaps, so processes killed
        # by the reset between submissions stay as zombies, still count
        # toward pids_limit, and starve the next submissions.
        "init": True,
    }
    if supervisor:
        kwargs["cap_add"] = list(SUPERVISOR_CAPS)
    return kwargs


def container_sandbox_is_stale(container):
    """True when `container` was created before the current sandbox limits."""
    try:
        labels = container.labels
    except Exception:
        return False
    if labels is None:
        labels = {}
    if not isinstance(labels, dict):
        return False
    return labels.get(SANDBOX_LABEL) != SANDBOX_VERSION


# Runs the autograder as nobody inside a container whose `docker exec` runs as
# root. Used by the one-off containers (rerun, test autograder, editor runs);
# the persistent assignment container has its own fuller script in
# routes/submission.py. Exit code 90 means the container could not be prepared.
RUN_AUTOGRADER_AS_NOBODY = f"""
mkdir -p /autograder/submission /autograder/results || exit 90
chown -R {SANDBOX_USER} /autograder/source /autograder/submission /autograder/results || exit 90
cd /autograder && HOME=/tmp setpriv --reuid={SANDBOX_UID} --regid={SANDBOX_UID} --clear-groups \\
    /bin/bash /autograder/source/run_autograder
"""


def run_autograder_command(container_name):
    """argv for `subprocess.run` that runs the autograder as nobody."""
    return ["docker", "exec", container_name, "sh", "-c", RUN_AUTOGRADER_AS_NOBODY]
