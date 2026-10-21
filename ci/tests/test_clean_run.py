"""Tests for ci/clean-run.sh and the run label the smoke-test contract uses.

Integration tier: needs a Docker daemon, and skips without one.
"""
import os
import subprocess
import time
import uuid

import pytest
from conftest import docker_works

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "clean-run.sh")
EXAMPLE = os.path.join(HERE, "smoke-example.sh")
LABEL_KEY = "datumpin.ci-run"

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(not docker_works(), reason="needs a Docker daemon")]


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout.strip()


def labelled(kind, run):
    """Ids of containers or networks carrying the run label."""
    listing = ["ps", "-aq"] if kind == "container" else ["network", "ls", "-q"]
    return docker(*listing, "--filter", f"label={LABEL_KEY}={run}").split()


@pytest.fixture
def run():
    """A fresh run label; removes anything still carrying it afterwards."""
    value = f"test-{uuid.uuid4().hex[:8]}"
    yield value
    for cid in labelled("container", value):
        subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
    for nid in labelled("network", value):
        subprocess.run(["docker", "network", "rm", nid], capture_output=True)


def test_clean_run_removes_only_what_carries_the_label(run):
    docker("network", "create", "--label", f"{LABEL_KEY}={run}", f"clean-{run}")
    docker("run", "-d", "--label", f"{LABEL_KEY}={run}", "--network", f"clean-{run}",
           "alpine:3.20", "sleep", "300")
    other = docker("run", "-d", "alpine:3.20", "sleep", "300")
    try:
        subprocess.run(["bash", CLEAN, run], check=True, capture_output=True, text=True)

        assert labelled("container", run) == []
        assert labelled("network", run) == []
        assert docker("ps", "-q", "--filter", f"id={other}") != ""
    finally:
        subprocess.run(["docker", "rm", "-f", other], capture_output=True)


def test_smoke_example_labels_what_it_starts(run, tmp_path):
    (tmp_path / "Dockerfile").write_text('FROM alpine:3.20\nCMD ["sleep", "300"]\n')  # never answers
    tag = f"clean-run-test:{uuid.uuid4().hex[:8]}"
    docker("build", "-q", "-t", tag, str(tmp_path))
    smoke = subprocess.Popen(["bash", EXAMPLE, tag], env={**os.environ, "CI_RUN_LABEL": run},
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(4)  # inside its retry loop

        assert len(labelled("container", run)) >= 1
        assert len(labelled("network", run)) == 1
    finally:
        smoke.kill()
        smoke.wait()
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)
