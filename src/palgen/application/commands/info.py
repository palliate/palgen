import click

from ...application.log import set_min_level
from ...palgen import Palgen


@click.command()
@click.argument('extension', required=False)
@click.pass_obj
def info(obj: Palgen, extension: str):
    """Print project or extension info and exit. This is a builtin command."""
    set_min_level(3)
    assert isinstance(obj, Palgen)

    if extension is not None:
        mod = obj.extensions.runnable[extension].extension
        print(mod.to_string())
        return

    text = f"""\
Name:            {obj.project.name}
Description:     {obj.project.description}
Version:         {obj.project.version}

Sources:         {', '.join(str(f) for f in obj.project.sources)}
Output:          {obj.options.output}

Extension paths: {', '.join(str(f) for f in obj.options.extensions.folders)}
Dependencies:    {', '.join(str(d) for d in obj.options.extensions.dependencies)}

Extensions:
   Runnable:    {', '.join(obj.extensions.runnable)}
   Exportable:  {', '.join(obj.extensions.runnable)}
   Private:     {', '.join(obj.extensions.private)}
"""
    print(text)
