from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents import discover_agents, load_agent
from .messages import read_outbox_entries
from .org import derive_org_graph, get_agent_credits, get_credits, get_org_config

BASE_PATH = Path(__file__).resolve().parent.parent
app = FastAPI(title="LeMMing API", description="API for LeMMing multi-agent system", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentInfo(BaseModel):
    name: str
    title: str
    description: str
    model: str
    schedule: str
    read_outboxes: list[str]
    tools: list[str]


class OutboxEntryModel(BaseModel):
    id: str
    timestamp: str
    tick: int
    agent: str
    kind: str
    payload: dict[str, Any]
    tags: list[str] | None = None
    meta: dict[str, Any] | None = None


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "LeMMing API", "version": "0.4.0"}


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    agents = discover_agents(BASE_PATH)
    results: list[AgentInfo] = []
    for agent in agents:
        results.append(
            AgentInfo(
                name=agent.name,
                title=agent.title,
                description=agent.short_description,
                model=agent.model.key,
                schedule=f"every {agent.schedule.run_every_n_ticks} ticks (offset {agent.schedule.phase_offset})",
                read_outboxes=agent.permissions.read_outboxes,
                tools=agent.permissions.tools,
            )
        )
    return results


@app.get("/api/agents/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str) -> AgentInfo:
    try:
        agent = load_agent(BASE_PATH, agent_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return AgentInfo(
        name=agent.name,
        title=agent.title,
        description=agent.short_description,
        model=agent.model.key,
        schedule=f"every {agent.schedule.run_every_n_ticks} ticks (offset {agent.schedule.phase_offset})",
        read_outboxes=agent.permissions.read_outboxes,
        tools=agent.permissions.tools,
    )


@app.get("/api/agents/{agent_name}/outbox", response_model=list[OutboxEntryModel])
async def get_agent_outbox(agent_name: str, limit: int = 20) -> list[OutboxEntryModel]:
    entries = read_outbox_entries(BASE_PATH, agent_name, limit=limit)
    return [OutboxEntryModel(**entry.to_dict()) for entry in entries]


@app.get("/api/org-graph")
async def get_org_graph() -> dict[str, Any]:
    return derive_org_graph(BASE_PATH)


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
    agents = discover_agents(BASE_PATH)
    credits = get_credits(BASE_PATH)
    total_credits = sum(entry.get("credits_left", 0.0) for entry in credits.values())
    return {
        "total_agents": len(agents),
        "total_credits": total_credits,
        "timestamp": datetime.utcnow().isoformat(),
    }
