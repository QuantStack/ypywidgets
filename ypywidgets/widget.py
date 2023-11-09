from __future__ import annotations

from pycrdt import Doc, Map, Text


class Widget:
    _attrs: Map | None
    _ydoc: Doc

    def __init__(self, ydoc: Doc | None = None) -> None:
        if ydoc is None:
            self._ydoc = Doc()
            self._attrs = Map()
            self._ydoc["_attrs"] = self._attrs
            self._ydoc["_model_name"] = Text()
            self._attrs.observe(self._set_attr)
        else:
            self._ydoc = ydoc
            self._attrs = None

    @property
    def ydoc(self) -> Doc:
        return self._ydoc

    def _set_attr(self, event):
        for k, v in event.keys.items():
            new_value = v["newValue"]
            if getattr(self, k) != new_value:
                setattr(self, k, new_value)
