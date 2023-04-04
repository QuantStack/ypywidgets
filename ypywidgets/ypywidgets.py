from typing import Dict, Optional
from uuid import uuid4

import comm
import y_py as Y

from .utils import (
    YMessageType,
    YSyncMessageType,
    create_update_message,
    process_sync_message,
    sync,
)


class Widget:

    def __init__(
        self,
        primary: bool = True,
        comm_data: Optional[Dict] = None,
        comm_metadata: Optional[Dict] = None,
    ) -> None:
        self._ydoc = Y.YDoc()
        self._attrs = self._ydoc.get_map("_attrs")
        self._attrs.observe(self._set_attr)
        self._comm = None
        if primary:
            if comm_metadata is None:
                comm_metadata = {"ymodel_name": self.__class__.__name__}
            self._comm_id = uuid4().hex
            self._comm = comm.create_comm(
                comm_id=self._comm_id,
                target_name="ywidget",
                data=comm_data,
                metadata=comm_metadata,
            )
            self._comm.on_msg(self._receive)
            msg = sync(self._ydoc)
            self._comm.send(**msg)

    def _set_attr(self, event):
        for k, v in event.keys.items():
            new_value = v["newValue"]
            if getattr(self, k) != new_value:
                setattr(self, k, new_value)

    def _repr_mimebundle_(self, **kwargs):
        plaintext = repr(self)
        if len(plaintext) > 110:
            plaintext = plaintext[:110] + '…'
        data = {
            "text/plain": plaintext,
            "application/vnd.jupyter.ywidget-view+json": {
                "version_major": 2,
                "version_minor": 0,
                "model_id": self._comm_id
            }
        }
        return data

    def _receive(self, msg):
        message = bytes(msg["buffers"][0])
        if message[0] == YMessageType.SYNC:
            reply = process_sync_message(message[1:], self._ydoc)
            if reply:
                self._comm.send(buffers=[reply])
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self._ydoc.observe_after_transaction(self._send)

    def _send(self, event: Y.AfterTransactionEvent):
        update = event.get_update()
        message = create_update_message(update)
        self._comm.send(buffers=[message])
