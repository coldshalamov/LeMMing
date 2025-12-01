"""FastAPI backend for LeMMing dashboard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .agents import discover_agents, load_agent
from .memory import get_memory_summary
from .messaging import collect_incoming_messages
from .org import get_agent_credits, get_credits, get_org_chart, get_org_config

# Base path for the LeMMing installation
BASE_PATH = Path(__file__).resolve().parent.parent

# FastAPI app
app = FastAPI(title="LeMMing API", description="API for LeMMing multi-agent system", version="0.3.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class AgentInfo(BaseModel):
    """Agent information model."""

    name: str
    role: str
    description: str
    model: str
    speed_multiplier: int
    credits_left: float
    max_credits: float
    cost_per_action: float
    send_to: list[str]
    read_from: list[str]


class MessageInfo(BaseModel):
    """Message information model."""

    id: str
    sender: str
    receiver: str
    content: str
    importance: str
    timestamp: str
    turn_created: int
    ttl_turns: int | None


class SystemStatus(BaseModel):
    """System status model."""

    total_agents: int
    total_credits: float
    timestamp: str


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass


manager = ConnectionManager()


# REST Endpoints


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LeMMing API", "version": "0.3.0"}


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents():
    """List all agents."""
    agents = discover_agents(BASE_PATH)
    credits = get_credits(BASE_PATH)

    result = []
    for agent in agents:
        credit_info = credits.get(agent.name, {})
        result.append(
            AgentInfo(
                name=agent.name,
                role=agent.role,
                description=agent.description,
                model=agent.model_key,
                speed_multiplier=agent.org_speed_multiplier,
                credits_left=credit_info.get("credits_left", 0.0),
                max_credits=agent.max_credits,
                cost_per_action=credit_info.get("cost_per_action", 0.0),
                send_to=agent.send_to,
                read_from=agent.read_from,
            )
        )

    return result


@app.get("/api/agents/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str):
    """Get detailed information about a specific agent."""
    try:
        agent = load_agent(BASE_PATH, agent_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    credit_info = get_agent_credits(agent_name, BASE_PATH)

    return AgentInfo(
        name=agent.name,
        role=agent.role,
        description=agent.description,
        model=agent.model_key,
        speed_multiplier=agent.org_speed_multiplier,
        credits_left=credit_info.get("credits_left", 0.0),
        max_credits=agent.max_credits,
        cost_per_action=credit_info.get("cost_per_action", 0.0),
        send_to=agent.send_to,
        read_from=agent.read_from,
    )


@app.get("/api/messages")
async def list_messages(agent: str | None = None, limit: int = 50):
    """
    List messages.

    Args:
        agent: Filter by agent name (messages to this agent)
        limit: Maximum number of messages to return
    """
    messages = []

    if agent:
        # Get messages for specific agent
        incoming = collect_incoming_messages(BASE_PATH, agent, current_turn=999999)
        for msg in incoming[:limit]:
            messages.append(
                {
                    "id": msg.id,
                    "sender": msg.sender,
                    "receiver": msg.receiver,
                    "content": msg.content,
                    "importance": msg.importance,
                    "timestamp": msg.timestamp,
                    "turn_created": msg.turn_created,
                    "ttl_turns": msg.ttl_turns,
                }
            )
    else:
        # Get all messages across all agents
        agents = discover_agents(BASE_PATH)
        for ag in agents:
            incoming = collect_incoming_messages(BASE_PATH, ag.name, current_turn=999999)
            for msg in incoming:
                messages.append(
                    {
                        "id": msg.id,
                        "sender": msg.sender,
                        "receiver": msg.receiver,
                        "content": msg.content,
                        "importance": msg.importance,
                        "timestamp": msg.timestamp,
                        "turn_created": msg.turn_created,
                        "ttl_turns": msg.ttl_turns,
                    }
                )

    # Sort by timestamp and limit
    messages.sort(key=lambda x: x["timestamp"], reverse=True)
    return messages[:limit]


@app.get("/api/org-chart")
async def get_org_chart_endpoint():
    """Get the organization chart."""
    return get_org_chart(BASE_PATH)


@app.get("/api/credits")
async def get_credits_endpoint():
    """Get credits for all agents."""
    return get_credits(BASE_PATH)


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    agents = discover_agents(BASE_PATH)
    credits = get_credits(BASE_PATH)

    total_credits = sum(c.get("credits_left", 0.0) for c in credits.values())

    return SystemStatus(total_agents=len(agents), total_credits=total_credits, timestamp=datetime.utcnow().isoformat())


@app.get("/api/agents/{agent_name}/logs")
async def get_agent_logs(agent_name: str, lines: int = 20):
    """Get agent activity logs."""
    log_file = BASE_PATH / "agents" / agent_name / "logs" / "activity.log"

    if not log_file.exists():
        return {"logs": [], "agent": agent_name}

    with log_file.open("r") as f:
        all_lines = f.readlines()

    recent = all_lines[-lines:]

    return {"logs": [line.rstrip() for line in recent], "agent": agent_name}


@app.get("/api/agents/{agent_name}/memory")
async def get_agent_memory(agent_name: str):
    """Get agent memory."""
    memories = get_memory_summary(BASE_PATH, agent_name)
    return {"agent": agent_name, "memories": memories}


@app.get("/api/config")
async def get_config():
    """Get organization configuration."""
    return get_org_config(BASE_PATH)


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            # Echo back or process
            await websocket.send_text(f"Received: {data}")

            # Broadcast status updates periodically
            agents = discover_agents(BASE_PATH)
            credits = get_credits(BASE_PATH)

            status = {
                "type": "status_update",
                "data": {
                    "total_agents": len(agents),
                    "total_credits": sum(c.get("credits_left", 0.0) for c in credits.values()),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            await manager.broadcast(status)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Serve the dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard HTML."""
    dashboard_path = BASE_PATH / "ui" / "lemming_dashboard.html"

    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")

    with dashboard_path.open("r") as f:
        content = f.read()

    return HTMLResponse(content=content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
