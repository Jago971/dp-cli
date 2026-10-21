"""Tests for ci/push-image.sh against a throwaway local registry.

The registry runs on the host's Docker, published on a loopback port the
daemon can push to; the registry's own answers are read from a container in
its network namespace, so the test also works from a CI job container.
Integration tier: needs a Docker daemon, and skips without one.
"""
import os
import subprocess
import uuid

import pytest
from conftest import docker_works

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "push-image.sh")
MANIFEST_TYPES = ("application/vnd.oci.image.manifest.v1+json,"
                  "application/vnd.docker.distribution.manifest.v2+json")

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(not docker_works(), reason="needs a Docker daemon")]


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout.strip()


def image_id(tag):
    result = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", tag],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


@pytest.fixture
def registry():
    name = f"push-image-test-{uuid.uuid4().hex[:8]}"
    docker("run", "-d", "--name", name, "-p", "127.0.0.1::5000", "registry:2")
    port = docker("port", name, "5000").splitlines()[0].rsplit(":", 1)[1]
    yield name, f"localhost:{port}"
    docker("rm", "-f", name)
    for tag in docker("images", "--format", "{{.Repository}}:{{.Tag}}",
                      "--filter", f"reference=localhost:{port}/*").splitlines():
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)


@pytest.fixture
def build(tmp_path):
    tags = []

    def make(marker):
        (tmp_path / "Dockerfile").write_text(f"FROM alpine:3.20\nRUN echo {marker} > /marker\n")
        tag = f"push-image-test-local:{uuid.uuid4().hex[:8]}"
        docker("build", "-q", "-t", tag, str(tmp_path))
        tags.append(tag)
        return tag

    yield make
    for tag in tags:
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)


def served_manifest(registry_name, repo, tag):
    """The manifest the registry serves for repo:tag."""
    return docker("run", "--rm", "--network", f"container:{registry_name}", "alpine:3.20",
                  "wget", "-q", "-O-", "--header", f"Accept: {MANIFEST_TYPES}",
                  f"http://localhost:5000/v2/{repo}/manifests/{tag}")


def test_push_leaves_host_tag_on_the_image_it_had(registry, build):
    name, host = registry
    deployed = build("old")
    docker("tag", deployed, f"{host}/app:prep")  # what the host runs
    new = build("new")

    subprocess.run(["bash", SCRIPT, new, f"{host}/app:prep", f"{host}/app:prep-abc1234"],
                   check=True, capture_output=True, text=True)

    assert image_id(f"{host}/app:prep") == image_id(deployed)
    assert image_id(f"{host}/app:prep-abc1234") is None
    assert served_manifest(name, "app", "prep") == served_manifest(name, "app", "prep-abc1234")
    docker("pull", "-q", f"{host}/app:prep-abc1234")  # an absent tag: pulling it disturbs nothing
    assert image_id(f"{host}/app:prep-abc1234") == image_id(new)
