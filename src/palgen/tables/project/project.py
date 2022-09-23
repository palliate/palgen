from palgen.parser import Parser
from palgen.log import logger
from palgen.validation import *
from git import Repo


class Project(Parser):
    settings_schema = Dict({
        'name': String,
        'description': Maybe(String),
        'version': String(pattern="[0-9.]+$"),
        'type': String(pattern="(application|library|plugin)$"),
        'folders': List(String),
        'requires': Maybe(List(String(pattern="[a-zA-Z]+/[0-9.]+$"))),
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"{self.settings_schema.check(self.settings)=}")

    def prepare(self):
        allowed_types = set(['application', 'library', 'plugin'])
        for project in self.input:
            if project.type not in allowed_types:
                raise ValueError(f"Build type {project.type} not recognized.")
            project.git = self._git_info(project.root)

            if project.type == "application":
                if self.application:
                    raise ValueError(
                        "Only one application build may be defined.")
                self.application = project

            elif project.type == "library":
                if self.library:
                    raise ValueError("Only one library build may be defined.")
                self.library = project

            else:
                self.plugins.append(project)

    def render(self):
        template = self.env.get_template("build/build.h.in")
        self.output |= {self.out_path / "src" / "build.h":
                        template.render({"application": self.application,
                                         "library": self.library,
                                         "plugins": self.plugins})}

    def _git_info(self, path):
        ret = None
        try:
            repo = Repo(path, search_parent_directories=True)
            remote = repo.remotes.origin.url

            ret = {
                "remote_url": remote,
                "web_url": remote
                .replace('.git', '')
                .replace(':', '/')
                .replace('git@', 'https://'),
                "commit": repo.head.commit.hexsha,
                "commit_short": repo.head.commit.hexsha[:7],
                "modified": repo.is_dirty()
            }

        except Exception as ex:
            logger.warning(f"Couldn't get git info: {repr(ex)}")

        return ret
