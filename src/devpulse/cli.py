"""DevPulse CLI — your AI-powered tech radar from the terminal.

Built with Typer — function arguments become CLI arguments automatically.
Type hints drive the parsing, no decorators needed.

Commands:
    devpulse track litellm              Track a PyPI package
    devpulse track --github BerriAI/x   Track a GitHub repo
    devpulse track --topic "AI agents"  Track a topic
    devpulse untrack litellm            Stop tracking
    devpulse list                       Show tracked items
    devpulse brief                      Get your AI briefing
    devpulse config model gpt-4o        Set default model
    devpulse config show                Show settings
"""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from devpulse import __version__
from devpulse.config import DevPulseConfig
from devpulse.models import ItemType

console = Console()

# ──────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────

app = typer.Typer(
    name="devpulse",
    help="📡 DevPulse — Your AI-powered tech radar.\n\nTrack packages, releases, and trends. Get briefed like a CTO.",
    no_args_is_help=True,
)

# Sub-app for "devpulse config ..."
config_app = typer.Typer(help="Manage DevPulse settings.")
app.add_typer(config_app, name="config")

# Shared config instance.
_config = DevPulseConfig()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"devpulse {__version__}")
        raise typer.Exit


@app.callback()
def _main(
    version: Annotated[
        bool, typer.Option("--version", "-v", help="Show version and exit.", callback=_version_callback)
    ] = False,
) -> None:
    """📡 DevPulse — Your AI-powered tech radar."""


def _resolve_model(model_override: str | None) -> str:
    """Figure out which LLM model to use (flag → env var → config → error)."""
    model = model_override or os.environ.get("DEVPULSE_MODEL") or _config.model
    if not model:
        console.print(
            "[red]No model configured.[/red] Set one with:\n"
            "  devpulse config model azure/gpt-4.1\n"
            "  or set DEVPULSE_MODEL env var\n"
            "  or pass --model flag"
        )
        raise typer.Exit(1)
    return model


# ──────────────────────────────────────────────
# track / untrack / list
# ──────────────────────────────────────────────


@app.command()
def track(
    name: Annotated[str, typer.Argument(help="Package name, repo (owner/repo), or topic to track.")],
    github: Annotated[bool, typer.Option("--github", help="Track as a GitHub repo.")] = False,
    topic: Annotated[bool, typer.Option("--topic", help="Track as a topic.")] = False,
    version: Annotated[str | None, typer.Option("--version", "-V", help="Current version you're using.")] = None,
) -> None:
    """Track a package, repo, or topic."""
    if github:
        item_type = ItemType.GITHUB
        source_url = f"https://github.com/{name}"
    elif topic:
        item_type = ItemType.TOPIC
        source_url = None
    else:
        item_type = ItemType.PYPI
        source_url = f"https://pypi.org/project/{name}/"

    try:
        item = _config.add_item(name, item_type, source_url=source_url, current_version=version)
        console.print(f"[green]✓[/green] Now tracking [bold]{item.name}[/bold] ({item.item_type.value})")
    except ValueError as exc:
        console.print(f"[yellow]{exc}[/yellow]")


@app.command()
def untrack(
    name: Annotated[str, typer.Argument(help="Name of the item to stop tracking.")],
) -> None:
    """Stop tracking a package, repo, or topic."""
    if _config.remove_item(name):
        console.print(f"[green]✓[/green] Stopped tracking [bold]{name}[/bold]")
    else:
        console.print(f"[yellow]Not tracking '{name}'[/yellow]")


@app.command(name="list")
def list_items() -> None:
    """Show all tracked items."""
    items = _config.tracked_items
    if not items:
        console.print("[yellow]No items tracked yet.[/yellow] Run [bold]devpulse track <package>[/bold] to start.")
        return

    table = Table(title=f"📡 DevPulse — Tracking {len(items)} items")
    table.add_column("Name", style="bold")
    table.add_column("Type", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Last Checked", style="dim")

    for item in items:
        last_checked = item.last_checked.strftime("%Y-%m-%d %H:%M") if item.last_checked else "never"
        table.add_row(
            item.name,
            item.item_type.value,
            item.current_version or "—",
            last_checked,
        )

    console.print(table)


# ──────────────────────────────────────────────
# brief
# ──────────────────────────────────────────────


@app.command()
def brief(
    model: Annotated[str | None, typer.Option("--model", "-m", help="LLM model to use.")] = None,
    raw: Annotated[bool, typer.Option("--raw", help="Print raw response without formatting.")] = False,
) -> None:
    """Get your AI-powered tech briefing.

    The agent checks your tracked packages, finds trending repos,
    and synthesizes everything into a prioritized briefing.
    """
    resolved_model = _resolve_model(model)
    items = _config.tracked_items
    packages = [i.name for i in items if i.item_type == ItemType.PYPI]
    topics = [i.name for i in items if i.item_type == ItemType.TOPIC]

    # Build the message for the agent
    parts = ["Give me a tech briefing."]
    if packages:
        parts.append(f"Check these PyPI packages for updates: {', '.join(packages)}.")
    if topics:
        parts.append(f"Also search for news about: {', '.join(topics)}.")
    if not packages and not topics:
        parts.append("I'm not tracking anything specific yet — give me general Python/AI trends.")

    message = " ".join(parts)

    console.print(f"[dim]Using model: {resolved_model}[/dim]")
    console.print("[dim]Fetching data and generating briefing...[/dim]\n")

    # Import here to avoid loading ADK/LiteLLM on every CLI invocation
    from devpulse.agents.orchestrator import run_agent

    try:
        response = run_agent(model=resolved_model, message=message)
    except Exception as exc:
        console.print(f"[red]Agent error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if raw:
        typer.echo(response)
    else:
        console.print(response)

    # Update last_checked for all tracked items
    for item in items:
        _config.update_last_checked(item.name)


# ──────────────────────────────────────────────
# config model / config show
# ──────────────────────────────────────────────


@config_app.command(name="model")
def config_model(
    model_name: Annotated[str, typer.Argument(help="LLM model string (e.g. azure/gpt-4.1, gpt-4o).")],
) -> None:
    """Set the default LLM model."""
    _config.model = model_name
    _config.save_settings()
    console.print(f"[green]✓[/green] Default model set to [bold]{model_name}[/bold]")


@config_app.command(name="show")
def config_show() -> None:
    """Show current configuration."""
    console.print(f"[bold]📡 DevPulse v{__version__}[/bold]\n")
    console.print(f"  Config dir:    [dim]{_config.config_dir}[/dim]")
    console.print(f"  Model:         [cyan]{_config.model or '(not set)'}[/cyan]")
    console.print(f"  Sources:       {', '.join(_config.sources)}")
    console.print(f"  Default days:  {_config.default_days}")
    console.print(f"  Tracked items: {len(_config.tracked_items)}")


# ──────────────────────────────────────────────
# status
# ──────────────────────────────────────────────


@app.command()
def status() -> None:
    """Show DevPulse status and tracked items."""
    config_show()
    console.print()
    list_items()
