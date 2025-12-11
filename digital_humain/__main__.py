"""Main CLI entry point for Digital Humain."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from digital_humain.utils.logger import setup_logger
from digital_humain.utils.config import load_config, save_config, get_default_config

app = typer.Typer(
    name="digital-humain",
    help="Self-hosted Agentic AI for Enterprise Desktop Automation"
)
console = Console()


@app.command()
def init(
    config_path: str = typer.Option(
        "config/config.yaml",
        help="Path to configuration file"
    )
):
    """Initialize Digital Humain with default configuration."""
    console.print("\n[bold blue]Digital Humain - Initialization[/bold blue]")
    
    # Check if config already exists
    if Path(config_path).exists():
        overwrite = typer.confirm(
            f"Configuration file {config_path} already exists. Overwrite?"
        )
        if not overwrite:
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    # Create default config
    config = get_default_config()
    
    if save_config(config, config_path):
        console.print(f"[green]✓ Configuration saved to {config_path}[/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Install Ollama: https://ollama.ai")
        console.print("2. Pull a model: ollama pull llama2")
        console.print("3. Start Ollama: ollama serve")
        console.print("4. Run an example: python examples/simple_automation.py")
    else:
        console.print("[red]✗ Failed to save configuration[/red]")


@app.command()
def info(
    config_path: str = typer.Option(
        "config/config.yaml",
        help="Path to configuration file"
    )
):
    """Show system information and configuration."""
    console.print("\n[bold blue]Digital Humain - System Information[/bold blue]\n")
    
    # Load configuration
    config = load_config(config_path)
    
    # Create info table
    table = Table(title="Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # LLM settings
    llm_config = config.get("llm", {})
    table.add_row("LLM Provider", llm_config.get("provider", "N/A"))
    table.add_row("LLM Model", llm_config.get("model", "N/A"))
    table.add_row("LLM Base URL", llm_config.get("base_url", "N/A"))
    
    # Agent settings
    agent_config = config.get("agents", {})
    table.add_row("Max Iterations", str(agent_config.get("max_iterations", "N/A")))
    table.add_row("Verbose Mode", str(agent_config.get("verbose", "N/A")))
    
    # Logging settings
    log_config = config.get("logging", {})
    table.add_row("Log Level", log_config.get("level", "N/A"))
    table.add_row("Log File", log_config.get("log_file", "N/A"))
    
    console.print(table)
    console.print()


@app.command()
def check():
    """Check system dependencies and configuration."""
    console.print("\n[bold blue]Digital Humain - System Check[/bold blue]\n")
    
    checks = []
    
    # Check Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 9)
    checks.append(("Python Version", python_version, python_ok))
    
    # Check Ollama connectivity
    try:
        from digital_humain.core.llm import OllamaProvider
        ollama = OllamaProvider()
        models = ollama.list_models()
        ollama_ok = len(models) > 0
        ollama_msg = f"{len(models)} models available" if ollama_ok else "No models found"
    except Exception as e:
        ollama_ok = False
        ollama_msg = f"Error: {str(e)[:50]}"
    checks.append(("Ollama Server", ollama_msg, ollama_ok))
    
    # Check required packages
    required_packages = [
        "langgraph",
        "langchain",
        "pillow",
        "pyautogui",
        "pydantic",
        "loguru"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            checks.append((f"Package: {package}", "Installed", True))
        except ImportError:
            checks.append((f"Package: {package}", "Not installed", False))
    
    # Display results
    table = Table(title="System Check Results", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Result", style="white")
    
    for component, status, ok in checks:
        status_icon = "✓" if ok else "✗"
        status_color = "green" if ok else "red"
        table.add_row(component, status, f"[{status_color}]{status_icon}[/{status_color}]")
    
    console.print(table)
    
    # Summary
    total = len(checks)
    passed = sum(1 for _, _, ok in checks if ok)
    
    console.print()
    if passed == total:
        console.print(f"[green]All checks passed ({passed}/{total})[/green]")
    else:
        console.print(f"[yellow]{passed}/{total} checks passed[/yellow]")
        console.print("\n[bold]To fix issues:[/bold]")
        if not ollama_ok:
            console.print("- Install and start Ollama: https://ollama.ai")
            console.print("- Pull a model: ollama pull llama2")
    
    console.print()


@app.command()
def version():
    """Show version information."""
    from digital_humain import __version__
    console.print(f"\n[bold blue]Digital Humain[/bold blue] version [green]{__version__}[/green]\n")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
