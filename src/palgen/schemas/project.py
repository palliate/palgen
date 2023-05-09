from typing import Optional, Annotated
from pydantic import Field
from palgen.util.schema import Model
from pathlib import Path

class ProjectSettings(Model):
    name: str
    version: str = Field(regex=r'[0-9.]+$')
    description: Optional[str] = ""

    output: Optional[str] = None
    #folders: Annotated[list[str], "Source folders"] = [] # TODO
    folders: list[Path] = []
