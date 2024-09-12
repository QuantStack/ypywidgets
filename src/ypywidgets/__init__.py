import importlib.metadata

from .widget import Widget as Widget
from .reactive import Reactive as Reactive


try:
    __version__ = importlib.metadata.version("ypywidgets")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
