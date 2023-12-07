from unittest.mock import Mock, patch, call
import json
import plugins.take as take_module


def test_help():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    assert take.help() == {"take": "Take money from other user(s)"}


def test_input_not_take():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    assert take.input("not_take") is None


def test_input_take():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    assert take.input("take") == True
    master_mock.donext.assert_called_with(take, "who")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "User to take from?"),
            call(True, "buttons", json.dumps({"special": "accounts"})),
        ]
    )


def test_who_valid_user():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    master_mock.accounts.accounts = {"user1": {}}
    assert take.who("user1") == True
    assert "user1" in take.totakefrom
    master_mock.donext.assert_called_with(take, "who")


def test_who_abort():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    master_mock.accounts.accounts = {"user1": {}}
    assert take.who("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_who_amount():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    master_mock.accounts.accounts = {"user1": {}}
    take.totakefrom = ["user1"]
    assert take.who("50") == True
    assert take.value == 50
    master_mock.donext.assert_called_with(take, "reason")


def test_who_invalid_amount():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    master_mock.accounts.accounts = {"user1": {}}
    take.totakefrom = ["user1"]
    assert take.who("1000") == True
    master_mock.donext.assert_called_with(take, "who")


def test_who_unknown_user():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    master_mock.accounts.accounts = {"user1": {}}
    assert take.who("unknown_user") == True
    master_mock.donext.assert_called_with(take, "who")


def test_reason_abort():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    assert take.reason("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_reason_valid():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    take.totakefrom = ["user1", "user2"]
    take.peruser = 50
    assert take.reason("some reason") == True
    assert take.myreason == "some reason"
    master_mock.receipt.add.assert_called()


def test_startup():
    master_mock = Mock()
    take = take_module.take("SID", master_mock)
    take.startup()
    # No assertion needed, just checking if method exists and runs without error
