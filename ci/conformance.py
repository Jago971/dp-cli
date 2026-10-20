"""Checks that a repo uses the datumpin plugin and workflow the standard way.

Run from CI through DEVKIT's conformance workflow, or by hand:

    python ci/conformance.py <repo-root>

Each check prints PASS, FAIL or SKIP with the rule it enforces; the exit code
is 1 when any check fails. The rules come from the plugin's skills
(claude-md-authoring, documentation-cross-cutting, gitea-workflows) and the
plugin README's onboarding list; this script only makes the mechanical ones
automatic. A repo skips a check that does not apply by naming it in its
.claude/flow.yaml:

    conformance:
      skip: [changelog]   # with a comment saying why

Standard library only, so it runs anywhere Python does.
"""
import json
import re
import sys
from pathlib import Path

MARKETPLACE = {"source": "git", "url": "git@gitea:Datumpin/DEVKIT.git", "ref": "main"}
SECTIONS = ["Response style", "Engineering principles", "Git commits and PRs", "Skills and workflow"]
PRINCIPLES = ["Secure", "Modular", "Reusable", "Conventional", "Simple", "Readable", "Maintainable",
              "Follow established patterns"]
DOCS = {
    "quickstart": "docs/QUICKSTART.md",
    "docs-index": "docs/README.md",
    "roadmap": "docs/plan/ROADMAP.md",
    "changelog": "docs/log/CHANGELOG.md",
}
DEVKIT_CALL = re.compile(r"uses:\s*Datumpin/DEVKIT/\.gitea/workflows/([\w.-]+)@(\S+)")


def read(root, rel):
    path = root / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else None


def skipped(root):
    flow = read(root, ".claude/flow.yaml") or ""
    match = re.search(r"^conformance:\s*\n\s+skip:\s*\[([^\]]*)\]", flow, re.M)
    return {name.strip() for name in match.group(1).split(",")} if match else set()


def check_settings(root):
    text = read(root, ".claude/settings.json")
    if text is None:
        return False, ".claude/settings.json is missing"
    data = json.loads(text)
    source = data.get("extraKnownMarketplaces", {}).get("datumpin", {}).get("source")
    if source != MARKETPLACE:
        return False, f"the datumpin marketplace must be {MARKETPLACE}, found {source}"
    if data.get("enabledPlugins", {}).get("datumpin@datumpin") is not True:
        return False, "datumpin@datumpin is not enabled"
    return True, "the plugin installs from DEVKIT main"


def check_flow(root):
    flow = read(root, ".claude/flow.yaml")
    if flow is None or not re.search(r"^components:\s*\n\s+[A-Z][A-Z0-9-]*:", flow, re.M):
        return False, ".claude/flow.yaml must declare components"
    return True, ".claude/flow.yaml declares components"


def check_claude_sections(root):
    text = read(root, "CLAUDE.md")
    if text is None:
        return False, "CLAUDE.md is missing"
    headings = re.findall(r"^## (.+?)\s*$", text, re.M)[:len(SECTIONS)]
    if headings != SECTIONS:
        return False, f"CLAUDE.md must open with {SECTIONS}, found {headings}"
    return True, "CLAUDE.md opens with the four standard sections in order"


def check_claude_principles(root):
    text = read(root, "CLAUDE.md") or ""
    block = re.search(r"^## Engineering principles\s*$(.*?)(?=^## )", text, re.M | re.S)
    names = re.findall(r"^- \*\*([^:*]+):\*\*", block.group(1), re.M) if block else []
    missing = [p for p in PRINCIPLES if p not in names]
    if missing:
        return False, f"Engineering principles is missing {missing}"
    return True, "the eight core principles are present"


def check_factory_ignored(root):
    lines = (read(root, ".gitignore") or "").splitlines()
    if ".factory/" not in [line.strip() for line in lines]:
        return False, ".gitignore must ignore .factory/"
    return True, ".factory/ is ignored"


def check_no_skills_copy(root):
    if (root / "skills").exists():
        return False, "a root skills/ copy exists; the plugin provides the skills"
    return True, "no root skills/ copy"


def check_ci(root):
    text = read(root, ".gitea/workflows/ci.yml")
    if text is None:
        return False, ".gitea/workflows/ci.yml is missing"
    if (root / ".claude-plugin" / "marketplace.json").exists():
        ok = "uses: ./.gitea/workflows/" in text
        return ok, "DEVKIT's ci.yml calls its own workflows from the checkout" if ok else \
            "DEVKIT's ci.yml must call its workflows from the checkout (./.gitea/workflows/)"
    calls = DEVKIT_CALL.findall(text)
    wrong = sorted({f"{name}@{ref}" for name, ref in calls if ref != "main"})
    if not calls:
        return False, "ci.yml calls no DEVKIT shared workflow"
    if wrong:
        return False, f"DEVKIT calls must pin @main: {wrong}"
    if "conformance.yml" not in {name for name, _ in calls}:
        return False, "ci.yml must call DEVKIT's conformance workflow"
    return True, f"ci.yml calls DEVKIT @main ({len(calls)} jobs)"


def doc_check(rel):
    def check(root):
        if not (root / rel).exists():
            return False, f"{rel} is missing"
        return True, f"{rel} exists"
    return check


CHECKS = {
    "settings": check_settings,
    "flow": check_flow,
    "claude-sections": check_claude_sections,
    "claude-principles": check_claude_principles,
    "factory-ignored": check_factory_ignored,
    "no-skills-copy": check_no_skills_copy,
    "ci": check_ci,
    **{name: doc_check(rel) for name, rel in DOCS.items()},
}


def main(root):
    skip = skipped(root)
    failed = 0
    for name, check in CHECKS.items():
        if name in skip:
            print(f"SKIP  {name}: skipped in .claude/flow.yaml")
            continue
        ok, detail = check(root)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    unknown = skip - set(CHECKS)
    for name in sorted(unknown):
        failed += 1
        print(f"FAIL  {name}: no such check (conformance.skip in .claude/flow.yaml)")
    print(f"{len(CHECKS) - failed - len(skip & set(CHECKS))} passed, {failed} failed, {len(skip & set(CHECKS))} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
