from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field

from palgen.util.schema import Model


class ProjectSettings(Model):
    name:        Annotated[str, "Project name"]
    version:     Annotated[str, Field(regex=r"^[0-9.]+$"), "Version number"]
    description: Annotated[Optional[str], "Project description"] = ""

    output:      Annotated[Optional[str], "Output folder"] = None
    folders:     Annotated[list[Path], "Source folders"] = []
