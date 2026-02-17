"""CLI for MCP Toolbelt."""

import click
import uvicorn
import sys


@click.command()
@click.option("--port", "-p", default=8765, help="Port to run on")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--ngrok", is_flag=True, help="Expose via ngrok tunnel")
def main(port: int, host: str, ngrok: bool):
    """MCP Toolbelt - Debug, inspect, and mock MCP servers.

    Run a local MCP server with request logging, proxy mode, and mock tools.
    Set proxy dynamically via ?proxy=URL query param or the web UI.

    \b
    Examples:
      mcp-toolbelt                    # Run on localhost:8765
      mcp-toolbelt --port 9000        # Run on custom port
      mcp-toolbelt --ngrok            # Expose via ngrok
    """

    ngrok_url = None
    if ngrok:
        try:
            from pyngrok import ngrok as pyngrok
            tunnel = pyngrok.connect(port, bind_tls=True)
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

    from mcp_toolbelt import app as app_module
    uvicorn.run(
        app_module.app,
        host=host,
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
