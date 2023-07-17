# due to a bug in pyreverse this must be a full path
# otherwise it's confused with the palgen package
from palgen.schemas.palgen import PalgenSettings, ExtensionSettings

from .project import ProjectSettings
from .root import RootSettings

__all__ = ['PalgenSettings', 'ExtensionSettings', 'ProjectSettings', 'RootSettings']
