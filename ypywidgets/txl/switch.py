from textual.widgets import Switch as TextualSwitch

from ..switch import Switch as SwitchModel
from .widget import init


class Switch(TextualSwitch):

    def __init__(self, model: SwitchModel) -> None:
        init(self, model)
