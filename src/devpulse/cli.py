"""DevPulse CLI — Your AI-powered tech radar."""

import click
from rich.console import Console

from devpulse import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="devpulse")
def main() -> None:
    """📡 DevPulse — Your AI-powered tech radar.

    Track packages, releases, and trends. Get briefed like a CTO.
    """


@main.command()
def status() -> None:
    """Show DevPulse status and tracked items."""
    console.print(f"[bold green]📡 DevPulse v{__version__}[/bold green]")
    console.print("[dim]Your AI-powered tech radar is ready.[/dim]")
    console.print()
    console.print("[yellow]No items tracked yet.[/yellow] Run [bold]devpulse track <package>[/bold] to get started.")


if __name__ == "__main__":
    main()
