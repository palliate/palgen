from typing import Any
from pydantic import RootModel, root_validator


class RootSettings(RootModel):
    root: dict[Any, Any]

    @root_validator(pre=True, allow_reuse=True)
    @classmethod
    def validate(cls, value):
        settings = value.get("__root__")
        assert "project" in settings, "Missing project table."
        settings.setdefault("palgen", {})

        for key, setting in settings.items():
            assert isinstance(setting, dict), \
                f"Setting {key} is not a table."

        return value

    def get(self, key, default=None):
        return self.root.get(key, default)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def keys(self):
        return self.root.keys()

    def items(self):
        return self.root.items()
