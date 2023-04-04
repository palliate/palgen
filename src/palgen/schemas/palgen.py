from typing import Optional
from pydantic import BaseModel
from pathlib import Path


class ModuleSettings(BaseModel):
    # inherit modules from other projects
    inherit: bool = True
    # extra paths to check for modules
    extra_folders: list[Path] = []
    dependencies: Optional[Path] = None

    # Loaders
    #toml: bool = False  # not implemented
    python: bool = True
    manifest: bool = True


class PalgenSettings(BaseModel):
    output: Optional[str] = None
    folders: list[str] = []
    modules: ModuleSettings = ModuleSettings()
