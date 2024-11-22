import json

from unittest.mock import Mock, call
from unittest.mock import patch, mock_open

from plugins.accounts import accounts


def test_help():
    acc = accounts("main", Mock())
    assert acc.help() == {"adduseralias": "Add user key alias"}


def test_init():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    assert acc.SID == "SID"
    assert acc.master == master_mock
    assert acc.accounts == {}
    assert acc.members == []


@patch("time.strftime")
def test_updateaccount(mock_strftime):
    mock_strftime.return_value = "2021-01-01_12:00:00"
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"user1": {"amount": 100.0, "lastupdate": "2020-12-31_12:00:00"}}
    acc.updateaccount("user1", 50.0)
    assert acc.accounts["user1"]["amount"] == 150.0
    assert acc.accounts["user1"]["lastupdate"] == "2021-01-01_12:00:00"
    master_mock.callhook.assert_called_with(
        "balance", ("user1", 100.0, 150.0, master_mock.transID)
    )


def test_readaccounts():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    # Correctly formatted mock data
    mock_accounts_data = "user1 100.0 2021-01-01\nuser2 200.0 2021-01-02"
    mock_aliases_data = "alias1 user1\nalias2 user2"

    def custom_mock_open(filename, _bla, _bla2):
        if filename == "data/revbank.accounts":
            return mock_open(read_data=mock_accounts_data)()
        elif filename == "data/revbank.aliases":
            return mock_open(read_data=mock_aliases_data)()
        else:
            return mock_open()()  # Default mock

    with patch(
        "plugins.accounts.codecs.open", side_effect=custom_mock_open
    ) as mock_file:
        acc.readaccounts()

        # Assertions for accounts file
        assert acc.accounts["user1"] == {"amount": 100.0, "lastupdate": "2021-01-01"}
        assert acc.accounts["user2"] == {"amount": 200.0, "lastupdate": "2021-01-02"}

        # Assertions for aliases file
        assert acc.aliases["alias1"] == "user1"
        assert acc.aliases["alias2"] == "user2"


def test_writeaccount():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    # Setup initial data
    acc.accounts = {
        "user1": {"amount": 100.0, "lastupdate": "2021-01-01"},
        "user2": {"amount": 200.0, "lastupdate": "2021-01-02"},
    }
    acc.aliases = {"alias1": "user1", "alias2": "user2"}

    # Mock file handles
    mock_file_handles = {
        "data/revbank.accounts": mock_open(),
        "data/revbank.aliases": mock_open(),
    }

    # Custom side effect function for mock_open
    def custom_open_mock(file_name, *args, **kwargs):
        return mock_file_handles[file_name]()

    with patch("builtins.open", side_effect=custom_open_mock):
        acc.writeaccount()

        # Assertions for accounts file write
        accounts_file_handle = mock_file_handles["data/revbank.accounts"]
        accounts_file_handle().write.assert_has_calls(
            [
                call("user1              +100.00 2021-01-01\n"),
                call("user2              +200.00 2021-01-02\n"),
            ]
        )

        # Assertions for aliases file write
        aliases_file_handle = mock_file_handles["data/revbank.aliases"]
        aliases_file_handle().write.assert_has_calls(
            [call("alias1 user1\n"), call("alias2 user2\n")]
        )


def test_hook_balance():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"user1": {"amount": 100.0, "lastupdate": "2021-01-01"}}
    args = ("user1", 90.0, 100.0, 123456)

    acc.hook_balance(args)

    expected_calls = [
        call(
            False,
            "infobox/account/user1",
            json.dumps({"amount": 100.0, "lastupdate": "2021-01-01"}),
        ),
        call(
            True,
            "accounts/user1",
            json.dumps({"amount": 100.0, "lastupdate": "2021-01-01"}),
        ),
    ]
    master_mock.send_message.assert_has_calls(expected_calls, any_order=True)


@patch("plugins.accounts.accounts.writeaccount")
def test_hook_endsession(mock_writeaccount):
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    acc.hook_endsession("some text")

    mock_writeaccount.assert_called_once()


