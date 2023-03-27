import pytest

from .utils import agetattr


@pytest.mark.asyncio
async def test_attribute_sync(synced_widgets):
    local_widget, remote_widget = await synced_widgets

    local_widget.foo = "foo1"
    assert await agetattr(remote_widget, "foo") == "foo1"

    local_widget.bar = "bar2"
    assert await agetattr(remote_widget, "bar") == "bar2"

    remote_widget.baz = "baz3"
    assert await agetattr(local_widget, "baz") == "baz3"
