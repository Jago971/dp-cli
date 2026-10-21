"""Shared pytest helpers for the CI-script tests."""
import shutil
import subprocess


def docker_works():
    """True when a Docker daemon answers; the integration tests skip without one."""
    return bool(shutil.which("docker")) and subprocess.run(
        ["docker", "info"], capture_output=True).returncode == 0
