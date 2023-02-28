from typing import Optional
from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    name: str
    version: str = Field(regex=r'[0-9.]+$')
    description: Optional[str] = ""

    output: Optional[str] = None
    folders: list[str] = []
