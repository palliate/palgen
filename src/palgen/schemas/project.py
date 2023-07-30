from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    """ Basic project settings """
    name:        Annotated[str, "Project name"]
    version:     Annotated[str, Field(pattern=r"^[0-9.]+$"), "Version number"]
    description: Annotated[Optional[str], "Project description"] = ""
    sources:     Annotated[list[Path], "Source folders"] = []
