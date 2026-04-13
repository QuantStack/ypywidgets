import math
from contextlib import AsyncExitStack
from functools import partial
from typing import Any, cast

import comm
import pytest
from anyio import Event, create_memory_object_stream, create_task_group, fail_after
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from pycrdt import (
    YMessageType,
    YSyncMessageType,
    TransactionEvent,
    create_sync_message,
    create_update_message,
    handle_sync_message,
)
from ypywidgets import Widget
from ypywidgets.comm import CommWidget

pytestmark = pytest.mark.anyio


class MockComm(comm.base_comm.BaseComm):
    def __init__(
        self,
        task_group: TaskGroup,
        send_send_stream: MemoryObjectSendStream,
        send_recv_stream: MemoryObjectReceiveStream,
        recv_send_stream: MemoryObjectSendStream,
        recv_recv_stream: MemoryObjectReceiveStream,
        comm_id: str = "",
        target_name: str = "",
        data=None,
        metadata=None,
    ) -> None:
        self.send_send_stream = send_send_stream
        self.send_recv_stream = send_recv_stream
        self.recv_send_stream = recv_send_stream
        self.recv_recv_stream = recv_recv_stream
        super().__init__(
            comm_id=comm_id, target_name=target_name, data=data, metadata=metadata
        )
        task_group.start_soon(self.receive)

    def publish_msg(
        self, msg_type, data, metadata, buffers, target_name=None, target_module=None
    ):
        self.send_send_stream.send_nowait(
            (msg_type, data, metadata, buffers, target_name, target_module)
        )

    def handle_msg(self, msg):
        self._msg_callback(msg)

    async def receive(self) -> None:
        while True:
            msg = await self.recv_recv_stream.receive()
            self.handle_msg(msg)


class Context:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    async def __aenter__(self) -> "Context":
        send_send_stream, send_recv_stream = create_memory_object_stream(
            max_buffer_size=math.inf
        )
        recv_send_stream, recv_recv_stream = create_memory_object_stream(
            max_buffer_size=math.inf
        )
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(send_send_stream)
            await stack.enter_async_context(recv_send_stream)
            await stack.enter_async_context(send_recv_stream)
            await stack.enter_async_context(recv_recv_stream)
            self.task_group = await stack.enter_async_context(create_task_group())
            comm.create_comm = partial(
                MockComm,
                self.task_group,
                send_send_stream,
                send_recv_stream,
                recv_send_stream,
                recv_recv_stream,
            )
            for task in self.tasks:
                self.task_group.start_soon(task)
            self.stack = stack.pop_all()
        return self

    async def __aexit__(self, *exc) -> bool | None:
        self.task_group.cancel_scope.cancel()
        comm.create_comm = _create_comm
        return await self.stack.__aexit__(*exc)


def _create_comm(*args: Any, **kwargs: Any) -> comm.BaseComm:
    return comm.DummyComm(*args, **kwargs)  # pragma: nocover


class SyncedWidgets:
    def __init__(
        self, widget_factories: tuple[type[CommWidget], type[Widget]], context: Context
    ) -> None:
        self.local_widget_factory, self.remote_widget_factory = widget_factories
        self.local_widget: CommWidget | None = None
        self.remote_widget: Widget | None = None
        self.local_widget_created = Event()
        self.remote_widget_created = Event()
        context.add_task(self.receive)

    def send(self, event: TransactionEvent) -> None:
        update = event.update
        message = create_update_message(update)
        self.comm.recv_send_stream.send_nowait({"buffers": [message]})

    async def receive(self) -> None:
        self.local_widget = self.local_widget_factory()
        self.local_widget_created.set()
        self.comm = cast(MockComm, self.local_widget._comm)
        while True:
            (
                msg_type,
                data,
                metadata,
                buffers,
                target_name,
                target_module,
            ) = await self.comm.send_recv_stream.receive()
            match msg_type:
                case "comm_open":
                    self.remote_widget = self.remote_widget_factory()
                    msg = create_sync_message(self.remote_widget.ydoc)
                    self.comm.handle_msg({"buffers": [msg]})
                case "comm_msg":
                    assert self.remote_widget is not None
                    message = buffers[0]
                    match message[0]:
                        case YMessageType.SYNC:
                            reply = handle_sync_message(
                                message[1:], self.remote_widget.ydoc
                            )
                            if reply is not None:
                                self.comm.handle_msg({"buffers": [reply]})
                            if message[1] == YSyncMessageType.SYNC_STEP2:
                                self.sub = self.remote_widget.ydoc.observe(self.send)
                                self.remote_widget_created.set()

    async def get_local_widget(self, timeout: float = 0.2) -> CommWidget:
        with fail_after(timeout):
            await self.local_widget_created.wait()
            assert self.local_widget is not None
            return self.local_widget

    async def get_remote_widget(self, timeout: float = 0.2) -> Widget:
        with fail_after(timeout):
            await self.remote_widget_created.wait()
            assert self.remote_widget is not None
            return self.remote_widget


@pytest.fixture
def context() -> Context:
    return Context()


@pytest.fixture
def widget_factories() -> tuple[type[CommWidget], type[Widget]]:
    return CommWidget, Widget


@pytest.fixture
def synced_widgets(
    widget_factories: tuple[type[CommWidget], type[Widget]], context: Context
) -> SyncedWidgets:
    return SyncedWidgets(widget_factories, context)
