from textual.widgets import Checkbox as TextualCheckbox

from ..checkbox import Checkbox as CheckboxModel


class Checkbox(TextualCheckbox):

    def __init__(self, model: CheckboxModel) -> None:
        super().__init__()
        self.ymodel = model
        self.ymodel.yvalue.observe(self._on_ychange)

    def watch_value(self, value: bool) -> None:
        super().watch_value(value)
        self.ymodel.value = value

    def _on_ychange(self, event) -> None:
        self.value = self.ymodel.value
