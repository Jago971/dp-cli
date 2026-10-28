"""Unit tier: the plugin's skills load lightly - short descriptions, every sibling file linked."""
from pathlib import Path

import pytest
import yaml

SKILLS = Path(__file__).resolve().parents[2] / "plugins" / "datumpin" / "skills"
DESCRIPTION_LIMIT = 160  # writing-for-agents, The two loads: every description is in context every turn


def skill_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def frontmatter(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").removeprefix("---\n").partition("\n---\n")[0])


@pytest.mark.unit
@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.parent.name)
def test_a_skill_description_is_160_characters_or_fewer(path):
    assert len(frontmatter(path)["description"]) <= DESCRIPTION_LIMIT


@pytest.mark.unit
@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.parent.name)
def test_every_sibling_file_is_linked_from_its_skill(path):
    text = path.read_text(encoding="utf-8")
    siblings = [f.name for f in path.parent.glob("*.md") if f.name != "SKILL.md"]

    assert [name for name in siblings if f"({name})" not in text and f"(./{name})" not in text] == []


def skill_text(name, file="SKILL.md"):
    return (SKILLS / name / file).read_text(encoding="utf-8")


@pytest.mark.unit
def test_gitea_defines_dod_as_waiting_for_the_milestone_sign_off():
    text = skill_text("gitea")

    assert "waiting for its milestone's sign-off" in text
    assert "Feature DoD signed" not in text


@pytest.mark.unit
def test_change_ready_promotion_gate_is_per_milestone_and_the_model_never_signs():
    text = skill_text("change-ready")
    gate = text.partition("## Promotion gate")[2].partition("\n## ")[0]

    assert "per milestone" in gate
    assert "evidence pack" in gate
    assert "never signs" in gate


@pytest.mark.unit
def test_gitea_workflows_describes_the_release_pr_per_milestone_and_its_tag():
    text = skill_text("gitea-workflows")

    assert "release PR per milestone" in text
    assert "tag" in text.partition("release PR per milestone")[2][:400]


@pytest.mark.unit
def test_formats_milestone_shape_says_it_is_gated_by_dod():
    shape = skill_text("formats", "gitea.md").partition("## Milestone")[2].partition("\n## ")[0]

    assert "gated by DoD" in shape


@pytest.mark.unit
def test_no_doc_still_says_dod_means_feature_signed():
    root = SKILLS.parents[2]
    files = [*root.joinpath("plugins").rglob("*.md"), *root.joinpath("docs").rglob("*.md"), root / "README.md"]
    stale = [str(f) for f in files if "Feature DoD signed" in f.read_text(encoding="utf-8") and f.name != "CHANGELOG.md"]

    assert stale == []
