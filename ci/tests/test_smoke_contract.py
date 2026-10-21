"""Tests for the smoke-test contract docker-image runs, as CI runs it.

smoke-example.sh is the shape a repo's smoke script follows. In CI, pytest
runs in a job container beside the Docker daemon, as docker-image's step
does, so a script relying on host ports fails here too; run on a host
directly, this test cannot catch that.
Integration tier: needs a Docker daemon, and skips without one.
"""
import os
import subprocess
import uuid

import pytest
from conftest import docker_works

EXAMPLE = os.path.join(os.path.dirname(__file__), "smoke-example.sh")


pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(not docker_works(), reason="needs a Docker daemon")]


@pytest.fixture
def web_image(tmp_path):
    """Builds a tiny web server image serving "ok" on the given port."""
    tags = []

    def build(port):
        (tmp_path / "Dockerfile").write_text(
            "FROM python:3.12-alpine\n"
            "RUN mkdir /www && echo ok > /www/index.html\n"
            f'CMD ["python", "-m", "http.server", "{port}", "-d", "/www"]\n')
        tag = f"smoke-contract-test:{uuid.uuid4().hex[:8]}"
        subprocess.run(["docker", "build", "-q", "-t", tag, str(tmp_path)], check=True, capture_output=True)
        tags.append(tag)
        return tag

    yield build
    for tag in tags:
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)


def smoke(tag):
    return subprocess.run(["bash", EXAMPLE, tag], capture_output=True, text=True, timeout=120)


def test_smoke_working_image_passes(web_image):
    assert smoke(web_image(8080)).returncode == 0


def test_smoke_broken_image_fails(web_image):
    result = smoke(web_image(9999))  # answers on the wrong port

    assert result.returncode == 1
    assert "FAIL" in result.stdout
