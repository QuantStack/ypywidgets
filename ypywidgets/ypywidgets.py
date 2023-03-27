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
        name: str,
        primary: bool = True,
        comm_data: Optional[Dict] = None,
        comm_metadata: Optional[Dict] = None,
    ) -> None:
        self._name = name
        self._ydoc = Y.YDoc()
        self._attrs = self._ydoc.get_map("attrs")
        self._comm = None
        if primary:
            self._comm_id = uuid4().hex
            self._comm = comm.create_comm(
                comm_id=self._comm_id,
                target_name=self._name,
                data=comm_data,
                metadata=comm_metadata,
            )
            self._comm.on_msg(self._receive)
            msg = sync(self._ydoc)
            self._comm.send(**msg)

    def __setattr__(self, k, v):
        if k.startswith("_"):
            self.__dict__[k] = v
        else:
            with self._ydoc.begin_transaction() as t:
                self._attrs.set(t, k, v)

    def __getattr__(self, k):
        if k.startswith("_"):
            return self.__getattribute__(k)

        return self._attrs[k]

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
