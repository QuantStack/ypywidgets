from textual.widgets import Switch as TextualSwitch

from ..switch import Switch as SwitchModel


class Switch(TextualSwitch):

    def __init__(self, model: SwitchModel) -> None:
        super().__init__()
        self.ymodel = model
        self.ymodel.yvalue.observe(self._on_ychange)

    def watch_value(self, value: bool) -> None:
        super().watch_value(value)
        self.ymodel.value = value

    def _on_ychange(self, event) -> None:
        self.value = self.ymodel.value
