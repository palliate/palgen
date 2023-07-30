from typing import Any

from pydantic import RootModel, model_validator


class RootSettings(RootModel):
    """ Root schema for palgen.toml """

    root: dict[Any, Any]

    @model_validator(mode='before')
    @classmethod
    def validate(cls, value):
        assert "project" in value, "Missing project table."
        value.setdefault("palgen", {})

        for key, setting in value.items():
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
