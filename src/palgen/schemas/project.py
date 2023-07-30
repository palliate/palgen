from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel


class ProjectSettings(BaseModel):
    """ Basic project settings """
    name:        Annotated[str, "Project name"]
    version:     Annotated[str, "Version number"] = "0"
    description: Annotated[Optional[str], "Project description"] = ""
    sources:     Annotated[list[Path], "Source folders"] = []
