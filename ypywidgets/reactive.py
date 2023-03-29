from __future__ import annotations
from typing import Callable

from reacttrs.reactive import Reactive, ReactiveType


def set_attr(obj, name, value):
    try:
        with obj._ydoc.begin_transaction() as t:
            obj._attrs.set(t, name, value)
    except:
        # Already mutably borrowed
        pass


class reactive(Reactive[ReactiveType]):
    def __init__(
        self,
        default: ReactiveType | Callable[[], ReactiveType],
        *,
        init: bool = True,
        always_update: bool = False,
    ) -> None:
        super().__init__(
            default,
            init=init,
            always_update=always_update,
            on_set=set_attr,
        )
