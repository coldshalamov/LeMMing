from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from .agents import discover_agents, load_agent
from .engine import load_tick
from .messages import OutboxEntry, count_outbox_entries, read_outbox_entries
from .org import compute_virtual_inbox_sources, get_agent_credits, get_credits, get_org_config
from .paths import get_logs_dir, validate_agent_name

BASE_PATH = Path(os.environ.get("LEMMING_BASE_PATH", Path(__file__).resolve().parent.parent))
MAX_LIMIT = 1000

app = FastAPI(title="LeMMing API", description="API for LeMMing multi-agent system", version="0.4.0")

# Configure CORS
# Default to localhost:3000 for local development
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScheduleInfo(BaseModel):
    run_every_n_ticks: int
    phase_offset: int


class CreditsInfo(BaseModel):
    model: str | None = None
    credits_left: float | None = None
    max_credits: float | None = None
    soft_cap: float | None = None
    cost_per_action: float | None = None


class AgentInfo(BaseModel):
    name: str
    title: str
    description: str
    model: str
    schedule: ScheduleInfo
    read_outboxes: list[str]
    tools: list[str]
    credits: CreditsInfo | None = None


class OutboxEntryModel(BaseModel):
    id: str
    created_at: str
    tick: int
    agent: str
    kind: str
    payload: dict[str, Any]
    tags: list[str] | None = None
    meta: dict[str, Any] | None = None


class LogEntry(BaseModel):
    model_config = ConfigDict(extra="allow")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "LeMMing API", "version": "0.4.0"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _serialize_entry(entry: OutboxEntry) -> dict[str, Any]:
    data = entry.to_dict()
    data.setdefault("tags", [])
    return data


def _load_agents_with_credits(base_path: Path) -> tuple[list[Any], dict[str, Any]]:
    agents = discover_agents(base_path)
    credits = get_credits(base_path, agents)
    return agents, credits


def _build_agent_info(agent: Any, credits: dict[str, Any]) -> AgentInfo:
    agent_credits = credits.get(agent.name)
    return AgentInfo(
        name=agent.name,
        title=agent.title,
        description=agent.short_description,
        model=agent.model.key,
        schedule=ScheduleInfo(
            run_every_n_ticks=agent.schedule.run_every_n_ticks,
            phase_offset=agent.schedule.phase_offset,
        ),
        read_outboxes=agent.permissions.read_outboxes,
        tools=agent.permissions.tools,
        credits=CreditsInfo(**agent_credits) if agent_credits else None,
    )


def _read_agent_logs(base_path: Path, agent_name: str, limit: int = 100) -> list[dict[str, Any]]:
    try:
        validate_agent_name(agent_name)
    except ValueError:
        return []

    log_path = get_logs_dir(base_path, agent_name) / "structured.jsonl"
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except OSError:
        return []

    entries: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
    return entries


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    agents, credits = _load_agents_with_credits(BASE_PATH)
    return [_build_agent_info(agent, credits) for agent in agents]


@app.get("/api/agents/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str) -> AgentInfo:
    try:
        agent = load_agent(BASE_PATH, agent_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    _, credits = _load_agents_with_credits(BASE_PATH)
    return _build_agent_info(agent, credits)


@app.get("/api/agents/{agent_name}/outbox", response_model=list[OutboxEntryModel])
async def get_agent_outbox(agent_name: str, limit: int = 20, since_tick: int | None = None) -> list[OutboxEntryModel]:
    if limit > MAX_LIMIT:
        raise HTTPException(status_code=400, detail=f"Limit cannot exceed {MAX_LIMIT}")
    entries = read_outbox_entries(BASE_PATH, agent_name, limit=limit, since_tick=since_tick)
    return [OutboxEntryModel(**_serialize_entry(entry)) for entry in entries]


@app.get("/api/agents/{agent_name}/logs", response_model=list[LogEntry])
async def get_agent_logs(agent_name: str, limit: int = 100) -> list[dict[str, Any]]:
    if limit > MAX_LIMIT:
        raise HTTPException(status_code=400, detail=f"Limit cannot exceed {MAX_LIMIT}")
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit must be positive")
    return _read_agent_logs(BASE_PATH, agent_name, limit=limit)


@app.get("/api/org-graph")
async def get_org_graph() -> dict[str, Any]:
    # Avoid mutating credits on read-only operations.
    agents = discover_agents(BASE_PATH)
    agent_names = {agent.name for agent in agents}
    return {
        agent.name: {
            "can_read": compute_virtual_inbox_sources(agent, agent_names),
            "tools": agent.permissions.tools,
        }
        for agent in agents
    }


@app.get("/api/credits")
async def get_credits_endpoint() -> dict[str, Any]:
    return get_credits(BASE_PATH)


@app.get("/api/agents/{agent_name}/credits")
async def get_agent_credit(agent_name: str) -> dict[str, Any]:
    return get_agent_credits(agent_name, BASE_PATH)


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    return get_org_config(BASE_PATH)


@app.get("/api/status")
async def status() -> dict[str, Any]:
    agents, credits = _load_agents_with_credits(BASE_PATH)
    tick = load_tick(BASE_PATH)
    total_messages = sum(count_outbox_entries(BASE_PATH, agent.name) for agent in agents)
    total_credits = sum(entry.get("credits_left", 0.0) for entry in credits.values())
    return {
        "tick": tick,
        "total_agents": len(agents),
        "total_messages": total_messages,
        "total_credits": total_credits,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/messages", response_model=list[OutboxEntryModel])
async def list_messages(
    agent: str | None = None, limit: int = 50, since_tick: int | None = None
) -> list[OutboxEntryModel]:
    if limit > MAX_LIMIT:
        raise HTTPException(status_code=400, detail=f"Limit cannot exceed {MAX_LIMIT}")
    agent_names: list[str]
    if agent:
        try:
            load_agent(BASE_PATH, agent)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Agent '{agent}' not found")
        agent_names = [agent]
    else:
        agent_names = [a.name for a in discover_agents(BASE_PATH)]

    entries: list[OutboxEntry] = []
    for agent_name in agent_names:
        entries.extend(read_outbox_entries(BASE_PATH, agent_name, limit=limit, since_tick=since_tick))

    entries.sort(key=lambda e: (e.tick, e.created_at), reverse=True)
    return [OutboxEntryModel(**_serialize_entry(entry)) for entry in entries[:limit]]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            status_payload = await status()
            messages = await list_messages(limit=20)
            await websocket.send_json(
                {"status": status_payload, "messages": [m.model_dump() for m in messages]}
            )
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        return
