from __future__ import annotations

from collections.abc import Callable
from typing import Any

import comm
from pycrdt import (
    Doc,
    Text,
    TransactionEvent,
    YMessageType,
    YSyncMessageType,
    create_sync_message,
    create_update_message,
    handle_sync_message,
)

from .widget import Widget


def handle_comm_opened(*args, **kwargs):
    # TODO handle comm open from front-end
    pass  # pragma: nocover


def register_comm_target():
    comm_manager = comm.get_comm_manager()
    if comm_manager is not None:
        comm_manager.register_target("ywidget", handle_comm_opened)


def create_widget_comm(
    data: dict | None = None,
    metadata: dict | None = None,
    comm_id: str | None = None,
) -> comm.base_comm.BaseComm:
    _comm = comm.create_comm(
        comm_id=comm_id,
        target_name="ywidget",
        data=data,
        metadata=metadata,
    )
    return _comm


class CommProvider:
    _on_receive: Callable[[bytes], None] | None

    def __init__(
        self,
        ydoc: Doc,
        comm: comm.base_comm.BaseComm,
    ) -> None:
        self._ydoc = ydoc
        self._comm = comm
        self._on_receive = None
        msg = create_sync_message(ydoc)
        self._comm.send(buffers=[msg])
        self._comm.on_msg(self._receive)

    def _receive(self, msg: dict[str, Any]):
        message = bytes(msg["buffers"][0])
        message_type = message[0]
        message_content = message[1:]
        if message_type == YMessageType.SYNC:
            reply = handle_sync_message(message_content, self._ydoc)
            if reply is not None:
                self._comm.send(buffers=[reply])
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self._ydoc.observe(self._send)
        elif message_type == 2:
            if self._on_receive is not None:
                self._on_receive(message_content)

    def _send(self, event: TransactionEvent):
        update = event.update
        message = create_update_message(update)
        self._comm.send(buffers=[message])

    def on_receive(self, callback: Callable[[bytes], None]):
        self._on_receive = callback

    def send(self, message: bytes):
        self._comm.send(buffers=[bytes([2]) + message])


class CommWidget(Widget):
    def __init__(
        self,
        ydoc: Doc | None = None,
        comm_data: dict | None = None,
        comm_metadata: dict | None = None,
        comm_id: str | None = None,
    ):
        super().__init__(ydoc)
        model_name = self.__class__.__name__
        _model_name = self.ydoc["_model_name"] = Text()
        _model_name += model_name
        if comm_metadata is None:
            comm_metadata = dict(
                ymodel_name=model_name,
                create_ydoc=not ydoc,
            )
        self._comm = create_widget_comm(comm_data, comm_metadata, comm_id)
        self._provider = CommProvider(self.ydoc, self._comm)

    def _repr_mimebundle_(self, *args, **kwargs):  # pragma: nocover
        plaintext = repr(self)
        if len(plaintext) > 110:
            plaintext = plaintext[:110] + '…'
        data = {
            "text/plain": plaintext,
            "application/vnd.jupyter.ywidget-view+json": {
                "version_major": 2,
                "version_minor": 0,
                "model_id": self._comm.comm_id,
            }
        }
        return data

    def on_receive(self, callback: Callable[[bytes], None]) -> None:
        self._provider.on_receive(callback)

    def send(self, message: bytes) -> None:
        self._provider.send(message)
