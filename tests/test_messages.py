import asyncio

import pytest


@pytest.mark.asyncio
async def test_messages(synced_widgets):
    local_messages = []
    remote_messages = []
    local_widget, remote_widget = synced_widgets

    def on_local_message(message):
        local_messages.append(message)

    def on_remote_message(message):
        remote_messages.append(message)
        remote_widget.send(message + b", World!")

    local_widget.on_receive(on_local_message)
    remote_widget.on_receive(on_remote_message)

    local_widget.send(b"Hello")
    await asyncio.sleep(0.1)
    assert remote_messages == [b"Hello"]
    assert local_messages == [b"Hello, World!"]

    remote_widget.send(b"msg")
    await asyncio.sleep(0.1)
    assert remote_messages == [b"Hello"]
    assert local_messages == [b"Hello, World!", b"msg"]
