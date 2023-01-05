from typing import Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    name: str
    folders: list[str]
    version: str = Field(regex=r'[0-9.]+$')
    description: Optional[str] = ""
    output: Optional[str] = None
