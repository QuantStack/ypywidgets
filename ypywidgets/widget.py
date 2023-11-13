from __future__ import annotations

from pycrdt import Doc, Map, Text


class Widget:
    _initialized = False
    _attrs: Map
    ydoc: Doc

    def __init__(self, ydoc: Doc | None = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.ydoc = Doc() if ydoc is None else ydoc
        self.ydoc["_attrs"] = self._attrs = Map()
        self.ydoc["_model_name"] = Text()
        self._attrs.observe(self._set_attr)
        for k, v in self._attrs.items():
            setattr(self, k, v)

    def _set_attr(self, event):
        for k, v in event.keys.items():
            new_value = v["newValue"]
            if getattr(self, k) != new_value:
                setattr(self, k, new_value)
