"""Department and social organization management for LeMMing.

This module implements the "organization of terminals" concept, where departments
are groups of agents that work together to achieve emergent intelligence through
social organization.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .agents import Agent, discover_agents
from .messages import OutboxEntry, collect_readable_outboxes
from .paths import get_agents_dir

logger = logging.getLogger(__name__)


@dataclass
class DepartmentMetadata:
    """Metadata for a department (a group of agents)."""

    name: str
    description: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    author: str = ""
    contact: str = ""
    readme: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "author": self.author,
            "contact": self.contact,
            "readme": self.readme,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DepartmentMetadata:
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            author=data.get("author", ""),
            contact=data.get("contact", ""),
            readme=data.get("readme", ""),
        )


@dataclass
class SocialRelationship:
    """Represents a social relationship between agents."""

    source: str
    target: str
    relationship_type: str  # "reports_to", "collaborates_with", "mentors", "informed_by"
    strength: float = 1.0  # 0.0 to 1.0, indicates relationship strength
    last_interaction_tick: int = 0
    interaction_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "last_interaction_tick": self.last_interaction_tick,
            "interaction_count": self.interaction_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SocialRelationship:
        return cls(
            source=data.get("source", ""),
            target=data.get("target", ""),
            relationship_type=data.get("relationship_type", "collaborates_with"),
            strength=float(data.get("strength", 1.0)),
            last_interaction_tick=int(data.get("last_interaction_tick", 0)),
            interaction_count=int(data.get("interaction_count", 0)),
        )


def get_department_file(base_path: Path, department_name: str) -> Path:
    """Get the path to a department.json file."""
    return base_path / "departments" / f"{department_name}.json"


def discover_departments(base_path: Path) -> list[DepartmentMetadata]:
    """Discover all departments from department.json files.

    Departments are defined by department.json files in the departments/ directory.
    Each department.json contains metadata about a group of agents.
    """
    departments_dir = base_path / "departments"
    if not departments_dir.exists():
        return []

    departments: list[DepartmentMetadata] = []
    for dept_file in departments_dir.glob("*.json"):
        try:
            with dept_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            dept = DepartmentMetadata.from_dict(data)
            departments.append(dept)
            logger.info(
                "department_discovered",
                extra={"event": "department_discovered", "name": dept.name},
            )
        except Exception as exc:
            logger.warning(
                "department_load_failed",
                extra={
                    "event": "department_load_failed",
                    "path": str(dept_file),
                    "error": str(exc),
                },
            )

    return departments


def save_department(base_path: Path, department: DepartmentMetadata) -> Path:
    """Save department metadata to a department.json file."""
    departments_dir = base_path / "departments"
    departments_dir.mkdir(parents=True, exist_ok=True)

    dept_file = departments_dir / f"{department.name}.json"
    with dept_file.open("w", encoding="utf-8") as f:
        json.dump(department.to_dict(), f, indent=2)

    logger.info(
        "department_saved",
        extra={"event": "department_saved", "name": department.name},
    )
    return dept_file


def get_department_agents(base_path: Path, department_name: str) -> list[Agent]:
    """Get all agents that belong to a department.

    Agents belong to a department if they are in a subdirectory that matches
    the department name, or if their folder is under departments/<name>/.
    """
    agents = discover_agents(base_path)
    department_agents: list[Agent] = []

    for agent in agents:
        # Check if agent is in the department directory
        if department_name in str(agent.path).replace("\\", "/"):
            department_agents.append(agent)

    return department_agents


def analyze_social_graph(base_path: Path, current_tick: int) -> list[SocialRelationship]:
    """Analyze the social graph from agent permissions and outbox interactions.

    Returns a list of social relationships between agents based on:
    1. Permission-based relationships (who can read whose outbox)
    2. Interaction history (actual message exchanges)
    """
    agents = discover_agents(base_path)
    relationships: list[SocialRelationship] = []

    # Build relationships from permissions
    for agent in agents:
        for target_name in agent.permissions.read_outboxes:
            if target_name == "*":
                # Wildcard: agent reads all outboxes
                for other in agents:
                    if other.name != agent.name:
                        relationships.append(
                            SocialRelationship(
                                source=agent.name,
                                target=other.name,
                                relationship_type="informed_by",
                                strength=0.8,
                            )
                        )
            elif target_name != agent.name:
                relationships.append(
                    SocialRelationship(
                        source=agent.name,
                        target=target_name,
                        relationship_type="informed_by",
                        strength=0.7,
                    )
                )

    # Analyze recent outbox interactions to strengthen relationships
    for agent in agents:
        outbox_dir = base_path / "agents" / agent.name / "outbox"
        if not outbox_dir.exists():
            continue

        # Count interactions with each recipient
        interaction_counts: dict[str, int] = {}
        recent_tick_threshold = max(0, current_tick - 100)

        for outbox_file in outbox_dir.glob("*.json"):
            try:
                with outbox_file.open("r", encoding="utf-8") as f:
                    entry_data = json.load(f)
                    entry = OutboxEntry.from_dict(entry_data)

                    if entry.tick >= recent_tick_threshold:
                        # Update interaction counts
                        for rel in relationships:
                            if rel.source == agent.name and rel.target in entry_data.get("to", []):
                                interaction_counts[rel.target] = interaction_counts.get(rel.target, 0) + 1
            except Exception:
                continue

        # Update relationship strengths based on interaction frequency
        for target, count in interaction_counts.items():
            for rel in relationships:
                if rel.source == agent.name and rel.target == target:
                    rel.interaction_count += count
                    rel.last_interaction_tick = current_tick
                    # Increase strength based on interaction frequency
                    rel.strength = min(1.0, rel.strength + (count * 0.05))

    return relationships


def save_social_graph(base_path: Path, relationships: list[SocialRelationship]) -> Path:
    """Save the social graph to a file for inspection."""
    social_dir = base_path / "social"
    social_dir.mkdir(parents=True, exist_ok=True)

    graph_file = social_dir / "social_graph.json"
    graph_data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "relationships": [rel.to_dict() for rel in relationships],
    }

    with graph_file.open("w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    logger.info(
        "social_graph_saved",
        extra={
            "event": "social_graph_saved",
            "relationships_count": len(relationships),
        },
    )
    return graph_file


def export_org_structure(base_path: Path) -> dict[str, Any]:
    """Export the complete organization structure to a dictionary.

    This provides a filesystem-backed snapshot of the entire organization,
    including departments, agents, and social relationships.
    """
    agents = discover_agents(base_path)
    departments = discover_departments(base_path)
    relationships = analyze_social_graph(base_path, current_tick=0)

    org_structure = {
        "exported_at": datetime.now(UTC).isoformat(),
        "statistics": {
            "total_agents": len(agents),
            "total_departments": len(departments),
            "total_relationships": len(relationships),
        },
        "departments": [dept.to_dict() for dept in departments],
        "agents": [
            {
                "name": agent.name,
                "title": agent.title,
                "short_description": agent.short_description,
                "schedule": {
                    "run_every_n_ticks": agent.schedule.run_every_n_ticks,
                    "phase_offset": agent.schedule.phase_offset,
                },
                "permissions": {
                    "read_outboxes": agent.permissions.read_outboxes,
                    "tools": agent.permissions.tools,
                },
            }
            for agent in agents
        ],
        "social_graph": [rel.to_dict() for rel in relationships],
    }

    return org_structure


def save_org_structure(base_path: Path, org_structure: dict[str, Any]) -> Path:
    """Save the organization structure to a file."""
    social_dir = base_path / "social"
    social_dir.mkdir(parents=True, exist_ok=True)

    org_file = social_dir / "organization.json"
    with org_file.open("w", encoding="utf-8") as f:
        json.dump(org_structure, f, indent=2)

    logger.info(
        "org_structure_saved",
        extra={"event": "org_structure_saved"},
    )
    return org_file


def validate_department(department: DepartmentMetadata) -> list[str]:
    """Validate department metadata.

    Returns a list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if not department.name:
        errors.append("Department name is required")

    if not department.description:
        errors.append("Department description is required")

    # Validate version format (simple semver-like)
    if department.version and not department.version.replace(".", "").isdigit():
        errors.append("Department version must be in numeric format (e.g., 1.0.0)")

    return errors
