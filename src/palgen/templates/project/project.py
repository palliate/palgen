import logging
from pathlib import Path

from palgen.parser import Parser
from palgen.validation import *
from git import Repo

logger = logging.getLogger('palgen')


class Project(Parser):
    settings_schema = Dict({
        'name': String,
        'description': Maybe(String),
        'version': String(pattern="[0-9.]+$"),
        'type': String(either=["application", "library", "plugin"]),
        'folders': List(String)
    })

    def __str__(self) -> str:
        output = (f"Project:     {self.settings['name']}\n"
                  f"Version:     {self.settings['version']}\n"
                  f"Type:        {self.settings['type']}\n")

        if "description" in self.settings:
            output += f"Description: {self.settings['description']}\n"

        return output

    def render(self):
        template = self.env.get_template("project.h.in")
        self.output = {input["source"] / "build.h":
                       template.render({"project": input["project"]})
                       for input in
                       self.input}

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
            logger.warning("Couldn't get git info: %s", repr(ex))

        return ret
