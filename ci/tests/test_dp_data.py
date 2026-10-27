"""Unit tier: dp.data, which finds the flow map and skills packaged or in a source checkout."""
import pytest

import dp


@pytest.mark.unit
def test_a_source_checkout_reads_the_plugins_own_files():
    assert dp.data("flows.yaml").is_file()
    assert dp.data("skills", "board", "SKILL.md").is_file()


@pytest.mark.unit
def test_packaged_data_wins_over_the_source_fallback(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(dp, "files", lambda name: tmp_path)
    assert dp.data("flows.yaml") == tmp_path / "data" / "flows.yaml"


@pytest.mark.unit
def test_an_installed_dp_never_reads_a_folder_beside_site_packages(tmp_path, monkeypatch):
    package = tmp_path / "site-packages" / "dp"
    package.mkdir(parents=True)
    (tmp_path / "flows.yaml").write_text("stray")
    monkeypatch.setattr(dp, "files", lambda name: package)
    monkeypatch.setattr(dp, "__file__", str(package / "__init__.py"))
    assert dp.data("flows.yaml") == package / "data" / "flows.yaml"
