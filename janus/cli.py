from typing import Optional

import typer
from typer_config import use_yaml_config

import requests
from requests.auth import HTTPDigestAuth

from janus import __app_name__, __version__, alert_configs_cli

from janus.logging import logger, setDebugLogLevel

app = typer.Typer()

app = typer.Typer()
app.add_typer(alert_configs_cli.app, name="alert-configs")

@app.command()
def version() -> None:
    """Print version information about the application"""
    _version_callback(True)
    
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

def _debug_logging_callback(value: bool) -> None:
    if value:
        setDebugLogLevel()

@app.callback()
# @use_yaml_config(default_value="config.yaml")
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logs",
        callback=_debug_logging_callback,
        is_eager=False,
        rich_help_panel="Customization and Utils"
    )
): 
    logger.debug("Starting janus ...")
    logger.debug("[DEBUG LOGGING ENABLED]")
    




### TOOD
### verify integrations - import failing due to missing webhook config
### Find way to avoid creating duplicates