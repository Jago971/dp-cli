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
# A BuildKit build (as in CI) pushes an image index with its attestations;
# the legacy builder pushes a single manifest. Accept either.
MANIFEST_TYPES = ("application/vnd.oci.image.index.v1+json,"
                  "application/vnd.oci.image.manifest.v1+json,"
                  "application/vnd.docker.distribution.manifest.list.v2+json,"
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
    """Starts registry:2 on a random loopback port; removes it and every tag under it afterwards."""
    name = f"push-image-test-{uuid.uuid4().hex[:8]}"
    docker("run", "-d", "--name", name, "-p", "127.0.0.1::5000", "registry:2")
    port = docker("port", name, "5000").splitlines()[0].rsplit(":", 1)[1]
    yield name, f"localhost:{port}"
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    tags = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}",
                           "--filter", f"reference=localhost:{port}/*"],
                          capture_output=True, text=True).stdout.split()
    for tag in tags:
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)


@pytest.fixture
def build(tmp_path):
    """Builds a one-file image under a throwaway local tag; removes the tags afterwards."""
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


def push(local, *tags):
    result = subprocess.run(["bash", SCRIPT, local, *tags], capture_output=True, text=True)
    print(result.stdout, result.stderr)  # shown when a test fails
    assert result.returncode == 0


def test_push_tag_the_host_runs_from_keeps_it_on_its_image(registry, build):
    name, host = registry
    deployed = build("old")
    docker("tag", deployed, f"{host}/app:prep")
    docker("image", "rm", deployed)  # as on the host: :prep is the old image's only tag
    deployed_id = image_id(f"{host}/app:prep")
    new = build("new")
    docker("tag", new, f"{host}/app:reference")
    docker("push", "-q", f"{host}/app:reference")  # what the registry serves for the new image

    push(new, f"{host}/app:prep")

    assert image_id(f"{host}/app:prep") == deployed_id
    assert served_manifest(name, "app", "prep") == served_manifest(name, "app", "reference")


def test_push_tag_absent_on_host_removes_it_afterwards(registry, build):
    _, host = registry
    new = build("new")

    push(new, f"{host}/app:prep-abc1234")

    assert image_id(f"{host}/app:prep-abc1234") is None
    docker("pull", "-q", f"{host}/app:prep-abc1234")
    assert image_id(f"{host}/app:prep-abc1234") == image_id(new)
