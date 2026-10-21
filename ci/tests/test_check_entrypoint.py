"""Tests for ci/check-entrypoint.sh against tiny images built on the spot.

Integration tier: needs a Docker daemon, and skips without one.
"""
import os
import shutil
import subprocess
import uuid

import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "check-entrypoint.sh")


def docker_works():
    return shutil.which("docker") and subprocess.run(
        ["docker", "info"], capture_output=True).returncode == 0


pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(not docker_works(), reason="needs a Docker daemon")]


@pytest.fixture
def image(tmp_path):
    """Builds an image from Dockerfile lines; removes it afterwards."""
    tags = []

    def build(*lines):
        (tmp_path / "entry.sh").write_text("#!/bin/sh\nexec \"$@\"\n")
        (tmp_path / "Dockerfile").write_text("\n".join(lines) + "\n")
        tag = f"check-entrypoint-test:{uuid.uuid4().hex[:8]}"
        subprocess.run(["docker", "build", "-q", "-t", tag, str(tmp_path)], check=True, capture_output=True)
        tags.append(tag)
        return tag

    yield build
    for tag in tags:
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)


def check(tag):
    return subprocess.run(["bash", SCRIPT, tag], capture_output=True, text=True)


def test_check_executable_entrypoint_passes(image):
    tag = image("FROM alpine:3.20", "COPY entry.sh /entry.sh", "RUN chmod 755 /entry.sh",
                'ENTRYPOINT ["/entry.sh"]')

    assert check(tag).returncode == 0


def test_check_non_executable_entrypoint_fails_naming_it(image):
    tag = image("FROM alpine:3.20", "COPY entry.sh /entry.sh", "RUN chmod 644 /entry.sh",
                'ENTRYPOINT ["/entry.sh"]')

    result = check(tag)

    assert result.returncode == 1
    assert "/entry.sh" in result.stdout + result.stderr


def test_check_image_without_entrypoint_passes(image):
    tag = image("FROM alpine:3.20")

    assert check(tag).returncode == 0
