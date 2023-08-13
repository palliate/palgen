import os
from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel


class ExtensionSettings(BaseModel):
    """ Palgen extension settings """

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
    """ Palgen settings """

    extensions: ExtensionSettings = ExtensionSettings()
    jobs:       Optional[int] = os.cpu_count() or 1
    output:     Annotated[Optional[Path], "Output folder"] = None
