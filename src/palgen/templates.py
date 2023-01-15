import importlib.util
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from pydantic import BaseModel, PrivateAttr

from palgen.template import Template

logger = logging.getLogger(__name__)


@dataclass
class TemplateMeta:
    name: str
    parser: type
    path: Path
    #TODO inheritable flag
    def __call__(self, root, settings=None):
        return self.parser(root, settings or {})


class Templates(BaseModel):
    # Feature flags
    #TODO
    toml: Optional[bool] = True
    py: Optional[bool] = True
    inline: Optional[bool] = True

    # palgen projects to inherit templates from
    #TODO
    inherit: Optional[list[str]] = []

    # additional project search paths
    #TODO
    folders: Optional[list[str]] = []
    repos: Optional[list[str]] = []

    _templates: dict[str, TemplateMeta] = PrivateAttr(default_factory=dict)

    def inherit_templates(self, templates: 'Templates'):
        for key, meta in templates:
            #TODO check if inheritable
            #TODO check for collisions

            self._templates[key] = meta

    def from_py(self, path: Path | str):
        if not self.py:
            return

        if not isinstance(path, Path):
            path = Path(path)

        # TODO precheck by inspecting AST before loading, see ast_helper.py
        spec = importlib.util.spec_from_file_location(str(uuid.uuid4().hex),
                                                      path)

        # file is pre-checked, these assertions should never fail
        assert spec, "Spec could not be loaded"
        assert spec.loader, "Spec has no loader"

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        attrs = [getattr(module, name)
                 for name in dir(module)
                 if not name.startswith('_')]

        for attr in attrs:
            if not isinstance(attr, type):
                continue
            if not issubclass(attr, Template) or attr is Template:
                continue

            name = attr.__name__.lower()
            if name in self._templates:
                logger.warning("Template %s redefined. Skipping.", name)
                continue

            logger.debug("Found template `%s`", name)
            self._templates[name] = TemplateMeta(name, attr, path)

    def from_toml(self, path: Path | str):
        if not self.toml:
            return

        if not isinstance(path, Path):
            path = Path(path)

        # TODO

    #region boilerplate
    def keys(self) -> Iterator[str]:
        return self._templates.keys()

    def values(self) -> Iterator[TemplateMeta]:
        return self._templates.values()

    def items(self) -> Iterator[tuple[str, TemplateMeta]]:
        return self._templates.items()

    def __getitem__(self, key) -> TemplateMeta:
        return self._templates[key]

    def __contains__(self, item) -> bool:
        return item in self._templates

    def __iter__(self) -> Iterator[tuple[str, TemplateMeta]]:
        return iter(self._templates.items())

    def __str__(self) -> str:
        return str(self._templates)
    #endregion
