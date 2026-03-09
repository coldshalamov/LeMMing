from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status as http_status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .agents import discover_agents, load_agent, validate_resume_data
from .engine import load_tick, run_once
from .messages import (
    OutboxEntry,
    count_outbox_entries,
    read_multi_agent_outbox_entries,
    read_outbox_entries,
    write_outbox_entry,
)
from .models import ModelRegistry
from .org import compute_virtual_inbox_sources, get_agent_credits, get_credits, get_org_config
from .paths import (
    get_agents_dir,
    get_config_dir,
    get_logs_dir,
    validate_agent_name,
    validate_path_prefix,
)
from .tools import ToolRegistry

# Load secrets from local file if they exist
SECRETS_PATH = Path(os.environ.get("LEMMING_BASE_PATH", Path(__file__).resolve().parent.parent)) / "secrets.json"
if SECRETS_PATH.exists():
    try:
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
            for k, v in secrets.items():
                if v and not os.environ.get(k):
                    os.environ[k] = v
    except Exception:
        pass

BASE_PATH = Path(os.environ.get("LEMMING_BASE_PATH", Path(__file__).resolve().parent.parent))
MAX_LIMIT = 1000

logger = logging.getLogger("lemming.api")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LeMMing API", description="API for LeMMing multi-agent system", version="0.4.1")

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


# Simple in-memory rate limiter
# Map: client_ip -> list of timestamps
_request_timestamps: dict[str, list[float]] = {}
MAX_RATE_LIMIT_CLIENTS = 10000


async def verify_admin_access(request: Request):
    """Verify admin access if configured."""
    admin_key = os.environ.get("LEMMING_ADMIN_KEY")
    # If no key is configured, allow access (default local dev mode)
    if not admin_key:
        return

    # If key is configured, enforce it
    request_key = request.headers.get("X-Admin-Key")
    # Use constant-time comparison to prevent timing attacks
    if not request_key or not secrets.compare_digest(request_key, admin_key):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )


def rate_limiter(limit: int = 10, window: int = 60, scope: str = "global"):
    async def dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{scope}"
        now = time.time()

        # Initialize
        if key not in _request_timestamps:
            # Memory leak protection: prevent unbounded growth
            if len(_request_timestamps) >= MAX_RATE_LIMIT_CLIENTS:
                # Evict the oldest inserted client (FIFO) to maintain size limit
                # This is O(1) and prevents CPU exhaustion from scanning
                try:
                    del _request_timestamps[next(iter(_request_timestamps))]
                except StopIteration:
                    pass
            _request_timestamps[key] = []

        # Filter old timestamps
        _request_timestamps[key] = [t for t in _request_timestamps[key] if now - t < window]

        if len(_request_timestamps[key]) >= limit:
            logger.warning(f"Rate limit exceeded for {key}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        _request_timestamps[key].append(now)

    return dependency


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Content Security Policy:
    # - default-src 'self': Only allow resources from the same origin
    # - img-src 'self' data: https: Allow images from self, data URIs (e.g. base64), and https
    # - script-src 'self' 'unsafe-inline' https: Allow scripts from self, inline (needed for Swagger UI), and https
    # - style-src 'self' 'unsafe-inline' https: Allow styles from self, inline (needed for Swagger UI), and https
    # - object-src 'none': Disable plugins like Flash
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "object-src 'none'"
    )
    return response


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


