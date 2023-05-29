import click
from palgen.util.log import set_min_level


@click.command()
@click.option("-f", "--full", help="Search for templates and inputs.", is_flag=True)
@click.pass_context
def info(ctx, full):
    """Print project info and exit."""
    set_min_level(3)
    text = f"""\
Name:        {ctx.obj.project.name}
Description: {ctx.obj.project.description}
Version:     {ctx.obj.project.version}"""

    if full:
        text += f"""

Templates:   {list(ctx.obj.modules.keys())}"""
        # Subprojects: {list(ctx.obj.subprojects.keys())}
    print(text)
