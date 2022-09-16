from palgen.parser import Parser


class Config(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env.filters["has_cli"] = Config.has_cli
        print(self.out_path)

    @staticmethod
    def has_cli(settings):
        return any([field["cli"] for field in settings if "cli" in field])

    def prepare(self):
        required_keys = set(['name', 'type'])
        cli = set()
        cli_shorthands = set()

        for v in self.input:
            if "name" not in v:
                raise KeyError("Config doesn't have a name")

            if "settings" not in v:
                raise KeyError(
                    f"Config {v['name']} doesn't declare any settings.")
            v["outpath"] = self._path_for(v)
            if "parent" in v:
                if not v["parent"].endswith('.'):
                    v["parent"] += '.'
            else:
                if "namespace" in v:
                    v["parent"] = '.'.join(v["namespace"].split("::")) + '.'

            for field in v["settings"]:
                missing_keys = required_keys - field.keys()
                if len(missing_keys):
                    raise KeyError("%s is missing the following keys %s" % (
                                   f"Setting {v['name']}.{field['name']}" if 'name' in field else f"A setting within {v['name']}",
                                   missing_keys))

                if "save" not in field:
                    field["save"] = True

                if "cli" in field:
                    if "shorthand" in field:
                        if field["shorthand"] in cli_shorthands:
                            raise KeyError(
                                f"Duplicate shorthand: {field['shorthand']}")
                        cli_shorthands.add(field["shorthand"])

                    command = field["name"]
                    if "command" in field:
                        if field["command"] in cli:
                            raise KeyError(
                                f"Duplicate cli argument: {field['command']}")
                        command = field["command"]
                    elif field["name"] in cli:
                        raise KeyError(
                            f"Duplicate cli argument: {field['name']}")
                    cli.add(command)

                if "parent" in field:
                    if not field["parent"].endswith('.'):
                        field["parent"] += '.'

                if "default" in field:
                    field["default"] = self._fix_value(field["default"])

    def render(self):
        # config files
        template = self.env.get_template("config/config.h.in")
        self.output |= {v['outpath']: template.render(v)
                        for v
                        in self.input}

        if "cli" not in self.settings or self.settings["cli"]:
            # commandline arguments
            template = self.env.get_template("config/cli.h.in")
            self.output[self.out_path /
                        "cli.h"] = template.render({"settings": self.input})

    def _path_for(self, table):
        return self.out_path                               \
            / table["source"].relative_to(self.root_path)  \
            / "config"                                     \
            / f"{table['name'].lower()}.h"

    def _fix_value(self, value) -> str:
        if type(value) is str:
            return f'"{value}"'

        elif type(value) is bool:
            return str(value).lower()

        elif type(value) is list:
            if len(value) > 1:
                raise ValueError(
                    "Raw default list contained more than one item")
            return value[0]

        return str(value)
