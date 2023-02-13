from typing import Any
from pydantic import BaseModel, root_validator


class RootSettings(BaseModel):
    __root__: dict[Any, Any]

    @root_validator(pre=True)
    @classmethod
    def validate(cls, value):
        settings = value.get("__root__")
        assert "project" in settings, "Missing project table."
        settings.setdefault("palgen", {})

        for key, setting in settings.items():
            assert isinstance(setting, dict), \
                f"Setting {key} is not a table."

        return value

    # region boilerplate
    def get(self, key, default=None):
        return self.__root__.get(key, default)

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    def keys(self):
        return self.__root__.keys()

    def items(self):
        return self.__root__.items()
    # endregion
