from typing import Optional

import typer
from typer_config import use_yaml_config

import requests
from requests.auth import HTTPDigestAuth

from janus import __app_name__, __version__
from janus.old.config import config_parser as conf

from janus.common import confirm_option_callback
from janus.logging import logger

import copy
import json

import questionary
from janus.old import config
from janus.projects import fetch_projects

app = typer.Typer()

@app.command()
@use_yaml_config(default_value="config.yaml") #TODO find a way to not load this if running with --help
def export(
    sourceUrl: str = typer.Option(str, "--sourceUrl", prompt="Source Ops Manager URL", callback=confirm_option_callback),
    sourceUsername: str = typer.Option( str, "--sourceUsername", prompt="Source Ops Manager API Key", callback=confirm_option_callback),
    sourceApiKey: str = typer.Option( str, "--sourceApiKey", prompt="Source Ops Manager API Key", callback=confirm_option_callback),
    outputFile: str = typer.Option( str, "--outputFile", prompt="Output file (can be used in import process)", callback=confirm_option_callback),
) -> None:
    """Export Alert Configs to the specified output file"""    
    projects = fetch_projects(sourceUrl, sourceUsername, sourceApiKey)

    choices = []
    projectIdNameDict = {}
    choice_template = "{} ({})"
    for project in projects['results']:
        choices.append(questionary.Choice(title=choice_template.format(project['name'], project['id'] ), value=project['id'], checked=True))
        projectIdNameDict[project['id']] = project['name']

    answer = questionary.checkbox(
        'Select projects to export Alert Configs from',
        choices=choices
    ).ask()

    export_alert_configs(sourceUrl, answer, projectIdNameDict, sourceUsername, sourceApiKey, outputFile)


