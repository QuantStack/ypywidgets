import y_py as Y
from ypywidgets import Widget


def test_comm(mock_comm):
    ydoc2 = Y.YDoc()
    widget = Widget("my_widget", True, comm_data={"remote_ydoc": ydoc2})
    ydoc1 = widget.ydoc
    ytext1 = ydoc1.get_text("text")
    text = "hello world!"
    with ydoc1.begin_transaction() as txn:
        ytext1.extend(txn, text)
    ytext2 = ydoc2.get_text("text")
    assert str(ytext1) == str(ytext2) == text
