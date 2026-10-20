"""Reports where a repo's pinned dependency versions differ from the master copies.

Run by the `versions` job of DEVKIT's security-scan workflow, or by hand:

    python ci/versions.py <repo-root>

The master copies (ci/master/requirements.txt and ci/master/package.json) are
the fleet's approved versions: changing one is a DEVKIT PR, reviewed in OWASP
Dependency-Track and approved by an Owner (the gitea-workflows skill,
Dependency versions). This only reports, and always exits 0: osv-scanner is
the blocking check for known vulnerabilities, and a newer patch in one repo
should not stop a PR.

    DRIFT  a different minor or patch version than the master
    MAJOR  a different major version (louder: a breaking upgrade or a lag)

Packages the masters do not list are counted, not reported one by one.
Standard library only.
"""
import json
import re
import sys
from pathlib import Path

MASTER = Path(__file__).resolve().parent / "master"
SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", ".devkit", "dist", "build"}


def normalise(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def numbers(version):
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def python_pins(path):
    pins = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_.\-\[\]]+?)(?:\[[^\]]*\])?\s*==\s*([^\s;#]+)", line)
        if match:
            pins[normalise(match.group(1))] = match.group(2)
    return pins


def npm_pins(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    pins = {}
    for section in ("dependencies", "devDependencies"):
        for name, spec in data.get(section, {}).items():
            version = re.sub(r"^[\^~=v]", "", str(spec))
            if re.match(r"^\d", version):
                pins[name] = version
    return pins


def files(root, name_pattern):
    for path in root.rglob(name_pattern):
        if not SKIP_DIRS & set(path.relative_to(root).parts):
            yield path


def compare(pins, master, where, lines):
    unlisted = 0
    for name, version in sorted(pins.items()):
        approved = master.get(name)
        if approved is None:
            unlisted += 1
        elif numbers(version) != numbers(approved):
            kind = "MAJOR" if numbers(version)[:1] != numbers(approved)[:1] else "DRIFT"
            lines.append(f"{kind}  {where}: {name} {version}, master {approved}")
    return unlisted


def main(root):
    master_py = python_pins(MASTER / "requirements.txt")
    master_js = npm_pins(MASTER / "package.json")
    lines, unlisted, checked = [], 0, 0
    for path in files(root, "requirements*.txt"):
        checked += 1
        unlisted += compare(python_pins(path), master_py, path.relative_to(root).as_posix(), lines)
    for path in files(root, "package.json"):
        checked += 1
        unlisted += compare(npm_pins(path), master_js, path.relative_to(root).as_posix(), lines)
    for line in lines:
        print(line)
    print(f"{checked} files checked: {sum(l.startswith('DRIFT') for l in lines)} drift, "
          f"{sum(l.startswith('MAJOR') for l in lines)} major, {unlisted} pins not in the masters")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
