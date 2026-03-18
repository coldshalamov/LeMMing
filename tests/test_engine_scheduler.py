from pathlib import Path

from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule
from lemming.engine import should_run


def _dummy_agent(tmp_path: Path, run_every: int, offset: int) -> Agent:
    schedule = AgentSchedule(run_every_n_ticks=run_every, phase_offset=offset)
    return Agent(
        name="tester",
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


def test_should_run_matches_phase(tmp_path: Path) -> None:
    agent = _dummy_agent(tmp_path, run_every=3, offset=1)
    # Spec: should_run = (tick % N) == (offset % N)
    # With N=3, offset=1: should_run when (tick % 3) == 1
    assert should_run(agent, 1)   # 1 % 3 == 1
    assert not should_run(agent, 2)  # 2 % 3 == 2 != 1
    assert should_run(agent, 4)   # 4 % 3 == 1
    assert not should_run(agent, 5)  # 5 % 3 == 2 != 1


def test_should_run_handles_zero_offset(tmp_path: Path) -> None:
    agent = _dummy_agent(tmp_path, run_every=2, offset=0)
    assert should_run(agent, 2)
    assert not should_run(agent, 3)