class CreateAgentRequest(BaseModel):
    name: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")  # The slug/folder name
    resume: dict[str, Any]  # The full resume JSON content
    path_prefix: str | None = Field(
        None, max_length=100, pattern=r"^[a-zA-Z0-9/_-]+$"
    )  # Optional subfolder (e.g. "engineering/backend")

    @field_validator("resume")
    @classmethod
    def check_resume_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Limit the complexity of the resume JSON."""
        # Simple check: serialize and check string length
        try:
            content = json.dumps(v)
            if len(content) > 50_000:  # 50KB limit
                raise ValueError("Resume JSON is too large (max 50KB)")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid resume JSON: {e}")
        return v


class CloneAgentRequest(BaseModel):
    source_agent: str
    target_name: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    target_path_prefix: str | None = Field(None, max_length=100, pattern=r"^[a-zA-Z0-9/_-]+$")


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


class SendMessageRequest(BaseModel):
    target: str = Field(..., max_length=50)
    text: str = Field(..., max_length=20000)  # ~20KB limit for messages
    importance: str = Field("normal", pattern="^(normal|high|critical)$")


class ToolInfo(BaseModel):
    id: str
    description: str


@app.post("/api/messages", dependencies=[Depends(rate_limiter(limit=10, window=60, scope="messages"))])
async def send_message(request: SendMessageRequest) -> dict[str, str]:
    """Send a message from 'human' to a target agent."""
    tick = load_tick(BASE_PATH)

    # Ensure human agent dir exists
    human_dir = get_agents_dir(BASE_PATH) / "human"
    if not human_dir.exists():
        # Create it if missing (bootstrap usually does this)
        human_dir.mkdir(parents=True, exist_ok=True)
        (human_dir / "outbox").mkdir(exist_ok=True)

    entry = OutboxEntry.create(
        agent="human",
        tick=tick,
        kind="message",
        payload={
            "text": request.text,
            "importance": request.importance,
            "target": request.target,
        },
        tags=["human-originated"],
    )
    # The 'target' logic in engine relies on the message content or routing.
    # But usually explicit visual routing requires 'recipient' metadata if we want strict routing.
    # For now, we follow the cli.py 'send_cmd' pattern.

    write_outbox_entry(BASE_PATH, "human", entry)
    return {"status": "sent", "id": entry.id}


class EngineConfig(BaseModel):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


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


def _read_last_lines(file_path: Path, limit: int) -> list[str]:
    """Efficiently read the last N lines from a file."""
    if limit <= 0:
        return []

    chunk_size = 8192
    try:
        with file_path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            end_pos = f.tell()
            if end_pos == 0:
                return []

            pos = end_pos
            lines_found = 0

            while pos > 0 and lines_found < limit:
                read_len = min(chunk_size, pos)
                pos -= read_len
                f.seek(pos)
                chunk = f.read(read_len)
                lines_found += chunk.count(b"\n")

            f.seek(pos)
            data = f.read(end_pos - pos)
            text = data.decode("utf-8", errors="ignore")
            lines = text.splitlines()

            return lines[-limit:]
    except OSError:
        return []


def _read_agent_logs(base_path: Path, agent_name: str, limit: int = 100) -> list[dict[str, Any]]:
    try:
        validate_agent_name(agent_name)
    except ValueError:
        return []

    log_path = get_logs_dir(base_path, agent_name) / "structured.jsonl"
    if not log_path.exists():
        return []

    # Safe log reading with DoS protection
    # Read only the last 1MB of logs if the file is large
    max_log_read_size = 1 * 1024 * 1024  # 1MB

    try:
        size = log_path.stat().st_size
        if size == 0:
            return []

        with log_path.open("rb") as f:
            if size > max_log_read_size:
                f.seek(size - max_log_read_size)
                content_bytes = f.read()
                # We might have cut a multibyte char or be in middle of line.
                # Skip to next newline to ensure clean start.
                first_newline = content_bytes.find(b"\n")
                if first_newline != -1:
                    content_bytes = content_bytes[first_newline + 1 :]
                else:
                    # No newline found in the last 1MB? That's a huge line.
                    # Just decode what we can, ignoring errors at the start/end
                    pass
            else:
                content_bytes = f.read()

        # Decode using replace to handle any remaining partial bytes gracefully
        content = content_bytes.decode("utf-8", errors="replace")
        lines = content.splitlines()

    except OSError:
        return []

    entries: list[dict[str, Any]] = []
    # If we still have too many lines, take only the last 'limit'
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


@app.post(
    "/api/agents",
    status_code=201,
    dependencies=[Depends(rate_limiter(limit=5, window=60, scope="agents_create")), Depends(verify_admin_access)],
)
async def create_agent(request: CreateAgentRequest) -> dict[str, str]:
    try:
        validate_agent_name(request.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Determine target directory
    agents_dir = get_agents_dir(BASE_PATH)
    if request.path_prefix:
        try:
            validate_path_prefix(request.path_prefix)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        target_dir = agents_dir / request.path_prefix / request.name
    else:
        target_dir = agents_dir / request.name

    if target_dir.exists():
        raise HTTPException(status_code=409, detail=f"Agent directory '{request.name}' already exists")

    # Create directory structure
    try:
        target_dir.mkdir(parents=True, exist_ok=False)
        (target_dir / "outbox").mkdir()
        (target_dir / "memory").mkdir()
        (target_dir / "logs").mkdir()
        (target_dir / "workspace").mkdir()
    except OSError as e:
        logger.error(f"Failed to create directories for agent '{request.name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create agent directories")

    # Construct resume.json
    final_resume = request.resume.copy()
    final_resume["name"] = request.name  # Ensure name matches folder

    resume_path = target_dir / "resume.json"
    errors = validate_resume_data(final_resume, resume_path=resume_path)
    if errors:
        import shutil

        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail={"errors": errors})
    try:
        with open(resume_path, "w", encoding="utf-8") as f:
            json.dump(final_resume, f, indent=2)
    except OSError as e:
        # Cleanup on failure
        import shutil

        shutil.rmtree(target_dir, ignore_errors=True)
        logger.error(f"Failed to write resume.json for agent '{request.name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to write resume.json")

    return {"status": "created", "path": str(target_dir.relative_to(BASE_PATH))}


@app.post(
    "/api/agents/clone",
    status_code=201,
    dependencies=[Depends(rate_limiter(limit=5, window=60, scope="agents_clone")), Depends(verify_admin_access)],
)
async def clone_agent(request: CloneAgentRequest) -> dict[str, str]:
    try:
        validate_agent_name(request.target_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Find source agent
    try:
        source_agent = load_agent(BASE_PATH, request.source_agent)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Source agent not found")

    agents_dir = get_agents_dir(BASE_PATH)
    if request.target_path_prefix:
        try:
            validate_path_prefix(request.target_path_prefix)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        target_dir = agents_dir / request.target_path_prefix / request.target_name
    else:
        target_dir = agents_dir / request.target_name

    if target_dir.exists():
        raise HTTPException(status_code=409, detail=f"Target directory '{request.target_name}' already exists")

    # Copy logic
    import shutil

    try:
        # We only copy the directory structure and resume.json, NOT memory/logs/outbox
        target_dir.mkdir(parents=True)
        (target_dir / "outbox").mkdir()
        (target_dir / "memory").mkdir()
        (target_dir / "logs").mkdir()
        (target_dir / "workspace").mkdir()

        # Read source resume, update name, write to target
        with open(source_agent.resume_path, encoding="utf_8") as f:
            source_data = json.load(f)

        source_data["name"] = request.target_name

        with open(target_dir / "resume.json", "w", encoding="utf-8") as f:
            json.dump(source_data, f, indent=2)

    except OSError as e:
        # Cleanup
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        logger.error(f"Failed to clone agent '{request.target_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clone agent")

    return {"status": "cloned", "path": str(target_dir.relative_to(BASE_PATH))}


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


@app.get("/api/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    return [ToolInfo(**item) for item in ToolRegistry.list_tool_info()]


@app.get("/api/models", response_model=list[str])
async def list_models() -> list[str]:
    registry = ModelRegistry(config_dir=get_config_dir(BASE_PATH))
    return registry.list_keys()


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
        # Get all discovered agents
        agent_names = [a.name for a in discover_agents(BASE_PATH)]
        # explicitly add human if not present (since human might not have a resume.json)
        if "human" not in agent_names and (get_agents_dir(BASE_PATH) / "human").exists():
            agent_names.append("human")

    entries = read_multi_agent_outbox_entries(BASE_PATH, agent_names, limit=limit, since_tick=since_tick)
    return [OutboxEntryModel(**_serialize_entry(entry)) for entry in entries]


@app.post(
    "/api/engine/tick",
    dependencies=[Depends(rate_limiter(limit=10, window=60, scope="engine_tick")), Depends(verify_admin_access)],
)
async def trigger_tick() -> dict[str, Any]:
    """Manually trigger one engine tick."""
    try:
        # run_once(BASE_PATH) will:
        # 1. Load current tick
        # 2. run_tick for that tick
        # 3. increment and persist_tick
        results = run_once(BASE_PATH)

        # After run_once, load_tick gives us the NEXT tick.
        # So the tick we just ran is next_tick_in_file - 1.
        current_tick = load_tick(BASE_PATH)

        return {"status": "success", "tick": current_tick - 1, "agents_run": len(results)}
    except Exception as e:
        import traceback

        logger.error(f"Tick failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Engine tick failed")


@app.get("/api/engine/config", response_model=EngineConfig)
async def get_engine_config() -> dict[str, Any]:
    """Get non-sensitive portion of config (masked)."""
    return {
        "openai_api_key": "***" if os.environ.get("OPENAI_API_KEY") else None,
        "anthropic_api_key": "***" if os.environ.get("ANTHROPIC_API_KEY") else None,
    }


@app.post(
    "/api/engine/config",
    dependencies=[Depends(rate_limiter(limit=5, window=60, scope="engine_config")), Depends(verify_admin_access)],
)
async def update_engine_config(config: EngineConfig) -> dict[str, str]:
    """Update engine secrets and persist to secrets.json."""
    current_secrets = {}
    if SECRETS_PATH.exists():
        try:
            with open(SECRETS_PATH) as f:
                current_secrets = json.load(f)
        except Exception:
            pass

    if config.openai_api_key:
        current_secrets["OPENAI_API_KEY"] = config.openai_api_key
        os.environ["OPENAI_API_KEY"] = config.openai_api_key

    if config.anthropic_api_key:
        current_secrets["ANTHROPIC_API_KEY"] = config.anthropic_api_key
        os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key

    with open(SECRETS_PATH, "w") as f:
        json.dump(current_secrets, f, indent=2)

    return {"status": "updated"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            status_payload = await status()
            messages = await list_messages(limit=20)
            await websocket.send_json({"status": status_payload, "messages": [m.model_dump() for m in messages]})
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        return
