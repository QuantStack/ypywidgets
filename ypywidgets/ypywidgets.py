from typing import Dict, Optional

import comm
from pycrdt import Doc, Map, Text, TransactionEvent

from .utils import (
    YMessageType,
    YSyncMessageType,
    create_update_message,
    process_sync_message,
    sync,
)


class Widget:

    _attrs: Optional[Map]

    def __init__(
        self,
        primary: bool = True,
        comm_data: Optional[Dict] = None,
        comm_metadata: Optional[Dict] = None,
        comm_id: Optional[str] = None,
        ydoc: Optional[Doc] = None,
    ) -> None:
        if ydoc:
            self._ydoc = ydoc
            self._attrs = None
            create_ydoc = False
        else:
            self._ydoc = Doc()
            self._attrs = Map()
            model_name = Text()
            self._ydoc["_attrs"] = self._attrs
            self._ydoc["_model_name"] = model_name
            self._attrs.observe(self._set_attr)
            create_ydoc = True
        if comm_id is None:
            comm_id = self._ydoc.guid
        self._comm = None
        if primary:
            model_name += self.__class__.__name__
            if comm_metadata is None:
                comm_metadata = dict(
                    ymodel_name=self.__class__.__name__,
                    create_ydoc=create_ydoc,
                )
            self._comm_id = comm_id
            self._comm = comm.create_comm(
                comm_id=self._comm_id,
                target_name="ywidget",
                data=comm_data,
                metadata=comm_metadata,
            )
            msg = sync(self._ydoc)
            self._comm.send(**msg)
            self._comm.on_msg(self._receive)

    @property
    def ydoc(self) -> Doc:
        return self._ydoc

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
                self._ydoc.observe(self._send)

    def _send(self, event: TransactionEvent):
        update = event.get_update()
        message = create_update_message(update)
        self._comm.send(buffers=[message])
