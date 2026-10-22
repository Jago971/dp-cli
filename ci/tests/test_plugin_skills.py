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
