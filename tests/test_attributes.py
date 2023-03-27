import asyncio

import pytest

from .utils import agetattr


@pytest.mark.asyncio
async def test_dynamic_attributes(synced_widgets):
    local_widget, remote_widget = await synced_widgets

    local_widget.foo = "foo1"
    assert await agetattr(remote_widget, "foo") == "foo1"

    local_widget.bar = "bar2"
    assert await agetattr(remote_widget, "bar") == "bar2"

    remote_widget.baz = "baz3"
    assert await agetattr(local_widget, "baz") == "baz3"


@pytest.mark.asyncio
async def test_ydoc_creation(synced_widgets):
    local_widget, remote_widget = await synced_widgets

    local_text = local_widget._ydoc.get_text("text")
    text = "hello world!"
    with local_widget._ydoc.begin_transaction() as t:
        local_text.extend(t, text)

    remote_text = remote_widget._ydoc.get_text("text")
    await asyncio.sleep(0.01)
    assert str(remote_text) == text
