from unittest.mock import Mock, patch, call, mock_open
import plugins.undo as undo_module
import pickle
import json

def test_undo_help():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    expected_help = {
        "undo": "Undo last transaction",
        "undolist": "Undo a transaction",
        "restore": "Restore a transaction",
    }
    assert undo.help() == expected_help

def test_undo_hook_checkout():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    master_mock.receipt = Mock(totals={}, receipt=[])

    with patch.object(undo, 'loadundo'), patch.object(undo, 'writeundo'):
        undo.hook_checkout("text")
        undo.writeundo.assert_called()
        assert undo.undo[master_mock.transID] == {
            "totals": master_mock.receipt.totals,
            "receipt": master_mock.receipt.receipt,
            "beni": "text",
        }

def test_undo_hook_undo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {}, "receipt": [], "beni": "text"}}
    
    with patch.object(undo, 'loadundo'), patch.object(undo, 'writeundo'), \
         patch.object(undo.master, 'callhook'):
        undo.hook_undo((123, {}, [], "text"))
        assert 123 not in undo.undo
        undo.master.callhook.assert_has_calls([
            call("checkout", "text"),
            call("endsession", "text")
        ])

def test_undo_writeundo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {i: "data" for i in range(60)}

    with patch('builtins.open', mock_open()) as mock_file:
        undo.writeundo()
        assert len(undo.undo) == 50
        mock_file.assert_called_with("data/revbank.UNDO", "wb")
        mock_file().write.assert_called()
def test_undo_loadundo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    mock_data = pickle.dumps({1: "data"})

    with patch('builtins.open', mock_open(read_data=mock_data)):
        undo.loadundo()
        assert undo.undo == {1: "data"}


def test_undo_doundo_abort():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    assert undo.doundo("abort") == True
    master_mock.callhook.assert_called_with("abort", None)

def test_undo_doundo_valid_transID():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {}, "receipt": [], "beni": "text"}}
    
    with patch.object(undo.master, 'callhook'):
        assert undo.doundo("123") == True
        undo.master.callhook.assert_called()

def test_undo_doundo_invalid_transID():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {}

    with patch.object(undo, 'listundo'):
        assert undo.doundo("999") == True
        undo.listundo.assert_called()

def test_undo_listundo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {"user": 10}, "receipt": [], "beni": "text"}}

    undo.listundo()
    calls = [
        call(
            True,
            "buttons",
            json.dumps({"special": "custom", "custom": [{"text": 123, "display": "user \u20ac10.00 2011-03-13 08:08:43"}], "sort": "text"})
        ),
        call(
            True,
            "message",
            "Select a transaction to undo"
        )
    ]
    master_mock.send_message.assert_has_calls(calls, any_order=True)

def test_undo_input():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, 'listundo'):
        assert undo.input("undolist") == True
        undo.listundo.assert_called_with(0)

        assert undo.input("restore") == True
        undo.listundo.assert_called_with(1)

        assert undo.input("undo") == True

def test_undo_hook_abort():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, 'loadundo'):
        undo.hook_abort(None)
        undo.loadundo.assert_called()

def test_undo_startup():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, 'loadundo'):
        undo.startup()
        undo.loadundo.assert_called()

