from .ypywidgets import Widget


class Switch(Widget):

    value: bool = False

    def __init__(self, open_comm: bool = True, **data) -> None:
        super().__init__(name="switch", open_comm=open_comm, **data)

    def toggle(self):
        self.value = not self.value
