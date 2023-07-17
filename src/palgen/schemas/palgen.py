import os
from typing import Annotated, Optional
from pydantic import BaseModel
from pathlib import Path


class ExtensionSettings(BaseModel):
    # inherit extensions from other projects
    inherit: bool = True
    # extra paths to check for extensions
    folders: list[Path] = []
    dependencies: list[Path] = []

    # Loaders
    #toml: bool = False  # not implemented
    python: bool = True
    manifest: bool = True

    inline: bool = True

class PalgenSettings(BaseModel):
    extensions: ExtensionSettings = ExtensionSettings()
    jobs:       Optional[int] = os.cpu_count() or 1
    output:     Annotated[Optional[Path], "Output folder"] = None
