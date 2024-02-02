from typing import Optional

import typer
from typer_config import use_yaml_config
from click.core import ParameterSource
from rich.prompt import Prompt

import requests
from requests.auth import HTTPDigestAuth

from janus import __app_name__, __version__, config
from janus.config import config_parser as conf

## TODO add logging as per Shaker's script
app = typer.Typer()

export_app = typer.Typer()
app.add_typer(export_app, name="export")
import_app = typer.Typer()
app.add_typer(import_app, name="import")
migrate_app = typer.Typer()
app.add_typer(migrate_app, name="migrate")

def name_callback(value: str):
    value = typer.prompt("What's your name?")
    print(f"Hello {value}")
    if value != "Camila":
        raise typer.BadParameter("Only Camila is allowed")
    return value

def confirm_option_callback(ctx: typer.Context, param: typer.CallbackParam, value: str):
    if (ctx.get_parameter_source(param.name) in [ParameterSource.DEFAULT_MAP, ParameterSource.PROMPT]):
        promt_text = f"{param.prompt} \[{value}]" #required format i.e. only [ has to be escaped
        confirmed = Prompt.ask(promt_text)
        if confirmed == '' :
            return value
        else:
            return confirmed
    return value

@export_app.command()
@use_yaml_config(default_value="config.yaml") #TODO find a way to not load this if running with --help
def alert_configs(
    sourceUrl: str = typer.Option(str, "--sourceUrl", prompt="Source Ops Manager URL", callback=confirm_option_callback),
    sourceUsername: str = typer.Option( str, "--sourceUsername", prompt="Source Ops Manager API Key", callback=confirm_option_callback),
    sourceApiKey: str = typer.Option( str, "--sourceApiKey", prompt="Source Ops Manager API Key", callback=confirm_option_callback),
    outputFile: str = typer.Option( str, "--outputFile", prompt="Source Ops Manager API Key", callback=confirm_option_callback),
) -> None:
    """TODO Initialize the to-do database."""
    export_alert_configs(sourceUrl, "65bbe3ed8fc7793252c95f18", sourceUsername, sourceApiKey, outputFile)
    # if app_init_error:
    #     typer.secho(
    #         f'Creating config file failed with "{ERRORS[app_init_error]}"',
    #         fg=typer.colors.RED,
    #     )
    #     raise typer.Exit(1)
    # db_init_error = database.init_database(Path(db_path))
    # if db_init_error:
    #     typer.secho(
    #         f'Creating database failed with "{ERRORS[db_init_error]}"',
    #         fg=typer.colors.RED,
    #     )
    #     raise typer.Exit(1)
    # else:
    #     typer.secho(f"The to-do database is {db_path}", fg=typer.colors.GREEN)

@import_app.command()
@use_yaml_config(default_value="config.yaml")
def alert_configs(
    destinationUrl: str = typer.Option(str, "--destinationUrl", prompt="Destination Ops Manager URL", callback=confirm_option_callback),
    destinationUsername: str = typer.Option( str, "--destinationUsername", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
    destinationApiKey: str = typer.Option( str, "--destinationApiKey", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
    inputFile: str = typer.Option( str, "--inputFile", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
) -> None:
    """TODO Initialize the to-do database."""
    import_alert_configs(inputFile, destinationUrl, '65bbf83effc8a138f6164c5e', destinationUsername, destinationApiKey)

@app.command()
def version(
) -> None:
    """Print version information about the application"""
    _version_callback(True)
    
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
@use_yaml_config(default_value="config.yaml")
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
): 
    print("starting...")
    return config.init_app()


def fetch_alert_configs(host, group, username, apikey):
    response = requests.get(host+
            "/api/public/v1.0/groups/"+ group+"/alertConfigs"
            ,auth=HTTPDigestAuth(username, apikey))
    response.raise_for_status()
    alert_configs = response.json()
    print(alert_configs)
    return alert_configs

def export_alert_configs(host, group, username, apikey, outputFile):
    alert_configs = fetch_alert_configs(host, group, username, apikey)
    json_object = json.dumps(alert_configs, indent=4)
    with open(outputFile, "w") as outfile:
        outfile.write(json_object)

def migrate_alert_configs(host, group, username, apikey):
    alert_configs = fetch_alert_configs(host, group, username, apikey)
    __post_alert_configs(alert_configs=alert_configs,
                         targetHost=host,
                         targetGroupId='65bbf83effc8a138f6164c5e',
                         targetUsername=username,
                         targetApikey=apikey)

import copy
import json

def import_alert_configs(inputFile, destinationUrl, destinationGroupId, destinationUsername, destinationApikey, continueOnError=True):
    print ("importing ... ")
    print( continueOnError)
    with open(inputFile, 'r') as openfile:
        alert_configs = json.load(openfile) 
    print(alert_configs)
    print(type(alert_configs))
    __post_alert_configs(alert_configs, destinationUrl, destinationGroupId, destinationUsername, destinationApikey, True, continueOnError)
    

def __alert_configs_create_payload_from_export_payload(alert_configs):
    response = []

    for alert in alert_configs['results']:
        new_alert = copy.deepcopy(alert)
        print("============= SOURCE alert data ==============")
        print( json.dumps(alert))
        print("============= end SOURCE alert data ==============")

        del new_alert['links']
        del new_alert['id']
        del new_alert['created']
        del new_alert['updated']
        del new_alert['groupId']

        response.append(new_alert)

    return response


def __post_alert_configs(alert_configs, destinationUrl, destinationGroupId, destinationUsername, destinationApikey, skipDuplicates, continueOnError):
    migrated_alerts = 0
    failed_migrations = 0

    destination_alert_configs = __alert_configs_create_payload_from_export_payload(alert_configs)

    if skipDuplicates:
        currentDestinationAlertConfigs = fetch_alert_configs(destinationUrl, destinationGroupId, destinationUsername, destinationApikey)
        current_alert_configs = __alert_configs_create_payload_from_export_payload(currentDestinationAlertConfigs)
        
    for alert in destination_alert_configs:
        if skipDuplicates:
            #first check for possible existance of rule
            for ac in current_alert_configs:
                if ac == alert:
                    print("i found it!")
                    break
            else:    
                ac = None
            
            if ac != None:
                print("need to skip this one")
                continue

        url = destinationUrl+"/api/public/v1.0/groups/"+destinationGroupId+"/alertConfigs/"
        headers = { "Content-Type" : "application/json" }
        print("============= POST data ==============")
        print( json.dumps(alert) )
        print("============= end POST data ==============")

        response = requests.post(url,
                    auth=HTTPDigestAuth(destinationUsername, destinationApikey),
                    data=json.dumps(alert),
                    headers=headers)
        print("============= response ==============")
        print( vars(response))
        print("============= end response ==============")

        if continueOnError and (response.status_code != requests.codes.created):
            print ("ERROR %s %s" % (response.status_code,response.reason))
            print( "Failed migration alert JSON:" )
            print (json.dumps(alert))
            failed_migrations += 1
        else:
            response.raise_for_status()
            migrated_alerts += 1
    print ("Migrated %d alerts to %s (%d failures)" % (migrated_alerts, destinationUrl,failed_migrations))



### TOOD
### verify integrations - import failing due to missing webhook config
### Find way to avoid creating duplicates