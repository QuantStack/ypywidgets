from .ypywidgets import Widget


class Switch(Widget):

    def __init__(self, value: bool = False, open_comm: bool = True) -> None:
        super().__init__(name="switch", open_comm=open_comm)
        self.yvalue = self.ydoc.get_map("value")
        self._set(value)

    def _set(self, value: bool) -> None:
        with self.ydoc.begin_transaction() as t:
            self.yvalue.set(t, "value",  value)

    @property
    def value(self) -> bool:
        return self.yvalue["value"]

    @value.setter
    def value(self, value: bool):
        if value == self.value:
            return

        self._set(value)

    def toggle(self):
        self.value = not self.value
