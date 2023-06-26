import contextlib
from functools import cached_property
import importlib
import itertools
import logging
from pathlib import Path
from pkgutil import walk_packages

import click
from pydantic import BaseModel, ValidationError, validate_model
from pydantic.errors import MissingError

from palgen.module import Module
from palgen.palgen import Palgen
from palgen.cli.util import pydantic_to_click

_logger = logging.getLogger(__name__)


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
        commands.extend(self.builtins.keys())

        if not ctx.obj:
            init_context(ctx)

        if ctx.obj:
            assert isinstance(ctx.obj, Palgen)
            commands.extend(ctx.obj.modules.runnables)


        return commands

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = cmd_name.lower()

        if from_group := super().get_command(ctx, cmd_name):
            # commands registered to the top level group
            return from_group

        if cmd_name in self.builtins:
            # built-in commands
            return self.builtins[cmd_name]

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
            nonlocal key
            ctx.obj.run(key, kwargs)

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

    @cached_property
    def builtins(self):
        keys = set()
        builtins = {}
        for (name, attr) in itertools.chain(CommandLoader._load_from("palgen.cli.commands"),
                                            CommandLoader._load_from("palgen.integrations")):
            if name in keys:
                logging.error("Duplicate command name `%s` found, skipping", name)
                continue

            keys.add(name)
            builtins[name] = attr
        return builtins

    @staticmethod
    def _load_builtin(name):
        with contextlib.suppress(ImportError):
            mod = importlib.import_module(name)
            for ident, attr in mod.__dict__.items():
                if ident.startswith('_'):
                    continue

                if isinstance(attr, click.core.Command):
                    yield getattr(attr, "name", ident), attr

    @staticmethod
    def _load_from(name: str):
        with contextlib.suppress(ImportError):
            pkg = importlib.import_module(name)
            for module in walk_packages(path=pkg.__path__, prefix=f"{name}."):
                if module.ispkg:
                    continue

                yield from CommandLoader._load_builtin(module.name)
