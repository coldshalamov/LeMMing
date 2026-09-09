"""CLI commands for department management."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

import click

from .department import (
    DepartmentMetadata,
    discover_departments,
    export_org_structure,
    get_department_agents,
    get_department_file,
    save_department,
    save_org_structure,
    save_social_graph,
    validate_department,
)
from .paths import get_agents_dir

logger = logging.getLogger(__name__)


@click.group(name="department")
def department_group() -> None:
    """Manage departments (groups of agents)."""
    pass


@department_group.command(name="list")
def list_departments() -> None:
    """List all discovered departments."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    departments = discover_departments(base_path)

    if not departments:
        click.echo("No departments found.")
        return

    click.echo(f"\nFound {len(departments)} department(s):\n")
    for dept in departments:
        click.echo(f"  • {dept.name} v{dept.version}")
        click.echo(f"    {dept.description}")
        if dept.author:
            click.echo(f"    Author: {dept.author}")
        if dept.tags:
            click.echo(f"    Tags: {', '.join(dept.tags)}")
        click.echo()


@department_group.command(name="create")
@click.argument("name")
@click.option("--description", "-d", required=True, help="Department description")
@click.option("--author", "-a", default="", help="Author name")
@click.option("--readme", "-r", default="", help="README content")
def create_department(name: str, description: str, author: str, readme: str) -> None:
    """Create a new department."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    dept = DepartmentMetadata(
        name=name,
        description=description,
        author=author,
        readme=readme,
    )

    errors = validate_department(dept)
    if errors:
        click.echo("Validation errors:")
        for error in errors:
            click.echo(f"  • {error}")
        raise click.Abort()

    save_department(base_path, dept)
    click.echo(f"✓ Created department: {name}")


@department_group.command(name="show")
@click.argument("name")
def show_department(name: str) -> None:
    """Show details of a specific department."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    dept_file = get_department_file(base_path, name)

    if not dept_file.exists():
        click.echo(f"Department not found: {name}")
        raise click.Abort()

    with dept_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
        dept = DepartmentMetadata.from_dict(data)

    # Get agents in this department
    agents = get_department_agents(base_path, name)

    click.echo(f"\n{dept.name} v{dept.version}")
    click.echo(f"Description: {dept.description}")
    if dept.author:
        click.echo(f"Author: {dept.author}")
    if dept.contact:
        click.echo(f"Contact: {dept.contact}")
    if dept.created_at:
        click.echo(f"Created: {dept.created_at}")
    if dept.tags:
        click.echo(f"Tags: {', '.join(dept.tags)}")
    if dept.dependencies:
        click.echo(f"Dependencies: {', '.join(dept.dependencies)}")

    click.echo(f"\nAgents ({len(agents)}):")
    for agent in agents:
        click.echo(f"  • {agent.name} ({agent.title})")

    if dept.readme:
        click.echo(f"\nREADME:\n{dept.readme}")


@department_group.command(name="export")
@click.option("--output", "-o", default="organization.json", help="Output file path")
def export_structure(output: str) -> None:
    """Export complete organization structure to JSON."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    org_structure = export_org_structure(base_path)

    output_path = Path(output)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(org_structure, f, indent=2)

    click.echo(f"✓ Exported organization to {output_path}")
    click.echo(f"  Agents: {org_structure['statistics']['total_agents']}")
    click.echo(f"  Departments: {org_structure['statistics']['total_departments']}")
    click.echo(f"  Relationships: {org_structure['statistics']['total_relationships']}")


@department_group.command(name="package")
@click.argument("name")
@click.option("--output", "-o", help="Output directory (default: departments/)")
def package_department(name: str, output: str | None) -> None:
    """Package a department as a shareable bundle.

    Creates a zip file containing the department metadata and all agent folders
    that belong to this department.
    """
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    output_dir = Path(output) if output else (base_path / "departments")
    output_dir.mkdir(parents=True, exist_ok=True)

    dept_file = get_department_file(base_path, name)
    if not dept_file.exists():
        click.echo(f"Department not found: {name}")
        raise click.Abort()

    # Get agents in this department
    agents = get_department_agents(base_path, name)

    if not agents:
        click.echo(f"No agents found in department: {name}")
        raise click.Abort()

    # Create temporary directory for packaging
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / name
        package_dir.mkdir()

        # Copy department metadata
        shutil.copy(dept_file, package_dir / "department.json")

        # Copy agent folders
        agents_dir = get_agents_dir(base_path)
        for agent in agents:
            agent_src = agents_dir / agent.name
            agent_dst = package_dir / "agents" / agent.name
            shutil.copytree(agent_src, agent_dst)

        # Create README
        readme_content = f"""# {name} Department Bundle

