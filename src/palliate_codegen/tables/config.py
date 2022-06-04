from palliate_codegen.parser import parser


class config(parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env.filters["has_cli"] = config.has_cli

    @staticmethod
    def has_cli(settings):
        return any([field["cli"] for field in settings if "cli" in field])

    def validate(self):
        required_keys = set(['name', 'type'])
        cli = set()
        cli_shorthands = set()

        for k, v in self.table.items():
            if "settings" not in v:
                raise KeyError(f"Config {k} doesn't declare any settings.")

            v["name"] = k
            for field in v["settings"]:
                missing_keys = required_keys - field.keys()
                if len(missing_keys):
                    raise KeyError("%s is missing the following keys %s" % (
                                   f"Setting {k}.{field['name']}" if 'name' in field else f"A setting within {k}",
                                   missing_keys))

                if "save" not in field:
                    field["save"] = True

                if "cli" in field:
                    if "shorthand" in field:
                        if field["shorthand"] in cli_shorthands:
                            raise KeyError(
                                f"Duplicate shorthand: {field['shorthand']}")
                        cli_shorthands.add(field["shorthand"])

                    if field["name"] in cli:
                        raise KeyError(
                            f"Duplicate cli argument: {field['name']}")
                    cli.add(field["name"])

                if "default" not in field:
                    continue
                field["default"] = self.fix_value(field["default"])

            # make sure smybol names are unique
            if len(v["settings"]) != len(set(field["name"] for field in v["settings"])):
                raise ValueError(f"Key collision within {k}")

    def render(self):
        # config files
        template = self.env.get_template("config.h.in")
        self.output |= {self.out_path / "config" / f"{k}.h": template.render(v)
                        for k, v
                        in self.table.items()}

        # commandline arguments
        template = self.env.get_template("cli.h.in")
        self.output[self.out_path /
                    "cli.h"] = template.render({"settings": self.table})
