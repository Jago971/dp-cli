"""Shared pytest helpers for the CI-script tests."""
import shutil
import subprocess
from pathlib import Path

import dp

SOURCE = Path(__file__).resolve().parents[2] / "plugins" / "datumpin" / "dp" / "src"
assert Path(dp.__file__).resolve().is_relative_to(SOURCE), (
    f"dp imported from {dp.__file__}, not the source tree: uninstall the installed copy (pip uninstall datumpin-dp)"
)


def docker_works():
    """True when a Docker daemon answers; the integration tests skip without one."""
    return bool(shutil.which("docker")) and subprocess.run(
        ["docker", "info"], capture_output=True).returncode == 0
