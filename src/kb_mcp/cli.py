"""CLI interface for KB MCP Server."""
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from kb_mcp.db import get_db
from kb_mcp.services import ProjectService, RequirementService, KnowledgeService, SearchService
from kb_mcp.models import ProjectCreate, RequirementCreate, KnowledgeCreate
from kb_mcp.models.requirement import Priority

# Главное приложение
app = typer.Typer(help="KB MCP Server CLI - Knowledge Base Management")

# Подприложения (группы)
project_app = typer.Typer(help="Project management")
req_app = typer.Typer(help="Requirement management")
kb_app = typer.Typer(help="Knowledge management")

# Добавляем подгруппы к главному
app.add_typer(project_app, name="project")
app.add_typer(req_app, name="req")
app.add_typer(kb_app, name="kb")

console = Console()


def get_services():
    """Get service instances."""
    db = get_db()
    conn = db.connect()
    return {
        "project": ProjectService(conn),
        "requirement": RequirementService(conn),
        "knowledge": KnowledgeService(conn),
        "search": SearchService(conn),
        "db": db
    }


@app.command()
def init():
    """Initialize database."""
    db = get_db()
    db.connect()
    console.print("[green]✅ Database initialized![/green]")


# ============================================================================
# PROJECT COMMANDS
# ============================================================================

@project_app.command("list")
def project_list(limit: int = typer.Option(20, "--limit")):
    """List all projects."""
    svcs = get_services()
    projects = svcs["project"].list(limit)
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    table = Table(title=f"Projects ({len(projects)})")
    table.add_column("Name", style="green")
    table.add_column("Description", style="dim")
    table.add_column("ID (copy this)", style="cyan", no_wrap=True)
    
    for p in projects:
        table.add_row(p.name, p.description or "-", p.id)
    
    console.print(table)
    svcs["db"].close()


@project_app.command("create")
def project_create(name: str = typer.Argument(...), description: Optional[str] = typer.Option(None, "--desc")):
    """Create a new project."""
    svcs = get_services()
    p = svcs["project"].create(ProjectCreate(name=name, description=description))
    svcs["db"].connect().commit()
    console.print(f"[green]✅ Project created![/green]")
    console.print(f"[bold]Name:[/bold] {p.name}")
    console.print(f"[bold]ID:[/bold] [cyan]{p.id}[/cyan]")
    svcs["db"].close()


@project_app.command("get")
def project_get(project_id: str = typer.Argument(...)):
    """Get project details."""
    svcs = get_services()
    p = svcs["project"].get(project_id)
    
    if not p:
        console.print("[red]❌ Project not found[/red]")
        return
    
    rprint(f"[bold]Project:[/bold] {p.name}")
    rprint(f"[bold]ID:[/bold] {p.id}")
    rprint(f"[bold]Description:[/bold] {p.description or '-'}")
    console.print(f"[dim]Created: {p.created_at} | Updated: {p.updated_at}[/dim]")
    svcs["db"].close()


@project_app.command("delete")
def project_delete(project_id: str = typer.Argument(...)):
    """Delete a project."""
    svcs = get_services()
    if svcs["project"].delete(project_id):
        svcs["db"].connect().commit()
        console.print("[green]✅ Project deleted[/green]")
    else:
        console.print("[red]❌ Project not found[/red]")
    svcs["db"].close()


@project_app.command("search")
def project_search(query: str = typer.Argument(...), limit: int = typer.Option(10, "--limit")):
    """Search projects."""
    svcs = get_services()
    results = svcs["project"].search(query, limit)
    
    if not results:
        console.print("[yellow]No results[/yellow]")
        return
    
    for p in results:
        console.print(f"[bold]{p.name}[/bold]")
        console.print(f"[cyan]{p.id}[/cyan]")
        if p.description:
            console.print(f"  {p.description[:80]}...")
        console.print()


# ============================================================================
# REQUIREMENT COMMANDS
# ============================================================================

@req_app.command("list")
def req_list(project_id: str = typer.Argument(...), status: Optional[str] = None, priority: Optional[str] = None):
    """List requirements for a project."""
    svcs = get_services()
    reqs = svcs["requirement"].list(project_id, status, priority)
    
    if not reqs:
        console.print("[yellow]No requirements found[/yellow]")
        return
    
    table = Table(title=f"Requirements ({len(reqs)})")
    table.add_column("Priority", style="red")
    table.add_column("Status", style="yellow")
    table.add_column("Title", style="green")
    
    for r in reqs:
        table.add_row(r.priority.value, r.status.value, r.title)
    
    console.print(table)
    svcs["db"].close()