@patch("plugins.accounts.accounts.readaccounts")
def test_hook_abort(mock_readaccounts):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"user1": {"amount": 100.0, "lastupdate": "2021-01-01"}}

    acc.hook_abort(None)

    mock_readaccounts.assert_called_once()
    expected_calls = [
        call(True, "nonmembers", '["user1"]'),
        call(True, "accounts/user1", '{"amount": 100.0, "lastupdate": "2021-01-01"}'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


@patch("time.time")
@patch("plugins.accounts.accounts.readaccounts")
def test_hook_pre_checkout(mock_readaccounts, mock_time):
    mock_time.return_value = 1300000100.0
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    acc.hook_pre_checkout("some text")

    mock_readaccounts.assert_called_once()
    assert acc.master.transID == 100


@patch("plugins.accounts.accounts.updateaccount")
def test_hook_post_checkout(mock_updateaccount):
    master_mock = Mock()
    master_mock.receipt.totals = {"user1": 50.0}
    acc = accounts("SID", master_mock)

    acc.hook_post_checkout("some text")

    mock_updateaccount.assert_called_once_with("user1", 50.0)
    expected_calls = [
        call(True, "buttons", '{"special": "infobox"}'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


def test_createnew():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.newaccount = "new_user"

    # Test with 'yes'
    assert acc.createnew("yes") == True
    assert "new_user" in acc.accounts
    assert acc.accounts["new_user"] == {"amount": 0, "lastupdate": 0}
    acc.accounts["new_user"]["lastupdate"] = "1970-01-01"

    # Test with 'no'
    assert acc.createnew("no") == True

    # Test with 'abort'
    acc.createnew("abort")
    master_mock.callhook.assert_called_with("abort", None)

    # Test with invalid input
    acc.createnew("invalid")
    expected_calls = [
        call(False, "infobox/account", '{"amount": 0, "lastupdate": 0}'),
        call(True, "buttons", '{"special": "infobox"}'),
        call(
            True,
            "message",
            "Invalid answer; Account new_user does not exist do you want to create?",
        ),
        call(
            True,
            "buttons",
            '{"special": "custom", "custom": [{"text": "yes", "display": "Yes"}, {"text": "no", "display": "No"}]}',
        ),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


@patch("builtins.open", new_callable=mock_open, read_data="user1\nuser2\n")
def test_startup(mock_file):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    mock_accounts_data = "user1 100.0 2021-01-01\nuser2 200.0 2021-01-02"
    mock_aliases_data = "alias1 user1\nalias2 user2"

    def custom_mock_open(filename, _bla, _bla2):
        if filename == "data/revbank.accounts":
            return mock_open(read_data=mock_accounts_data)()
        elif filename == "data/revbank.aliases":
            return mock_open(read_data=mock_aliases_data)()
        else:
            return mock_open()()  # Default mock

    with patch(
        "plugins.accounts.codecs.open", side_effect=custom_mock_open
    ) as mock_file:
        acc.startup()

    assert acc.members == ["user1", "user2"]
    expected_calls = [
        call(True, "nonmembers", '["user2", "user1", "new_user"]'),
        call(True, "accounts/user1", '{"amount": 100.0, "lastupdate": "2021-01-01"}'),
        call(True, "accounts/user2", '{"amount": 200.0, "lastupdate": "2021-01-02"}'),
        call(True, "accounts/new_user", '{"amount": 0, "lastupdate": "1970-01-01"}'),
        call(True, "members", '["user1", "user2"]'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


def test_messageandbuttons():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    acc.messageandbuttons("next_function", "custom_buttons", "Test message")

    master_mock.donext.assert_called_with(acc, "next_function")
    expected_calls = [
        call(True, "message", "Test message"),
        call(True, "buttons", '{"special": "custom_buttons"}'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


@patch("builtins.open")
def test_addalias(_open):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.adduseralias = "user_alias"

    # Test with 'abort'
    acc.addalias("abort")
    master_mock.callhook.assert_called_with("abort", None)

    # Test with valid alias
    acc.accounts = {"user1": {"amount": 0, "lastupdate": "now"}}
    acc.aliases = {}
    acc.addalias("new_alias")
    assert "new_alias" in acc.aliases
    assert acc.aliases["new_alias"] == "user_alias"


@patch("builtins.open")
def test_askalias(_open):
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    # Test with existing account
    acc.accounts = {"existing_user": {}}
    acc.askalias("existing_user")
    expected_calls = [
        call(True, "message", "What alias to add?"),
        call(True, "buttons", '{"special": "keyboard"}'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls

    # Test with 'abort'
    acc.askalias("abort")
    master_mock.callhook.assert_called_with("abort", None)


def test_input_existing_account():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"user1": {}}
    acc.aliases = {}

    # Test with existing account
    acc.input("user1")
    expected_calls = [
        call(False, "infobox/account", "{}"),
        call(True, "buttons", '{"special": "infobox"}'),
    ]
    assert master_mock.send_message.call_args_list == expected_calls


def test_newuser():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.master.receipt.receipt = [{"value": 10, "Lose": False}]

    acc.newuser("new_user")

    expected_calls = [
        call(True, "message", "Account new_user does not exist do you want to create?"),
        call(
            True,
            "buttons",
            '{"special": "custom", "custom": [{"text": "yes", "display": "Yes"}, {"text": "no", "display": "No"}]}',
        ),
    ]
    assert master_mock.send_message.call_args_list == expected_calls
