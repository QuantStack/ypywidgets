import asyncio
import time
from typing import Optional

import comm
import pytest
import y_py as Y
from ypywidgets import Widget
from ypywidgets.utils import YMessageType, YSyncMessageType, create_update_message, process_sync_message, sync


class MockComm(comm.base_comm.BaseComm):

    def __init__(
            self,
            comm_id=None,
            target_name=None,
            data=None,
            metadata=None,
    ):
        self.send_queue = asyncio.Queue()
        self.recv_queue = asyncio.Queue()
        super().__init__(comm_id=comm_id, target_name=target_name, data=data, metadata=metadata)
        self.receive_task = asyncio.create_task(self.receive())

    def publish_msg(self, msg_type, data, metadata, buffers, target_name=None, target_module=None):
        self.send_queue.put_nowait((msg_type, data, metadata, buffers, target_name, target_module))

    def handle_msg(self, msg):
        self._msg_callback(msg)

    async def receive(self):
        while True:
            msg = await self.recv_queue.get()
            self.handle_msg(msg)


comm.create_comm = MockComm


@pytest.fixture
def widget_factories():
    return Widget, Widget


@pytest.fixture
async def synced_widgets(widget_factories):
    local_widget = widget_factories[0]("my_widget")
    remote_widget_manager = RemoteWidgetManager(widget_factories[1], local_widget._comm)
    remote_widget = await remote_widget_manager.get_widget()
    return local_widget, remote_widget


class RemoteWidgetManager:

    comm: Optional[MockComm]
    widget: Optional[Widget]

    def __init__(self, widget_factory, comm):
        self.widget_factory = widget_factory
        self.comm = comm
        self.widget = None
        self.receive_task = asyncio.create_task(self.receive())

    def send(self, event: Y.AfterTransactionEvent):
        update = event.get_update()
        message = create_update_message(update)
        self.comm.recv_queue.put_nowait({"buffers": [message]})

    async def receive(self):
        while True:
            msg_type, data, metadata, buffers, target_name, target_module = await self.comm.send_queue.get()
            if msg_type == "comm_open":
                self.widget = self.widget_factory(target_name, primary=False)
                msg = sync(self.widget._ydoc)
                self.comm.handle_msg(msg)
            elif msg_type == "comm_msg":
                message = buffers[0]
                if message[0] == YMessageType.SYNC:
                    reply = process_sync_message(message[1:], self.widget._ydoc)
                    if reply:
                        self.comm.handle_msg({"buffers": [reply]})
                    if message[1] == YSyncMessageType.SYNC_STEP2:
                        self.widget._ydoc.observe_after_transaction(self.send)

    async def get_widget(self, timeout=0.1):
        t = time.monotonic()
        while True:
            if self.widget:
                return self.widget
            await asyncio.sleep(0)
            if time.monotonic() - t > timeout:
                raise TimeoutError("Timeout waiting for widget")
