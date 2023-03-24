import comm
import pytest
import y_py as Y
from ypywidgets.yutils import YMessageType, YSyncMessageType, create_update_message, process_sync_message


class MockComm(comm.base_comm.BaseComm):

    def publish_msg(self, msg_type, data=None, metadata=None, buffers=None, **keys):
        if msg_type == "comm_open":
            self.remote_ydoc = data["remote_ydoc"]
        elif msg_type == "comm_msg":
            message = buffers[0]
            if message[0] == YMessageType.SYNC:
                process_sync_message(message[1:], self.remote_ydoc, self.send_back)
                if message[1] == YSyncMessageType.SYNC_STEP2:
                    self.remote_ydoc.observe_after_transaction(self.receive)

    def send_back(self, buffers):
        self.handle_msg({"buffers": buffers})

    def handle_msg(self, msg):
        self._msg_callback(msg)

    def receive(self, event: Y.AfterTransactionEvent):
        update = event.get_update()
        message = create_update_message(update)
        self.handle_msg({"buffers": [message]})


@pytest.fixture
def mock_comm():
    comm.create_comm = MockComm
