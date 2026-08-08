from __future__ import annotations

import pytest
from pycrdt import Awareness, Doc, YMessageType, create_awareness_message

from ypywidgets.comm import CommWidget

pytestmark = pytest.mark.anyio


async def test_comm_provider_applies_awareness_message(synced_widgets, context):
    async with context:
        local_widget = await synced_widgets.get_local_widget()
        remote_awareness = Awareness(Doc())
        remote_awareness.set_local_state({"role": "remote"})
        payload = remote_awareness.encode_awareness_update([remote_awareness.client_id])
        message = create_awareness_message(payload)

        assert message[0] == YMessageType.AWARENESS

        local_widget._comm_provider._receive({"buffers": [message]})

        remote_state = local_widget.awareness.states.get(remote_awareness.client_id)
        assert remote_state is not None
        assert remote_state.get("role") == "remote"


async def test_comm_widget_exposes_provider_awareness():
    widget = CommWidget()
    assert widget.awareness is widget._comm_provider.awareness


async def test_comm_widget_awareness_observe_and_unobserve() -> None:
    widget = CommWidget()

    events: list[str] = []
    sub_id = widget.awareness.observe(lambda topic, _: events.append(topic))

    widget.awareness.set_local_state({"ping": 1})
    assert events

    widget.awareness.unobserve(sub_id)
    events.clear()
    widget.awareness.set_local_state({"ping": 2})
    assert events == []


async def test_comm_provider_sends_awareness_to_frontend(synced_widgets, context):
    async with context:
        local_widget = await synced_widgets.get_local_widget()

        sent_messages = []
        local_widget._comm_provider._comm.send = lambda buffers: sent_messages.append(
            buffers[0]
        )

        local_widget.awareness.set_local_state({"role": "python-test"})

        assert any(msg[0] == YMessageType.AWARENESS for msg in sent_messages)
