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

    with patch.object(undo, "loadundo"), patch.object(undo, "writeundo"):
        undo.hook_checkout("text")
        undo.writeundo.assert_called()
        assert undo.undo[master_mock.transID] == {
            "totals": master_mock.receipt.totals,
            "receipt": master_mock.receipt.receipt,
            "beni": "text",
        }


def test_undo_hook_checkout_stores_snapshot():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    master_mock.transID = 123
    master_mock.receipt = Mock(
        totals={"user": -2.5},
        receipt=[
            {
                "Lose": True,
                "value": 2.5,
                "description": "Product",
                "count": 1,
                "beni": "user",
                "product": "product1",
            }
        ],
    )

    with patch.object(undo, "loadundo"), patch.object(undo, "writeundo"):
        undo.hook_checkout("user")

    master_mock.receipt.totals["user"] = 0
    master_mock.receipt.receipt[0]["count"] = 99

    assert undo.undo[123]["totals"] == {"user": -2.5}
    assert undo.undo[123]["receipt"][0]["count"] == 1


def test_undo_hook_undo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {}, "receipt": [], "beni": "text"}}

    with patch.object(undo, "loadundo"), patch.object(undo, "writeundo"), patch.object(
        undo.master, "callhook"
    ):
        undo.hook_undo((123, {}, [], "text"))
        assert 123 not in undo.undo
        undo.master.callhook.assert_has_calls(
            [call("checkout", "text"), call("endsession", "text")]
        )


def test_undo_hook_undo_adds_positive_and_negative_totals():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {}, "receipt": [], "beni": "text"}}

    with patch.object(undo, "loadundo"), patch.object(undo, "writeundo"):
        undo.hook_undo((123, {"user1": 10, "user2": -5}, [], "text"))

    master_mock.receipt.add.assert_has_calls(
        [
            call(True, 10, "Undo 123", 1, "user1", "undo"),
            call(False, 5, "Undo 123", 1, "user2", "undo"),
        ]
    )


def test_undo_writeundo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {i: "data" for i in range(60)}

    with patch("builtins.open", mock_open()) as mock_file:
        undo.writeundo()
        assert len(undo.undo) == 50
        mock_file.assert_called_with("data/revbank.UNDO", "w", encoding="utf-8")
        mock_file().write.assert_called()
        written = "".join(call.args[0] for call in mock_file().write.call_args_list)
        loaded = json.loads(written)
        assert len(loaded) == 50


def test_undo_loadundo_pickle_backwards_compatible():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    mock_data = pickle.dumps({1: "data"})

    with patch("builtins.open", mock_open(read_data=mock_data)):
        undo.loadundo()
        assert undo.undo == {1: "data"}


def test_undo_loadundo_json():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    mock_data = json.dumps({"1": "data"}).encode("utf-8")

    with patch("builtins.open", mock_open(read_data=mock_data)):
        undo.loadundo()
        assert undo.undo == {1: "data"}


def test_undo_loadundo_ignores_errors():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {1: "old"}

    with patch("builtins.open", side_effect=OSError("missing")):
        undo.loadundo()

    assert undo.undo == {1: "old"}


def test_undo_doundo_abort():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    assert undo.doundo("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_undo_doundo_valid_transID():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {}, "receipt": [], "beni": "text"}}

    with patch.object(undo.master, "callhook"):
        assert undo.doundo("123") == True
        undo.master.callhook.assert_called()


def test_undo_doundo_invalid_transID():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {}

    with patch.object(undo, "listundo"):
        assert undo.doundo("999") == True
        undo.listundo.assert_called()


def test_undo_doundo_non_numeric_lists_undo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, "listundo"):
        assert undo.doundo("not-a-number") == True
        undo.listundo.assert_called()


def test_undo_dorestore_paths():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {
        123: {
            "totals": {"buyer": 10},
            "receipt": [
                {
                    "Lose": True,
                    "value": 2.5,
                    "description": "Product",
                    "count": 2,
                    "beni": "buyer",
                    "product": "product1",
                },
                {
                    "Lose": False,
                    "value": 1.0,
                    "description": "Other",
                    "count": 1,
                    "beni": "other",
                    "product": "other",
                },
            ],
            "beni": "buyer",
        }
    }

    assert undo.dorestore("abort")
    master_mock.callhook.assert_called_with("abort", None)

    master_mock.reset_mock()
    assert undo.dorestore("123")
    master_mock.callhook.assert_called_with(
        "undo",
        (
            123,
            undo.undo[123]["totals"],
            undo.undo[123]["receipt"],
            undo.undo[123]["beni"],
        ),
    )
    master_mock.receipt.add.assert_has_calls(
        [
            call(True, 2.5, "Product", 2, None, "product1"),
            call(False, 1.0, "Other", 1, "other", "other"),
        ]
    )

    with patch.object(undo, "listundo"):
        assert undo.dorestore("999")
        assert undo.dorestore("not-a-number")
        assert undo.listundo.call_count == 2


def test_undo_listundo():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {123: {"totals": {"user": 10}, "receipt": [], "beni": "text"}}
    expected_time = undo_module.time.strftime(
        "%Y-%m-%d %H:%M:%S", undo_module.time.localtime(123 + 1300000000)
    )

    undo.listundo()
    calls = [
        call(
            True,
            "buttons",
            json.dumps(
                {
                    "special": "custom",
                    "custom": [
                        {
                            "text": 123,
                            "display": f"user \u20ac10.00 {expected_time}",
                        }
                    ],
                    "sort": "text",
                }
            ),
        ),
        call(True, "message", "Select a transaction to undo"),
    ]
    master_mock.send_message.assert_has_calls(calls, any_order=True)


def test_undo_listundo_restore_and_limit():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)
    undo.undo = {
        i: {"totals": {"user": i}, "receipt": [], "beni": "text"} for i in range(60)
    }

    undo.listundo(restore=True)

    master_mock.send_message.assert_any_call(
        True, "message", "Select a transaction to restore"
    )
    master_mock.donext.assert_called_with(undo, "dorestore")
    buttons = json.loads(master_mock.send_message.call_args_list[0].args[2])
    assert len(buttons["custom"]) == 50


def test_undo_input():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, "listundo"):
        assert undo.input("undolist") == True
        undo.listundo.assert_called_with(0)

        assert undo.input("restore") == True
        undo.listundo.assert_called_with(1)

        assert undo.input("undo") == True

        assert undo.input("other") is None


def test_undo_hook_abort():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, "loadundo"):
        undo.hook_abort(None)
        undo.loadundo.assert_called()


def test_undo_startup():
    master_mock = Mock()
    undo = undo_module.undo("SID", master_mock)

    with patch.object(undo, "loadundo"):
        undo.startup()
        undo.loadundo.assert_called()
