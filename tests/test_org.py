"""Tests for org module."""

from __future__ import annotations

from pathlib import Path

import pytest

from lemming import org


def test_get_org_chart(temp_base_path: Path, setup_config_files, mock_org_chart):
    """Test loading org chart."""
    chart = org.get_org_chart(temp_base_path)
    assert chart == mock_org_chart
    assert "manager" in chart
    assert "planner" in chart


def test_get_org_config(temp_base_path: Path, setup_config_files, mock_org_config):
    """Test loading org config."""
    config = org.get_org_config(temp_base_path)
    assert config == mock_org_config
    assert config["base_turn_seconds"] == 10


def test_get_credits(temp_base_path: Path, setup_config_files, mock_credits):
    """Test loading credits."""
    credits = org.get_credits(temp_base_path)
    assert credits == mock_credits
    assert credits["manager"]["credits_left"] == 100.0


def test_can_send_allowed(temp_base_path: Path, setup_config_files):
    """Test permission check for allowed send."""
    assert org.can_send("manager", "planner", temp_base_path) is True
    assert org.can_send("manager", "hr", temp_base_path) is True


def test_can_send_denied(temp_base_path: Path, setup_config_files):
    """Test permission check for denied send."""
    assert org.can_send("planner", "hr", temp_base_path) is False
    assert org.can_send("hr", "planner", temp_base_path) is False


def test_get_read_from(temp_base_path: Path, setup_config_files):
    """Test getting read_from list."""
    read_from = org.get_read_from("manager", temp_base_path)
    assert "planner" in read_from
    assert "hr" in read_from
    assert len(read_from) == 2


def test_get_send_to(temp_base_path: Path, setup_config_files):
    """Test getting send_to list."""
    send_to = org.get_send_to("manager", temp_base_path)
    assert "planner" in send_to
    assert "hr" in send_to
    assert len(send_to) == 2


def test_get_agent_credits(temp_base_path: Path, setup_config_files):
    """Test getting agent credits."""
    credits = org.get_agent_credits("manager", temp_base_path)
    assert credits["model"] == "gpt-4.1-mini"
    assert credits["cost_per_action"] == 0.01
    assert credits["credits_left"] == 100.0


def test_get_agent_credits_nonexistent(temp_base_path: Path, setup_config_files):
    """Test getting credits for nonexistent agent."""
    credits = org.get_agent_credits("nonexistent", temp_base_path)
    assert credits == {}


def test_deduct_credits(temp_base_path: Path, setup_config_files):
    """Test deducting credits."""
    org.deduct_credits("manager", 10.0, temp_base_path)
    credits = org.get_agent_credits("manager", temp_base_path)
    assert credits["credits_left"] == 90.0


def test_deduct_credits_multiple(temp_base_path: Path, setup_config_files):
    """Test deducting credits multiple times."""
    org.deduct_credits("manager", 10.0, temp_base_path)
    org.deduct_credits("manager", 5.5, temp_base_path)
    credits = org.get_agent_credits("manager", temp_base_path)
    assert credits["credits_left"] == 84.5


def test_deduct_credits_new_agent(temp_base_path: Path, setup_config_files):
    """Test deducting credits for new agent (auto-initialize)."""
    org.deduct_credits("new_agent", 5.0, temp_base_path)
    credits = org.get_agent_credits("new_agent", temp_base_path)
    assert credits["credits_left"] == -5.0  # Started at 0, deducted 5


def test_save_credits(temp_base_path: Path, setup_config_files):
    """Test saving credits."""
    org.deduct_credits("manager", 10.0, temp_base_path)
    org.save_credits(temp_base_path)

    # Reload to verify persistence
    org.reset_caches()
    credits = org.get_agent_credits("manager", temp_base_path)
    assert credits["credits_left"] == 90.0


def test_reset_caches():
    """Test cache reset."""
    org._org_chart_cache = {"test": "data"}
    org._org_config_cache = {"test": "data"}
    org._credits_cache = {"test": "data"}

    org.reset_caches()

    assert org._org_chart_cache is None
    assert org._org_config_cache is None
    assert org._credits_cache is None


def test_org_chart_caching(temp_base_path: Path, setup_config_files):
    """Test that org chart is cached."""
    chart1 = org.get_org_chart(temp_base_path)
    chart2 = org.get_org_chart(temp_base_path)
    assert chart1 is chart2  # Same object reference


def test_missing_config_file(temp_base_path: Path):
    """Test error when config file is missing."""
    with pytest.raises(FileNotFoundError, match="Missing configuration file"):
        org.get_org_chart(temp_base_path)


def test_set_config_dir(temp_base_path: Path):
    """Test setting config directory."""
    org.set_config_dir(temp_base_path)
    assert org._config_dir == temp_base_path / "lemming" / "config"


def test_set_config_dir_none():
    """Test resetting config directory to default."""
    org.set_config_dir(None)
    assert org._config_dir == org.DEFAULT_CONFIG_DIR
