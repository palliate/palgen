import contextlib
import importlib
import logging
from pathlib import Path

import click
from pydantic import BaseModel, ValidationError, validate_model
from pydantic.errors import MissingError

from palgen.module import Module
from palgen.palgen import Palgen
from palgen.util.cli import pydantic_to_click

logger = logging.getLogger(__name__)


def init_context(ctx, config: str | Path = Path.cwd()):
    if isinstance(config, str):
        config = Path(config)

    if config.is_dir():
        config /= "palgen.toml"

    if not config.exists():
        raise FileNotFoundError("palgen.toml not found")

    ctx.obj = Palgen(config)


class CommandLoader(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = super().list_commands(ctx)

        for subfolder in (Path(__file__).parent.parent / "integrations").iterdir():
            if not subfolder.is_dir():
                continue

            name = f"palgen.integrations.{subfolder.name}.cli"
            if self._load_builtin(name) is not None:
                commands.append(subfolder.name)

        if not ctx.obj:
            init_context(ctx)

        if ctx.obj:
            assert isinstance(ctx.obj, Palgen)
            commands.extend(ctx.obj.modules.runnables)

        return commands

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = cmd_name.lower()

        if from_group := super().get_command(ctx, cmd_name):
            # built-in commands
            return from_group

        if from_integrations := self._load_builtin(f"palgen.integrations.{cmd_name}.cli"):
            return from_integrations

        assert isinstance(ctx.obj, Palgen)
        if cmd_name in ctx.obj.modules.runnables:
            module = ctx.obj.modules.runnables[cmd_name]
            if hasattr(module, "cli"):
                return module.cli
            else:
                return CommandLoader._generate_cli(module, ctx.obj)

        return None

    @staticmethod
    def _generate_cli(module: Module, palgen: Palgen):
        key = module.name.lower()

        @click.command(name=key,
                       help=module.__doc__,
                       context_settings={'show_default': True})
        @click.pass_context
        def wrapper(ctx, **kwargs):
            nonlocal module
            parser = module(ctx.obj.root, ctx.obj.root, kwargs)
            parser.run(ctx.obj.files)

        if key in palgen.settings:
            assert issubclass(module.Settings, BaseModel)
            *_, errors = validate_model(module.Settings, palgen.settings[key])
            if errors:
                unfiltered = [error for error in errors.raw_errors
                              if not isinstance(error.exc, MissingError)]
                if unfiltered:
                    raise ValidationError(unfiltered, module.Settings)

        for field, options in pydantic_to_click(module.Settings):
            if key in palgen.settings and field in palgen.settings[key]:
                options["required"] = False
                options["default"] = palgen.settings[key][field]

            wrapper = click.option(f'--{field}', **options)(wrapper)

        return wrapper

    @staticmethod
    def _load_builtin(name):
        with contextlib.suppress(ImportError):
            mod = importlib.import_module(name)
            if hasattr(mod, "cli"):
                return mod.cli

        return None