from __future__ import annotations

import pytest
from anyio import sleep
from pycrdt import Awareness, Doc, YMessageType, create_awareness_message

pytestmark = pytest.mark.anyio


async def test_comm_provider_applies_awareness_frame(synced_widgets, context):
    async with context:
        local_widget = await synced_widgets.get_local_widget()
        remote_awareness = Awareness(Doc())
        remote_awareness.set_local_state({"role": "remote"})
        payload = remote_awareness.encode_awareness_update([remote_awareness.client_id])
        frame = create_awareness_message(payload)

        assert frame[0] == YMessageType.AWARENESS

        local_widget._comm_provider._receive({"buffers": [frame]})

        remote_state = local_widget.awareness.states.get(remote_awareness.client_id)
        assert remote_state is not None
        assert remote_state.get("role") == "remote"


async def test_comm_widget_exposes_provider_awareness(synced_widgets, context):
    async with context:
        widget = await synced_widgets.get_local_widget()
        assert widget.awareness is widget._comm_provider.awareness


async def test_comm_widget_awareness_observe_and_unobserve(synced_widgets, context):
    async with context:
        widget = await synced_widgets.get_local_widget()

        events: list[str] = []
        sub_id = widget.awareness.observe(lambda topic, _: events.append(topic))

        widget.awareness.set_local_state({"ping": 1})
        assert events

        widget.awareness.unobserve(sub_id)
        events.clear()
        widget.awareness.set_local_state({"ping": 2})
        assert events == []


async def test_remote_manager_applies_awareness_messages(synced_widgets, context):
    async with context:
        local_widget = await synced_widgets.get_local_widget()
        await synced_widgets.get_remote_widget()

        local_widget.awareness.set_local_state({"role": "local"})
        payload = local_widget.awareness.encode_awareness_update(
            [local_widget.awareness.client_id]
        )
        frame = create_awareness_message(payload)

        synced_widgets.comm.send_send_stream.send_nowait(
            ("comm_msg", {}, None, [frame], None, None)
        )
        await sleep(0.01)

        assert synced_widgets._remote_awareness is not None
        remote_state = synced_widgets._remote_awareness.states.get(
            local_widget.awareness.client_id
        )
        assert remote_state is not None
        assert remote_state.get("role") == "local"
