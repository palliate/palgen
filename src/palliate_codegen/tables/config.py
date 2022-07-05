from palliate_codegen.parser import parser


class config(parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env.filters["has_cli"] = config.has_cli

    @staticmethod
    def has_cli(settings):
        return any([field["cli"] for field in settings if "cli" in field])

    def prepare(self):
        required_keys = set(['name', 'type'])
        cli = set()
        cli_shorthands = set()

        for v in self.table:
            if "name" not in v:
                raise KeyError("Config doesn't have a name")

            if "settings" not in v:
                raise KeyError(f"Config {v['name']} doesn't declare any settings.")
            v["outpath"] = self.path_for(v)
            #TODO check for collisions

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
                            raise KeyError(f"Duplicate cli argument: {field['command']}")
                        command = field["command"]
                    elif field["name"] in cli:
                        raise KeyError(f"Duplicate cli argument: {field['name']}")
                    cli.add(command)

                if "parent" in field:
                    if not field["parent"].endswith('.'):
                        field["parent"] += '.'

                if "default" in field:
                    field["default"] = self.fix_value(field["default"])

    def path_for(self, table):
        path = self.out_path
        if "namespace" in table:
            for namespace in table["namespace"].split("::"):
                path /= namespace.lower()

        return path / "config" / f"{table['name'].lower()}.h"

    def render(self):
        # config files
        template = self.env.get_template("config.h.in")
        self.output |= {v['outpath']: template.render(v)
                        for v
                        in self.table}

        if not self.no_cli:
            # commandline arguments
            template = self.env.get_template("cli.h.in")
            self.output[self.out_path / "cli.h"] = template.render({"settings": self.table})