This is a LeMMing department bundle containing {len(agents)} agent(s).

## Installation

1. Unzip this file
2. Copy the `agents/` folder contents to your LeMMing `agents/` directory
3. Copy `department.json` to your LeMMing `departments/` directory
4. Run `python -m lemming.cli bootstrap`
5. Start the engine: `python -m lemming.cli run`

## Agents Included

{chr(10).join(f"- {agent.name}: {agent.title}" for agent in agents)}

## Description

{dept_file.read_text(encoding="utf-8")}
"""
        (package_dir / "README.md").write_text(readme_content, encoding="utf-8")

        # Create zip file
        zip_path = output_dir / f"{name}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(package_dir))

    click.echo(f"✓ Packaged department: {name}")
    click.echo(f"  Location: {zip_path}")
    click.echo(f"  Agents: {len(agents)}")


@department_group.command(name="import")
@click.argument("bundle_path")
@click.option("--merge", "-m", is_flag=True, help="Merge with existing organization")
def import_department(bundle_path: str, merge: bool) -> None:
    """Import a department bundle into the current organization."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()
    bundle_file = Path(bundle_path)

    if not bundle_file.exists():
        click.echo(f"Bundle not found: {bundle_path}")
        raise click.Abort()

    if bundle_file.suffix != ".zip":
        click.echo("Bundle must be a .zip file")
        raise click.Abort()

    import tempfile
    import zipfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.unpack_archive(bundle_file, temp_path)

        # Find the department directory (should be root or first subdirectory)
        dept_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
        if not dept_dirs:
            click.echo("Invalid bundle: no department directory found")
            raise click.Abort()

        dept_path = dept_dirs[0]

        # Import department metadata
        dept_json = dept_path / "department.json"
        if dept_json.exists():
            with dept_json.open("r", encoding="utf-8") as f:
                dept_data = json.load(f)
            dept = DepartmentMetadata.from_dict(dept_data)

            existing_depts = discover_departments(base_path)
            existing_names = {d.name for d in existing_depts}

            if dept.name in existing_names and not merge:
                click.echo(f"Department already exists: {dept.name}")
                click.echo("Use --merge to overwrite")
                raise click.Abort()

            save_department(base_path, dept)
            click.echo(f"✓ Imported department metadata: {dept.name}")

        # Import agents
        agents_src = dept_path / "agents"
        agents_dst = get_agents_dir(base_path)
        agents_dst.mkdir(parents=True, exist_ok=True)

        if agents_src.exists():
            for agent_dir in agents_src.iterdir():
                if not agent_dir.is_dir():
                    continue

                agent_dst = agents_dst / agent_dir.name
                if agent_dst.exists() and not merge:
                    click.echo(f"Agent already exists: {agent_dir.name}")
                    click.echo("Use --merge to overwrite")
                    raise click.Abort()

                if agent_dst.exists():
                    shutil.rmtree(agent_dst)

                shutil.copytree(agent_dir, agent_dst)
                click.echo(f"✓ Imported agent: {agent_dir.name}")

    click.echo(f"\n✓ Department import complete. Run 'python -m lemming.cli bootstrap' to finalize.")


@department_group.command(name="analyze")
@click.option("--output", "-o", default="social_graph.json", help="Output file path")
def analyze_social(output: str) -> None:
    """Analyze and export the social graph of the organization."""
    from .cli import setup_logging

    setup_logging(level="INFO")

    base_path = Path.cwd()

    # Load current tick
    from .engine import load_tick

    tick = load_tick(base_path)

    # Analyze social graph
    from .department import analyze_social_graph

    relationships = analyze_social_graph(base_path, tick)
    save_social_graph(base_path, relationships)

    # Export to specified output
    output_path = Path(output)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "current_tick": tick,
                "relationships": [rel.to_dict() for rel in relationships],
            },
            f,
            indent=2,
        )

    click.echo(f"✓ Analyzed social graph: {len(relationships)} relationships")
    click.echo(f"  Output: {output_path}")

    # Show summary
    relationship_types: dict[str, int] = {}
    for rel in relationships:
        rtype = rel.relationship_type
        relationship_types[rtype] = relationship_types.get(rtype, 0) + 1

    click.echo("\nRelationship types:")
    for rtype, count in sorted(relationship_types.items()):
        click.echo(f"  {rtype}: {count}")
