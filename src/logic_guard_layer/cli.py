"""Command-line interface for Logic-Guard-Layer."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from logic_guard_layer import __version__


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option(version=__version__, prog_name="Logic-Guard-Layer")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool):
    """Logic-Guard-Layer: Neuro-symbolic validation for LLM outputs.

    A hybrid architecture combining LLMs with ontology-based reasoning
    to detect and correct logical inconsistencies in technical text.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@main.command()
@click.argument("text", required=False)
@click.option("-f", "--file", type=click.Path(exists=True), help="Read text from file")
@click.option("--no-correct", is_flag=True, help="Only validate, don't correct")
@click.option("-o", "--output", type=click.Path(), help="Write result to file")
@click.pass_context
def validate(
    ctx: click.Context,
    text: Optional[str],
    file: Optional[str],
    no_correct: bool,
    output: Optional[str],
):
    """Validate and optionally correct technical text.

    Examples:
        lgl validate "Motor M1 has 15000 operating hours"
        lgl validate -f input.txt -o output.txt
        lgl validate --no-correct "Text to check"
    """
    # Get input text
    if file:
        input_text = Path(file).read_text(encoding="utf-8")
    elif text:
        input_text = text
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        click.echo("Error: No input provided. Use TEXT argument, -f FILE, or pipe input.", err=True)
        ctx.exit(1)

    # Run validation
    async def run_validation():
        from logic_guard_layer.core.orchestrator import Orchestrator

        orchestrator = Orchestrator(auto_correct=not no_correct)
        try:
            result = await orchestrator.process(input_text)
            return result
        finally:
            await orchestrator.close()

    try:
        result = asyncio.run(run_validation())
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get("verbose"):
            import traceback
            traceback.print_exc()
        ctx.exit(1)

    # Format output
    output_lines = []
    output_lines.append("=" * 60)
    output_lines.append("LOGIC-GUARD-LAYER VALIDATION RESULT")
    output_lines.append("=" * 60)
    output_lines.append("")

    if result.is_valid:
        output_lines.append("[OK] Text is consistent with all constraints")
    else:
        output_lines.append(f"[ERROR] Found {len(result.final_violations)} violation(s)")
        for v in result.final_violations:
            output_lines.append(f"  - {v.type.value}: {v.message}")

    if result.was_corrected:
        output_lines.append("")
        output_lines.append("[CORRECTED TEXT]")
        output_lines.append("-" * 40)
        output_lines.append(result.final_text)
        output_lines.append("-" * 40)

    if result.correction_result:
        output_lines.append("")
        output_lines.append(f"Iterations: {result.correction_result.iterations}")

    output_lines.append(f"Processing time: {result.total_processing_time_ms:.2f}ms")
    output_lines.append("")

    output_text = "\n".join(output_lines)

    # Write output
    if output:
        Path(output).write_text(output_text, encoding="utf-8")
        click.echo(f"Result written to {output}")
    else:
        click.echo(output_text)

    # Exit code based on validity
    if not result.is_valid:
        ctx.exit(1)


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, reload: bool):
    """Start the web server with API and frontend.

    Examples:
        lgl serve
        lgl serve --port 3000
        lgl serve --reload  # Development mode
    """
    try:
        import uvicorn
        click.echo(f"Starting Logic-Guard-Layer server on http://{host}:{port}")
        click.echo("Press Ctrl+C to stop")
        uvicorn.run(
            "logic_guard_layer.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if ctx.obj.get("verbose") else "info",
        )
    except ImportError:
        click.echo("Error: uvicorn is required. Install with: pip install uvicorn", err=True)
        ctx.exit(1)


@main.command()
def constraints():
    """List all active validation constraints.

    Shows the constraint rules from the maintenance ontology
    that are used to validate technical text.
    """
    from logic_guard_layer.ontology.constraints import get_all_constraints

    constraints_list = get_all_constraints()

    click.echo("=" * 60)
    click.echo("LOGIC-GUARD-LAYER CONSTRAINTS")
    click.echo("=" * 60)
    click.echo("")

    for c in constraints_list:
        click.echo(f"[{c.id}] {c.name}")
        click.echo(f"    Type: {c.type.value}")
        click.echo(f"    Expression: {c.expression}")
        click.echo(f"    Description: {c.description}")
        click.echo("")


@main.command()
@click.option("--format", "fmt", type=click.Choice(["owl", "json"]), default="json", help="Output format")
def ontology(fmt: str):
    """Display the maintenance ontology.

    Shows the domain ontology used for semantic validation.
    """
    from logic_guard_layer.data import ONTOLOGY_PATH, SCHEMA_PATH

    if fmt == "json":
        schema_file = SCHEMA_PATH
        if schema_file.exists():
            click.echo(schema_file.read_text(encoding="utf-8"))
        else:
            click.echo("Error: maintenance_schema.json not found", err=True)
    else:
        owl_file = ONTOLOGY_PATH
        if owl_file.exists():
            click.echo(owl_file.read_text(encoding="utf-8"))
        else:
            click.echo("Error: maintenance.owl not found", err=True)


@main.command()
def info():
    """Show system information and configuration."""
    from logic_guard_layer.config import settings

    click.echo("=" * 60)
    click.echo("LOGIC-GUARD-LAYER SYSTEM INFO")
    click.echo("=" * 60)
    click.echo("")
    click.echo(f"Version: {__version__}")
    click.echo(f"LLM Model: {settings.openrouter_model}")
    click.echo(f"Max Iterations: {settings.max_correction_iterations}")
    click.echo(f"LLM Timeout: {settings.llm_timeout}s")
    click.echo(f"Debug Mode: {settings.debug}")
    click.echo("")

    # Check API key
    if settings.openrouter_api_key:
        key_preview = settings.openrouter_api_key[:8] + "..." + settings.openrouter_api_key[-4:]
        click.echo(f"API Key: {key_preview}")
    else:
        click.echo("API Key: [NOT SET] - Set OPENROUTER_API_KEY environment variable")
    click.echo("")


if __name__ == "__main__":
    main()
