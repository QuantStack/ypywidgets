from __future__ import annotations

from unittest.mock import patch

import pytest
from anyio import sleep
from pycrdt import Doc, Text, YMessageType, create_awareness_message

from ypywidgets.comm import CommProvider, CommWidget

pytestmark = pytest.mark.anyio


class DummyComm:
    def __init__(self):
        self.sent: list[bytes] = []
        self._handler = None

    def send(self, *, buffers=None, **kwargs):
        if buffers:
            self.sent.append(bytes(memoryview(buffers[0])))

    def on_msg(self, handler):
        self._handler = handler


def test_comm_provider_applies_awareness_frame():
    doc = Doc()
    comm = DummyComm()
    provider = CommProvider(doc, comm)

    awareness = provider.awareness
    awareness.set_local_state({"role": "tester"})
    payload = awareness.encode_awareness_update([awareness.client_id])
    frame = create_awareness_message(payload)

    assert frame[0] == YMessageType.AWARENESS

    provider._receive({"buffers": [frame]})

    state = awareness.get_local_state()
    assert state is not None
    assert state.get("role") == "tester"


@patch("ypywidgets.comm.create_widget_comm")
def test_comm_widget_exposes_provider_awareness(mock_create_comm):
    comm = DummyComm()
    mock_create_comm.return_value = comm

    widget = CommWidget()
    assert widget.awareness is widget._comm_provider.awareness


@patch("ypywidgets.comm.create_widget_comm")
def test_comm_widget_awareness_observe_and_unobserve(mock_create_comm):
    comm = DummyComm()
    mock_create_comm.return_value = comm
    widget = CommWidget()

    events: list[str] = []
    sub_id = widget.on_awareness_change(lambda topic, _: events.append(topic))

    widget.awareness.set_local_state({"ping": 1})
    assert events

    widget.unobserve_awareness(sub_id)
    events.clear()
    widget.awareness.set_local_state({"ping": 2})
    assert events == []