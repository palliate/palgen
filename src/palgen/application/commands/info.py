import click
from ..palgen import Palgen
from ...application.log import set_min_level


@click.command()
@click.option("-f", "--full", help="Search for extensions and inputs.", is_flag=True)
@click.argument('extension', required=False)
@click.pass_obj
def info(obj: Palgen, full, extension):
    """Print project or extension info and exit. This is a builtin command."""
    set_min_level(3)
    assert isinstance(obj, Palgen)

    if extension is not None:
        mod = obj.extensions.runnables[extension]
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
"""

    if full:
        text += f"""

Runnable:    {', '.join(obj.extensions.runnables)}
Exportable:  {', '.join(obj.extensions.runnables)}

Public:      {', '.join(obj.extensions.public)}
Private:     {', '.join(obj.extensions.private)}
"""
    print(text)