@app.command(name="import")
@use_yaml_config(default_value="config.yaml")
def import_(
    destinationUrl: str = typer.Option(str, "--destinationUrl", prompt="Destination Ops Manager URL", callback=confirm_option_callback),
    destinationUsername: str = typer.Option( str, "--destinationUsername", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
    destinationApiKey: str = typer.Option( str, "--destinationApiKey", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
    inputFile: str = typer.Option( str, "--inputFile", prompt="Destination Ops Manager API Key", callback=confirm_option_callback),
    detectAndSkipDuplicates: bool = typer.Option( True, "--detectAndSkipDuplicates", prompt="Detect already existing Alert Configs created on the destination project i.e. avoid creation of duplicate Alert Configs", callback=confirm_option_callback),
) -> None:
    """Import Alert Configs from the specified input file"""
    import_alert_configs(inputFile, destinationUrl, destinationUsername, destinationApiKey, detectAndSkipDuplicates)



def fetch_alert_configs(host, group, username, apikey):
    response = requests.get(host+"/api/public/v1.0/groups/"+ group+"/alertConfigs",
                            auth=HTTPDigestAuth(username, apikey))
    response.raise_for_status()
    alert_configs = response.json()
    logger.debug("Fetched Alert Configs ...")
    logger.debug(alert_configs)
    return alert_configs


def export_alert_configs(host, groups, groupNameDict, username, apikey, outputFile):
    output = []
    for group in groups:
        alert_configs = fetch_alert_configs(host, group, username, apikey)
        element = {'project' : {'id': group, 'name': groupNameDict[group]}, 'alertConfigs': []}
        element['alertConfigs'] = alert_configs['results']
        output.append(element)

    json_object = json.dumps(output, indent=4)
    with open(outputFile, "w") as outfile:
        outfile.write(json_object)

def import_alert_configs(inputFile, destinationUrl, destinationUsername, destinationApikey, detectAndSkipDuplicates, continueOnError=True):
    with open(inputFile, 'r') as openfile:
        import_data = json.load(openfile) 

    destProjects = fetch_projects(destinationUrl, destinationUsername, destinationApikey)

    choices = []
    choicesDict = {}
    destProjectIdNameDict = {}
    choice_template = "{} ({})"
    for project in destProjects['results']:
        choice = questionary.Choice(title=choice_template.format(project['name'], project['id'] ), value=project['id'])
        choices.append(choice)
        destProjectIdNameDict[project['id']] = project['name']
        choicesDict[project['id']] = choice
    skipChoice = questionary.Choice(title="Skip", value="Skip")
    choices.append(skipChoice)
    
    for alert_config_import in import_data:
        logger.info("Import Alert Configs for originally Project - %s (%s)", alert_config_import['project']['name'], alert_config_import['project']['id'])

        if (alert_config_import['project']['id'] in destProjectIdNameDict):
            #destination project exists
            answer = questionary.select(
                'Found destination Project with same Id. Importing Alert Configs into same project?',
                instruction='Simply choose a different project',
                choices=choices,
                default=choicesDict[alert_config_import['project']['id']]
            ).ask()
        else:
            answer = questionary.select(
                'Destination Project with same Id not found. Select project to import Alert Configs to',
                choices=choices
            ).ask()

        if (answer == 'Skip'):
            logger.info("Skipping import of Alert Configs for originally Project - %s (%s)", alert_config_import['project']['name'], alert_config_import['project']['id'])
            continue
        
        __post_alert_configs(alert_config_import['alertConfigs'], destinationUrl, answer, destinationUsername, destinationApikey, detectAndSkipDuplicates, continueOnError)
    

def __alert_configs_create_payload_from_export_payload(alert_configs):
    response = []

    for alert in alert_configs:
        new_alert = copy.deepcopy(alert)

        del new_alert['links']
        del new_alert['id']
        del new_alert['created']
        del new_alert['updated']
        del new_alert['groupId']

        response.append(new_alert)

    return response


def __post_alert_configs(alert_configs, destinationUrl, destinationGroupId, destinationUsername, destinationApikey, skipDuplicates, continueOnError):
    migrated_alerts = 0
    skipped_alerts = 0
    failed_migrations = 0

    alert_configs_to_import = __alert_configs_create_payload_from_export_payload(alert_configs)

    if skipDuplicates:
        currentDestinationAlertConfigs = fetch_alert_configs(destinationUrl, destinationGroupId, destinationUsername, destinationApikey)
        current_alert_configs = __alert_configs_create_payload_from_export_payload(currentDestinationAlertConfigs['results'])
        
    logger.info("Attempting to import %d Alert Configs to %s with Project Id %s", len(alert_configs_to_import), destinationUrl, destinationGroupId)
    for alert in alert_configs_to_import:
        if skipDuplicates:
            #first check for possible existance of rule
            for ac in current_alert_configs:
                if ac == alert:
                    logger.debug("Found duplicate Alert Config")
                    logger.debug("To Import : %s", alert)
                    logger.debug("Existing  : %s", ac)
                    break
            else:    
                ac = None
            
            if ac != None:
                skipped_alerts += 1
                continue

        url = destinationUrl+"/api/public/v1.0/groups/"+destinationGroupId+"/alertConfigs/"
        headers = { "Content-Type" : "application/json" }
        logger.debug("===================================================")
        logger.debug("Posting Request to create new Alert Config ...")
        logger.debug("%s", json.dumps(alert))
        logger.debug("---------------")
        
        response = requests.post(url,
                    auth=HTTPDigestAuth(destinationUsername, destinationApikey),
                    data=json.dumps(alert),
                    headers=headers)
        logger.debug("Response ...")
        logger.debug("%s", vars(response))
        logger.debug("===================================================")

        if continueOnError and (response.status_code != requests.codes.created):
            logger.error("Unable to create new Alert Config - %s %s" % (response.status_code,response.reason))
            print( "Failed migration alert JSON:" )
            print (json.dumps(alert))
            failed_migrations += 1
        else:
            response.raise_for_status()
            migrated_alerts += 1
    logger.info("Import Alert Configs to %s with Project Id %s Complete. Imported: %d, Skipped(duplicates): %d, Failed: %d" % (destinationUrl, destinationGroupId, migrated_alerts, skipped_alerts, failed_migrations))



### TOOD
### verify integrations - import failing due to missing webhook config