import typer
from click.core import ParameterSource
from click.types import BOOL
from rich.prompt import Prompt

from janus.logging import logger

def confirm_option_callback(ctx: typer.Context, param: typer.CallbackParam, value):
    if (ctx.get_parameter_source(param.name) in [ParameterSource.DEFAULT_MAP]):
        promt_text = f"{param.prompt} \[{value}]" #required format i.e. only [ has to be escaped
        confirmed = Prompt.ask(promt_text)
        if confirmed == '' :
            return value
        else:
            if (param.type.name == BOOL.name and isinstance(confirmed, str)):
                #TODO improve this to error out on invalid input
                return confirmed == 'True'
            else:
                return confirmed
    return value