from __future__ import annotations

import asyncio
import time

import comm
import pytest
import pytest_asyncio
from pycrdt import create_sync_message
from ypywidgets.comm import CommWidget


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
    return CommWidget, CommWidget


@pytest_asyncio.fixture
async def synced_widgets(widget_factories):
    local_widget = widget_factories[0]()
    remote_widget_manager = RemoteWidgetManager(widget_factories[1], local_widget._comm)
    remote_widget = await remote_widget_manager.get_widget()
    return local_widget, remote_widget


class RemoteWidgetManager:

    comm: MockComm
    widget: CommWidget | None

    def __init__(self, widget_factory, local_comm):
        self.widget_factory = widget_factory
        self.local_comm = local_comm
        self.widget = None
        self.receive_task = asyncio.create_task(self.receive())

    async def send(self):
        while True:
            msg_type, data, metadata, buffers, target_name, target_module = await self.widget._comm.send_queue.get()
            if msg_type == "comm_msg":
                self.local_comm.recv_queue.put_nowait({"buffers": buffers})

    async def receive(self):
        while True:
            msg_type, data, metadata, buffers, target_name, target_module = await self.local_comm.send_queue.get()
            if msg_type == "comm_open":
                self.widget = self.widget_factory()
                msg = create_sync_message(self.widget.ydoc)
                self.local_comm.recv_queue.put_nowait({"buffers": [msg]})
                self.send_task = asyncio.create_task(self.send())
            elif msg_type == "comm_msg":
                self.widget._comm.recv_queue.put_nowait({"buffers": buffers})

    async def get_widget(self, timeout=0.1):
        t = time.monotonic()
        while True:
            if self.widget:
                return self.widget
            await asyncio.sleep(0)
            if time.monotonic() - t > timeout:  # pragma: nocover
                raise TimeoutError("Timeout waiting for widget")
