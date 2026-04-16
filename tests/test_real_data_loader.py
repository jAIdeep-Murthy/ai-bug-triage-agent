from __future__ import annotations

from scripts.load_real_data import derive_owner_team, map_severity


def test_severity_mapping_critical() -> None:
    assert map_severity("blocker") == "critical"
    assert map_severity("critical") == "critical"


def test_severity_mapping_high() -> None:
    assert map_severity("major") == "high"


def test_severity_mapping_medium() -> None:
    assert map_severity("normal") == "medium"
    assert map_severity("") == "medium"


def test_severity_mapping_low() -> None:
    assert map_severity("trivial") == "low"
    assert map_severity("enhancement") == "low"


def test_owner_team_derivation() -> None:
    assert derive_owner_team("JDT/UI") == "ui-team"
    assert derive_owner_team("Compiler") == "compiler-team"
    assert derive_owner_team("Unknown") == "jdt-team"

