from __future__ import annotations

from typing import Generic

from pycrdt import ReadTransaction
from reacttrs import Reactive as _Reactive
from reacttrs.reactive import Validator, ValueType, Watcher

from .widget import Widget


class Reactive(_Reactive, Generic[ValueType]):

    def __init__(
        self,
        default: ValueType,
        *,
        validate: Validator | None = None,
        watchers: set[Watcher] | None = None,
    ) -> None:
        super().__init__(default, validate=validate, watchers=watchers)

        @self.watch
        def _set_attr(obj: Widget, old: ValueType, new: ValueType) -> None:
            with obj.ydoc.transaction() as txn:
                # if we set the attribute, we are observing our own change: do nothing
                # we know it's the case because callbacks provide read-only transactions
                if not isinstance(txn, ReadTransaction):
                    obj._attrs[self._name] = new
