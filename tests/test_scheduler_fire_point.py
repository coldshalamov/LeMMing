"""Tests for fire_point calculation and intra-tick ordering."""

from pathlib import Path

from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule
from lemming.engine import compute_fire_point, get_firing_agents


def _dummy_agent(name: str, tmp_path: Path, run_every: int, offset: int) -> Agent:
    """Create a dummy agent for testing."""
    schedule = AgentSchedule(run_every_n_ticks=run_every, phase_offset=offset)
    return Agent(
        name=name,
        path=tmp_path,
        title="Test",
        short_description="",
        workflow_description="",
        model=AgentModel(),
        permissions=AgentPermissions(),
        schedule=schedule,
        instructions="",
        credits=AgentCredits(),
        resume_path=tmp_path / "resume.json",
    )


def test_compute_fire_point_formula(tmp_path: Path) -> None:
    """Test fire_point calculation: (-offset mod N) / N"""
    # N=4, offset=0 → fire_point = 0.0
    agent = _dummy_agent("a", tmp_path, run_every=4, offset=0)
    assert compute_fire_point(agent) == 0.0

    # N=4, offset=1 → fire_point = (-1 mod 4) / 4 = 3/4 = 0.75
    agent = _dummy_agent("b", tmp_path, run_every=4, offset=1)
    assert compute_fire_point(agent) == 0.75

    # N=4, offset=2 → fire_point = (-2 mod 4) / 4 = 2/4 = 0.5
    agent = _dummy_agent("c", tmp_path, run_every=4, offset=2)
    assert compute_fire_point(agent) == 0.5

    # N=4, offset=3 → fire_point = (-3 mod 4) / 4 = 1/4 = 0.25
    agent = _dummy_agent("d", tmp_path, run_every=4, offset=3)
    assert compute_fire_point(agent) == 0.25


def test_every_tick_agent_fire_point(tmp_path: Path) -> None:
    """Agents that run every tick (N=1) have fire_point=0."""
    agent = _dummy_agent("always", tmp_path, run_every=1, offset=0)
    assert compute_fire_point(agent) == 0.0


def test_intra_tick_ordering_by_fire_point(tmp_path: Path) -> None:
    """Agents are ordered by fire_point (ascending), then by name."""
    # Create agents that all fire at tick 0 with different offsets
    # should_run: (tick % N) == (offset % N)
    # All have offset=0, so all fire at tick 0, 4, 8, etc.
    agents = [
        _dummy_agent("alice", tmp_path, run_every=4, offset=0),   # fp=0.0
        _dummy_agent("bob", tmp_path, run_every=4, offset=0),     # fp=0.0
        _dummy_agent("charlie", tmp_path, run_every=2, offset=0), # fp=0.0
        _dummy_agent("diana", tmp_path, run_every=1, offset=0),   # fp=0.0
    ]

    # All should fire at tick 4 (since 4 % N == 0 % N for N=1,2,4)
    firing = get_firing_agents(agents, tick=4)

    # All have fp=0.0, so ordered alphabetically
    assert [a.name for a in firing] == ["alice", "bob", "charlie", "diana"]


def test_intra_tick_ordering_tiebreaker(tmp_path: Path) -> None:
    """When fire_point is the same, agents are ordered alphabetically by name."""
    # All run every tick, so fire_point=0 for all
    agents = [
        _dummy_agent("zulu", tmp_path, run_every=1, offset=0),
        _dummy_agent("alpha", tmp_path, run_every=1, offset=0),
        _dummy_agent("bravo", tmp_path, run_every=1, offset=0),
    ]

    firing = get_firing_agents(agents, tick=1)

    # Should be alphabetically ordered
    assert [a.name for a in firing] == ["alpha", "bravo", "zulu"]


def test_mixed_schedules_ordering(tmp_path: Path) -> None:
    """Test ordering with agents having different run_every_n_ticks values."""
    agents = [
        _dummy_agent("fast", tmp_path, run_every=1, offset=0),    # fp=0.0, fires every tick
        _dummy_agent("medium", tmp_path, run_every=2, offset=0),  # fp=0.0, fires every 2 ticks
        _dummy_agent("slow", tmp_path, run_every=4, offset=0),    # fp=0.0, fires every 4 ticks
    ]

    # At tick 4, all should fire (4 % N == 0 % N for all)
    firing = get_firing_agents(agents, tick=4)

    # All have fp=0.0, so alphabetically ordered
    assert [a.name for a in firing] == ["fast", "medium", "slow"]


def test_deterministic_ordering_across_ticks(tmp_path: Path) -> None:
    """Ordering should be deterministic and consistent across ticks."""
    agents = [
        _dummy_agent("agent_c", tmp_path, run_every=2, offset=0),
        _dummy_agent("agent_a", tmp_path, run_every=2, offset=0),
        _dummy_agent("agent_b", tmp_path, run_every=2, offset=0),
    ]

    # Check ordering is the same across multiple ticks
    firing_tick2 = get_firing_agents(agents, tick=2)
    firing_tick4 = get_firing_agents(agents, tick=4)
    firing_tick6 = get_firing_agents(agents, tick=6)

    expected_order = ["agent_a", "agent_b", "agent_c"]
    assert [a.name for a in firing_tick2] == expected_order
    assert [a.name for a in firing_tick4] == expected_order
    assert [a.name for a in firing_tick6] == expected_order
