from palliate_codegen.parser import parser
from palliate_codegen.log import logger
from pathlib import Path


class build(parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _git_info(self, path):
        from git import Repo
        ret = None
        try:
            repo = Repo(path)
            head = repo.head.reference
            remote = repo.remotes.origin.url

            ret = {
                "remote_url": remote,
                "web_url": remote                     \
                           .replace('.git', '')       \
                           .replace(':', '/')         \
                           .replace('git@', 'https://'),
                "branch": head.name,
                "commit": head.commit.hexsha,
                "commit_short": head.commit.hexsha[:7],
                "modified": repo.is_dirty()
            }

        except Exception as ex:
            logger.error(f"Could not get git info from {path}. Please clone the project using git.")
            logger.error(f"Exception occured: {type(ex)}, {ex}")

        return ret

    def validate(self):
        required_keys = set(['version', 'type'])
        allowed_types = set(['application', 'library', 'plugin'])
        application = False
        library = False
        for key, table in self.table.items():
            missing_keys = required_keys - table.keys()
            if len(missing_keys):
                raise KeyError(
                    f"Build {key} is missing the following keys: {missing_keys}")

            if table["type"] not in allowed_types:
                raise ValueError(f"Build type {table['type']} not recognized.")

            # TODO refactor
            if table["type"] == "application":
                if application:
                    raise ValueError(
                        "Only one application build may be defined.")
                application = True

            elif table["type"] == "library":
                if library:
                    raise ValueError("Only one library build may be defined.")
                library = True

    def render(self):
        application = None
        library = None
        plugins = []
        for key, table in self.table.items():
            root = self.source_map[key]
            if "root" in table:
                root /= table["root"]
            root = root.resolve().absolute()
            table |= {"name": key, "root": str(root)}

            if table["git"] if "git" in table else True:
                table["git"] = self._git_info(root.resolve())

            # TODO refactor
            if table["type"] == "application":
                application = table
            elif table["type"] == "library":
                library = table
            else:
                plugins.append(table)

        template = self.env.get_template("build.h.in")
        self.output |= {self.out_path / "build.h":
                        template.render({"application": application,
                                         "library": library,
                                         "plugins": plugins})}
