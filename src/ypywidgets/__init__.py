import importlib.metadata

from .reactive import Reactive as Reactive
from .widget import Widget as Widget

try:
    __version__ = importlib.metadata.version("ypywidgets")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


from .comm import register_comm_target

register_comm_target()
