import asyncio
from functools import partial
from typing import Dict, Optional
from uuid import uuid4

import y_py as Y
from comm import create_comm

from .yutils import (
    YMessageType,
    YSyncMessageType,
    create_update_message,
    process_sync_message,
    put_updates,
    sync,
)


class Widget:
    def __init__(
        self,
        name: str,
        open_comm: bool,
        comm_data: Optional[Dict] = None,
        comm_metadata: Optional[Dict] = None,
    ) -> None:
        self.name = name
        self._update_queue = asyncio.Queue()
        self.ydoc = Y.YDoc()
        if open_comm:
            self.synced = asyncio.Event()
            self.comm_id = uuid4().hex
            self.comm = create_comm(
                comm_id=self.comm_id,
                target_name=self.name,
                data=comm_data,
                metadata=comm_metadata,
            )
            self.comm.on_msg(self._receive)
            sync(self.ydoc, self.comm)
            asyncio.create_task(self._send())

    def _repr_mimebundle_(self, **kwargs):
        plaintext = repr(self)
        if len(plaintext) > 110:
            plaintext = plaintext[:110] + '…'
        data = {
            "text/plain": plaintext,
            "application/vnd.jupyter.ywidget-view+json": {
                "version_major": 2,
                "version_minor": 0,
                "model_id": self.comm_id
            }
        }
        return data

    def _receive(self, msg):
        message = bytes(msg["buffers"][0])
        if message[0] == YMessageType.SYNC:
            process_sync_message(message[1:], self.ydoc, self.comm)
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self.synced.set()

    async def _send(self):
        await self.synced.wait()
        self.ydoc.observe_after_transaction(
            partial(put_updates, self._update_queue)
        )
        while True:
            update = await self._update_queue.get()
            message = create_update_message(update)
            self.comm.send(buffers=[message])
