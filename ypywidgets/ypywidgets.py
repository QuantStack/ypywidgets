import asyncio
from functools import partial
from typing import Dict, Optional
from uuid import uuid4

import y_py as Y
from comm import create_comm
from comm.base_comm import BaseComm
from pydantic import PrivateAttr
from psygnal import EventedModel, EmissionInfo

from .yutils import (
    YMessageType,
    YSyncMessageType,
    create_update_message,
    process_sync_message,
    put_updates,
    sync,
)


class Widget(EventedModel):

    _ydoc: Y.YDoc = PrivateAttr(default_factory=Y.YDoc)
    _ymap: Y.YMap = PrivateAttr()
    _name: str = PrivateAttr()
    _update_queue: asyncio.Queue = PrivateAttr()
    _synced: asyncio.Event = PrivateAttr()
    _comm_id: str = PrivateAttr()
    _comm: BaseComm = PrivateAttr()

    def __init__(
        self,
        name: str,
        open_comm: bool,
        comm_data: Optional[Dict] = None,
        comm_metadata: Optional[Dict] = None,
        **data,
    ) -> None:
        super().__init__(**data)
        self._name = name
        self._update_queue = asyncio.Queue()
        self._ymap = self.ydoc.get_map("attributes")

        # do initial sync with ydoc
        with self.ydoc.begin_transaction() as t:
            self._ymap.update(t, self.dict())

        # events is a psygnal.SignalGroup, that contains a SignalInstance
        # for each field on the model. However, it can *also* be directly connect
        # to a callback, which will be called for *any* event on the model
        # with the EmissionInfo object passed as the first argument.
        self.events.connect(self._on_event)
        self.ymap.observe(self._on_ychange)

        if open_comm:
            self._synced = asyncio.Event()
            self._comm_id = uuid4().hex
            self._comm = create_comm(
                comm_id=self._comm_id,
                target_name=self._name,
                data=comm_data,
                metadata=comm_metadata,
            )
            self._comm.on_msg(self._receive)
            sync(self.ydoc, self._comm)
            asyncio.create_task(self._send())

    def _on_event(self, info: EmissionInfo) -> None:
        # called anytime any field changes
        field_name = info.signal.name
        # info.args is a tuple of the arguments "emitted"
        # in the most common case of a single argument, we unwrap it here.
        new_val = info.args[0] if len(info.args) == 1 else list(info.args)
        with self._ydoc.begin_transaction() as t:
            self._ymap.set(t, field_name, new_val)

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
            process_sync_message(message[1:], self.ydoc, self._comm)
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self._synced.set()

    async def _send(self):
        await self._synced.wait()
        self.ydoc.observe_after_transaction(
            partial(put_updates, self._update_queue)
        )
        while True:
            update = await self._update_queue.get()
            message = create_update_message(update)
            self._comm.send(buffers=[message])

    def _on_ychange(self, event) -> None:
        for k, v in event.target.items():
            try:
                setattr(self, k, v)
            except BaseException:
                pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def ydoc(self) -> Y.YDoc:
        return self._ydoc

    @property
    def ymap(self) -> Y.YMap:
        return self._ymap
