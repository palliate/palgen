import click
from ..palgen import Palgen
from ...application.log import set_min_level


@click.command()
@click.option("-f", "--full", help="Search for templates and inputs.", is_flag=True)
@click.argument('module', required=False)
@click.pass_obj
def info(obj: Palgen, full, module):
    """Print project or module info and exit. This is a builtin command."""
    set_min_level(3)
    assert isinstance(obj, Palgen)

    if module is not None:
        mod = obj.modules.runnables[module]
        print(mod.to_string())
        return

    text = f"""\
Name:        {obj.project.name}
Description: {obj.project.description}
Version:     {obj.project.version}"""

    if full:
        text += f"""

Runnable:    {', '.join(obj.modules.runnables)}
Exportable:  {', '.join(obj.modules.runnables)}

Public:      {', '.join(obj.modules.public)}
Private:     {', '.join(obj.modules.private)}
"""
        # Subprojects: {list(ctx.obj.subprojects.keys())}
    print(text)
