from textual.widgets import Checkbox as TextualCheckbox

from ..checkbox import Checkbox as CheckboxModel


class Checkbox(TextualCheckbox):

    def __init__(self, model: CheckboxModel):
        super().__init__()
        self.ymodel = model
        self.ymodel.yvalue.observe(self._update)

    def watch_value(self, value: bool) -> None:
        super().watch_value(value)
        self.ymodel.value = value


    def _update(self, event):
        self.value = self.ymodel.value
