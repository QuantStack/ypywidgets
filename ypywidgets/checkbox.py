from .ypywidgets import Widget


class Checkbox(Widget):

    def __init__(self, value: bool = False, open_comm: bool = True):
        super().__init__(name="checkbox", open_comm=open_comm)
        self.yvalue = self.ydoc.get_map("value")
        with self.ydoc.begin_transaction() as t:
            self.yvalue.set(t ,"value",  value)

    def _set(self, value: bool):
        with self.ydoc.begin_transaction() as t:
            self.yvalue.set(t ,"value",  value)

    @property
    def value(self) -> bool:
        return self.yvalue["value"]

    @value.setter
    def value(self, value: bool):
        # if same value, nothing to do
        if value == self.value:
            return

        self._set(value)

    def toggle(self):
        self.value = not self.value
