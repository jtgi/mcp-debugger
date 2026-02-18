"""CLI for MCP Toolbelt."""

import os
import click
import uvicorn
import sys
from pathlib import Path


@click.command()
@click.option("--port", "-p", default=8765, help="Port to run on")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--ngrok", is_flag=True, help="Expose via ngrok tunnel")
@click.option("--ngrok-domain", default=None, help="Custom ngrok domain (or set NGROK_DOMAIN env var)")
@click.option("--config", "-c", type=click.Path(exists=True), help="Load config from JSON file")
def main(port: int, host: str, ngrok: bool, ngrok_domain: str | None, config: str | None):
    """MCP Toolbelt - Debug, inspect, and mock MCP servers.

    Run a local MCP server with request logging, proxy mode, and mock tools.
    Set proxy dynamically via ?proxy=URL query param or the web UI.

    \b
    Examples:
      mcp-toolbelt                       # Run on localhost:8765
      mcp-toolbelt --port 9000           # Custom port
      mcp-toolbelt --ngrok               # Expose via ngrok
      mcp-toolbelt --config config.json  # Load settings from file
    """
    from mcp_debugger import config as config_module
    from mcp_debugger import app as app_module

    # Load config if provided
    if config:
        cfg = config_module.load_config(Path(config))
        if cfg.get("proxy_target"):
            app_module.proxy_target = cfg["proxy_target"]

    domain = ngrok_domain or os.environ.get("NGROK_DOMAIN")

    ngrok_url = None
    if ngrok or domain:
        try:
            from pyngrok import ngrok as pyngrok
            kwargs = {"bind_tls": True}
            if domain:
                kwargs["domain"] = domain
            tunnel = pyngrok.connect(port, **kwargs)
            ngrok_url = tunnel.public_url
        except Exception as e:
            click.echo(f"Failed to start ngrok: {e}", err=True)
            click.echo("Make sure ngrok is installed and authenticated: ngrok authtoken <token>", err=True)
            sys.exit(1)

    click.echo()
    click.echo("  MCP Toolbelt")
    click.echo("  ────────────────────────────────────")
    click.echo(f"  Local:    http://{host}:{port}")
    click.echo(f"  MCP:      http://{host}:{port}/mcp")
    if ngrok_url:
        click.echo(f"  Public:   {ngrok_url}")
        click.echo(f"  MCP:      {ngrok_url}/mcp")
    click.echo("  ────────────────────────────────────")
    click.echo()

    uvicorn.run(
        app_module.app,
        host=host,
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
