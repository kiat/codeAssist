import os
import tempfile
from pathlib import Path


LOCAL_PYTEST_TEMP_ROOT = Path(__file__).resolve().parent / ".pytest_tmp_root"
LOCAL_PYTEST_TEMP_ROOT.mkdir(exist_ok=True)
LOCAL_PYTEST_RUN_TEMP = LOCAL_PYTEST_TEMP_ROOT / f"run-{os.getpid()}"

for env_name in ("TMPDIR", "TEMP", "TMP"):
    os.environ[env_name] = str(LOCAL_PYTEST_TEMP_ROOT)

tempfile.tempdir = str(LOCAL_PYTEST_TEMP_ROOT)


def pytest_configure(config):
    if not config.option.basetemp:
        config.option.basetemp = str(LOCAL_PYTEST_RUN_TEMP)
