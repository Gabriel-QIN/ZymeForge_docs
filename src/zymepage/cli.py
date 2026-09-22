"""ZymePage command-line entry point."""

from typing import Annotated

import typer

app = typer.Typer(name="zymepage", no_args_is_help=True)


@app.callback()
def main() -> None:
    """ZymeForge documentation and model catalog."""


@app.command("web")
def serve_web(
    host: Annotated[str, typer.Option(help="Interface to bind.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8000,
    reload: Annotated[bool, typer.Option(help="Reload when source files change.")] = False,
) -> None:
    """Serve the ZymePage tool catalog and model API."""
    import uvicorn

    uvicorn.run("zymepage.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
