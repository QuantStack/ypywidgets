from __future__ import annotations
from typing import Callable

from pycrdt import ReadTransaction
from reacttrs.reactive import Reactive, ReactiveType


def set_attr(obj, name, value):
    with obj._attrs.doc.transaction() as txn:
        # if we set the attribute, we are observing our own change: do nothing
        # we know it's the case because callbacks provide read-only transactions
        if not isinstance(txn, ReadTransaction):
            obj._attrs[name] = value


class reactive(Reactive[ReactiveType]):
    def __init__(
        self,
        default: ReactiveType | Callable[[], ReactiveType],
        *,
        init: bool = True,
        always_update: bool = False,
        sync: bool = True,
    ) -> None:
        on_set = set_attr if sync else None
        super().__init__(
            default,
            init=init,
            always_update=always_update,
            on_set=on_set,
        )
