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


def test_updateaccount_ignores_cash():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    assert acc.updateaccount("cash", 50.0) is None

    master_mock.callhook.assert_not_called()


def test_readaccounts():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"stale_user": {"amount": 1.0, "lastupdate": "old"}}
    acc.aliases = {"stale_alias": "stale_user"}

    # Correctly formatted mock data
    mock_accounts_data = "user1 100.0 2021-01-01\nuser2 200.0 2021-01-02"
    mock_aliases_data = "alias1 user1\nalias2 user2"

    def custom_mock_open(filename, _bla, _bla2):
        if filename == "data/revbank.accounts":
            return mock_open(read_data=mock_accounts_data)()
        if filename == "data/revbank.aliases":
            return mock_open(read_data=mock_aliases_data)()

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
        assert "stale_user" not in acc.accounts
        assert "stale_alias" not in acc.aliases


def test_readaccounts_tolerates_comments_blanks_and_whitespace():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    mock_accounts_data = (
        "# comment\n"
        "\n"
        "user1     +100.00   2021-01-01\n"
        "malformed\n"
        "user2\t-20.50\t2021-01-02 extra-field\n"
    )
    mock_aliases_data = (
        "# comment\n"
        "\n"
        "alias1     user1\n"
        "bad alias line\n"
        "alias2\tuser2\n"
    )

    def custom_mock_open(filename, _bla, _bla2):
        if filename == "data/revbank.accounts":
            return mock_open(read_data=mock_accounts_data)()
        if filename == "data/revbank.aliases":
            return mock_open(read_data=mock_aliases_data)()

    with patch("plugins.accounts.codecs.open", side_effect=custom_mock_open):
        acc.readaccounts()

    assert acc.accounts == {
        "user1": {"amount": 100.0, "lastupdate": "2021-01-01"},
        "user2": {"amount": -20.5, "lastupdate": "2021-01-02"},
    }
    assert acc.aliases == {"alias1": "user1", "alias2": "user2"}


def test_writeaccount():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    # Setup initial data
    acc.accounts = {
        "user1": {"amount": 100.0, "lastupdate": "2021-01-01"},
        "user2": {"amount": 200.0, "lastupdate": "2021-01-02"},
    }
    acc.aliases = {"alias1": "user1", "alias2": "user2"}

    with patch("plugins.accounts._atomic_write") as mock_atomic_write:
        acc.writeaccount()

    mock_atomic_write.assert_has_calls(
        [
            call(
                "data/revbank.accounts",
                [
                    "user1              +100.00 2021-01-01\n",
                    "user2              +200.00 2021-01-02\n",
                ],
            ),
            call(
                "data/revbank.aliases",
                ["alias1 user1\n", "alias2 user2\n"],
            ),
        ]
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
    acc.accounts = {"user1": {"amount": 12.5, "lastupdate": "old"}}

    acc.hook_pre_checkout("some text")

    mock_readaccounts.assert_called_once()
    assert acc.master.transID == 100
    assert acc.checkout_balances == {"user1": 12.5}


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


@patch("time.strftime", return_value="2021-01-01_12:00:00")
def test_createnew(_mock_strftime):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.newaccount = "new_user"

    # Test with 'yes'
    assert acc.createnew("yes") == True
    assert "new_user" in acc.accounts
    assert acc.accounts["new_user"] == {
        "amount": 0,
        "lastupdate": "2021-01-01_12:00:00",
    }

    # Test with 'no'
    assert acc.createnew("no") == True

    # Test with 'abort'
    acc.createnew("abort")
    master_mock.callhook.assert_called_with("abort", None)

    # Test with invalid input
    acc.createnew("invalid")
    expected_calls = [
        call(
            False,
            "infobox/account",
            '{"amount": 0, "lastupdate": "2021-01-01_12:00:00"}',
        ),
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


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="# comment\n\nuser1\n  user2  \n",
)
def test_startup(mock_file):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    mock_accounts_data = "user1 100.0 2021-01-01\nuser2 200.0 2021-01-02"
    mock_aliases_data = "alias1 user1\nalias2 user2"

    def custom_mock_open(filename, _bla, _bla2):
        if filename == "data/revbank.accounts":
            return mock_open(read_data=mock_accounts_data)()
        if filename == "data/revbank.aliases":
            return mock_open(read_data=mock_aliases_data)()

    with patch(
        "plugins.accounts.codecs.open", side_effect=custom_mock_open
    ) as mock_file:
        acc.startup()

    assert acc.members == ["user1", "user2"]
    expected_calls = [
        call(True, "nonmembers", "[]"),
        call(True, "accounts/user1", '{"amount": 100.0, "lastupdate": "2021-01-01"}'),
        call(True, "accounts/user2", '{"amount": 200.0, "lastupdate": "2021-01-02"}'),
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
def test_addalias_invalid_existing_or_short(_open):
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.adduseralias = "user1"
    acc.accounts = {"user1": {"amount": 0, "lastupdate": "now"}}
    acc.aliases = {"existing_alias": "user1"}

    assert acc.addalias("usr") is None
    assert acc.addalias("user1") is None
    assert acc.addalias("existing_alias") is None


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


def test_askalias_unknown_user():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {}

    assert acc.askalias("missing") is None


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


def test_input_alias_empty_receipt_and_checkout_paths():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.accounts = {"user1": {"amount": 12.0}}
    acc.aliases = {"alias1": "user1"}

    master_mock.receipt.is_empty.return_value = True
    assert acc.input("alias1") is True
    master_mock.send_message.assert_has_calls(
        [
            call(False, "infobox/account", '{"amount": 12.0}'),
            call(True, "buttons", '{"special": "infobox"}'),
        ]
    )

    master_mock.reset_mock()
    master_mock.receipt.is_empty.return_value = False
    assert acc.input("alias1") is True
    master_mock.callhook.assert_has_calls(
        [call("checkout", "user1"), call("endsession", "user1")]
    )


def test_input_adduseralias_and_unknown():
    master_mock = Mock()
    acc = accounts("SID", master_mock)

    assert acc.input("adduseralias") is True
    master_mock.donext.assert_called_with(acc, "askalias")
    assert acc.input("missing") is None


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


def test_newuser_no_positive_gain():
    master_mock = Mock()
    acc = accounts("SID", master_mock)
    acc.master.receipt.receipt = [
        {"value": -1, "Lose": False},
        {"value": 10, "Lose": True},
    ]

    assert acc.newuser("new_user") is None
