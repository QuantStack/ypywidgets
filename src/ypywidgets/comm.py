from __future__ import annotations

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
    def __init__(
        self,
        ydoc: Doc,
        comm: comm.base_comm.BaseComm,
    ) -> None:
        self._ydoc = ydoc
        self._comm = comm
        msg = create_sync_message(ydoc)
        self._comm.send(buffers=[msg])
        self._comm.on_msg(self._receive)

    def _receive(self, msg):
        message = bytes(msg["buffers"][0])
        if message[0] == YMessageType.SYNC:
            reply = handle_sync_message(message[1:], self._ydoc)
            if reply is not None:
                self._comm.send(buffers=[reply])
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self._ydoc.observe(self._send)

    def _send(self, event: TransactionEvent):
        update = event.update
        message = create_update_message(update)
        self._comm.send(buffers=[message])


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
        CommProvider(self.ydoc, self._comm)

    def _repr_mimebundle_(self, **kwargs):
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
