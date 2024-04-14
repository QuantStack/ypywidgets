from __future__ import annotations

from typing import Generic

from pycrdt import ReadTransaction
from declare import Declare as _Declare
from declare._declare import Validator, ValueType, WatchMethodType, WatchDecorator, Watcher

from .widget import Widget


class NestedWatchDecorator(WatchDecorator):
    def __call__(
        self, method: WatchMethodType | None = None
    ) -> WatchMethodType | WatchDecorator[WatchMethodType]:
        prev_method = self._declare._watcher
        if prev_method is None:
            _method = method
        else:
            self._declare._watcher = None
            def _method(obj, old, new):
                method(obj, old, new)
                prev_method(obj, old, new)
        super().__call__(_method)


class Declare(_Declare, Generic[ValueType]):

    def __init__(
        self,
        default: ValueType,
        *,
        validate: Validator | None = None,
        watch: Watcher | None = None,
    ) -> None:
        super().__init__(default, validate=validate, watch=watch)

        @self.watch
        def _set_attr(obj: Widget, old: ValueType, new: ValueType) -> None:
            with obj.ydoc.transaction() as txn:
                # if we set the attribute, we are observing our own change: do nothing
                # we know it's the case because callbacks provide read-only transactions
                if not isinstance(txn, ReadTransaction):
                    obj._attrs[self._name] = new

    @property
    def watch(self) -> WatchDecorator:
        return NestedWatchDecorator(self)