@req_app.command("create")
def req_create(
    project_id: str = typer.Argument(...),
    title: str = typer.Argument(...),
    content: str = typer.Argument(...),
    priority: str = typer.Option("medium")
):
    """Create a new requirement."""
    svcs = get_services()
    try:
        p = Priority(priority.lower())
    except ValueError:
        console.print("[red]❌ Invalid priority. Use: high, medium, low[/red]")
        return
    
    r = svcs["requirement"].create(RequirementCreate(
        project_id=project_id, title=title, content=content, priority=p
    ))
    svcs["db"].connect().commit()
    console.print(f"[green]✅ Requirement created:[/green] {r.title} ({r.id[:8]})")
    svcs["db"].close()


@req_app.command("get")
def req_get(requirement_id: str = typer.Argument(...)):
    """Get requirement details."""
    svcs = get_services()
    req = svcs["requirement"].get(requirement_id)
    
    if not req:
        console.print("[red]❌ Requirement not found[/red]")
        return
    
    rprint(f"[bold]{req.title}[/bold]")
    rprint(f"[dim]{req.content}[/dim]")
    console.print(f"\n[cyan]Priority:[/cyan] {req.priority.value} | [cyan]Status:[/cyan] {req.status.value}")
    console.print(f"[dim]ID: {req.id}[/dim]")
    svcs["db"].close()


# ============================================================================
# KNOWLEDGE COMMANDS
# ============================================================================

@kb_app.command("list")
def kb_list(project_id: Optional[str] = None, tags: Optional[str] = None, limit: int = 20):
    """List knowledge entries."""
    svcs = get_services()
    tag_list = tags.split(",") if tags else None
    entries = svcs["knowledge"].list(project_id=project_id, tags=tag_list, limit=limit)
    
    if not entries:
        console.print("[yellow]No entries found[/yellow]")
        return
    
    for e in entries:
        tags_str = ", ".join(e.tags) if e.tags else "-"
        console.print(f"[bold]{e.title}[/bold]")
        console.print(f"[cyan]ID:[/cyan] {e.id}")
        console.print(f"  {e.content[:100]}...")
        console.print(f"  [dim]Tags:[/dim] {tags_str}")
        console.print()


@kb_app.command("add")
def kb_add(
    project_id: str = typer.Argument(...),
    title: str = typer.Argument(...),
    content: str = typer.Argument(...),
    tags: Optional[str] = typer.Option(None, "--tags"),
    requirement_id: Optional[str] = typer.Option(None, "--req")
):
    """Add a knowledge entry."""
    svcs = get_services()
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    e = svcs["knowledge"].create(KnowledgeCreate(
        project_id=project_id,
        title=title,
        content=content,
        requirement_id=requirement_id,
        tags=tag_list
    ))
    svcs["db"].connect().commit()
    console.print(f"[green]✅ Entry added![/green]")
    console.print(f"[bold]Title:[/bold] {e.title}")
    console.print(f"[bold]ID:[/bold] [cyan]{e.id}[/cyan]")
    svcs["db"].close()


@kb_app.command("get")
def kb_get(entry_id: str = typer.Argument(...)):
    """Get knowledge entry."""
    svcs = get_services()
    e = svcs["knowledge"].get(entry_id)
    
    if not e:
        console.print("[red]❌ Entry not found[/red]")
        return
    
    rprint(f"[bold]{e.title}[/bold]")
    rprint(f"[dim]{e.content}[/dim]")
    console.print(f"\n[cyan]Tags:[/cyan] {', '.join(e.tags) if e.tags else '-'}")
    console.print(f"[dim]ID: {e.id} | Project: {e.project_id[:8]}...[/dim]")
    svcs["db"].close()


@kb_app.command("search")
def kb_search(query: str = typer.Argument(...), project_id: Optional[str] = None, limit: int = 10):
    """Search knowledge entries."""
    svcs = get_services()
    results = svcs["knowledge"].search(query, project_id, limit)
    
    if not results:
        console.print("[yellow]No results[/yellow]")
        return
    
    console.print(f"[bold]Found {len(results)} results:[/bold]\n")
    for e in results:
        console.print(f"[bold]{e.title}[/bold]")
        console.print(f"[cyan]ID:[/cyan] {e.id}")
        console.print(f"  {e.content[:120]}...")
        if e.tags:
            console.print(f"  [dim]Tags: {', '.join(e.tags)}[/dim]")
        console.print()
    svcs["db"].close()


# ============================================================================
# UNIFIED SEARCH
# ============================================================================

@app.command()
def search(query: str = typer.Argument(...), project_id: Optional[str] = None, limit: int = 10):
    """Unified search across all entities."""
    svcs = get_services()
    results = svcs["search"].search(query, project_id, limit=limit)
    
    if not results:
        console.print("[yellow]No results[/yellow]")
        return
    
    table = Table(title=f"Search Results ({len(results)})")
    table.add_column("Type", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Content", style="dim")
    
    for r in results:
        table.add_row(r.entity_type, r.title, r.content[:60] + "...")
    
    console.print(table)
    svcs["db"].close()


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
