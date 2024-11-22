import json
from unittest.mock import Mock, patch, call
import kassa


def test_session_startup():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    mock_plugin = Mock()
    mock_plugin.help.return_value = {"command": "description"}
    with patch(
        "glob.glob",
        return_value=[
            "plugins/plugin1.py",
            "plugins/plugin2.py",
            "plugins/receipt.py",
            "plugins/accounts.py",
            "plugins/products.py",
            "plugins/stock.py",
            "plugins/log.py",
            "plugins/POS.py",
        ],
    ), patch("builtins.__import__", return_value=mock_plugin), patch(
        "kassa.Session.send_message"
    ) as mock_send_message:
        session.startup()

        # Assertions to ensure plugins are loaded and startup messages are sent
        assert "plugin1" in session.plugins
        assert "plugin2" in session.plugins
        mock_send_message.assert_called()


def test_on_connect():
    client_mock = Mock()
    kassa.on_connect(client_mock, None, None, 0)

    client_mock.subscribe.assert_called_with("hack42bar/input/#")


def test_on_message():
    client_mock = Mock()
    msg_mock = Mock()
    msg_mock.topic = "hack42bar/input/session/1234/input"
    msg_mock.payload = b"some data"

    with patch("kassa.get_session", return_value=Mock()) as mock_get_session:
        kassa.on_message(client_mock, None, msg_mock)

        mock_get_session.assert_called_with("1234", client_mock)
        mock_get_session.return_value.input.assert_called_with("some data")


def test_realcallhook():
    session = kassa.Session("SID", Mock())
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}

    session.realcallhook("test_hook", "test_arg")

    plugin_mock.hook_test_hook.assert_called_with("test_arg")


def test_callhook():
    session = kassa.Session("SID", Mock())

    with patch.object(session, "realcallhook") as mock_realcallhook:
        session.callhook("test_hook", "test_arg")

        expected_calls = [
            call("pre_test_hook", "test_arg"),
            call("test_hook", "test_arg"),
            call("post_test_hook", "test_arg"),
        ]
        mock_realcallhook.assert_has_calls(expected_calls)


def test_donext():
    session = kassa.Session("SID", Mock())
    plugin_mock = Mock()

    session.donext(plugin_mock, "test_function")

    assert session.nextcall == {"plug": plugin_mock, "function": "test_function"}


def test_send_message():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    session.send_message(True, "test_topic", "test_message")

    client_mock.publish.assert_called_with(
        "hack42bar/output/session/SID/test_topic", "test_message", 1, True
    )


def test_input_empty_string():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    session.input("")

    client_mock.publish.assert_has_calls(
        [
            call(
                "hack42bar/output/session/SID/message",
                "Enter product, command or username",
                1,
                True,
            ),
            call("hack42bar/output/session/SID/buttons", json.dumps({}), 1, True),
        ]
    )


def test_input_with_nextcall():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}
    session.nextcall = {"plug": plugin_mock, "function": "test_function"}

    test_function_mock = Mock(return_value=True)
    setattr(plugin_mock, "test_function", test_function_mock)

    session.input("test_input")

    test_function_mock.assert_called_with("test_input")
    assert session.nextcall == {}


def test_input_split_text():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock, "withdraw": Mock()}

    plugin_mock.input.return_value = False

    session.input("part1 part2")

    plugin_mock.input.assert_has_calls([call("part1"), call("part2")])


def test_input_unknown_command():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock, "withdraw": Mock()}

    plugin_mock.input.return_value = False

    session.input("unknown_command")

    client_mock.publish.assert_has_calls(
        [
            call(
                "hack42bar/output/session/SID/message",
                "Enter product, command or username",
                1,
                True,
            ),
            call("hack42bar/output/session/SID/buttons", "{}", 1, True),
        ]
    )


def test_input_plugin_processing():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}

    plugin_mock.input.return_value = True

    session.input("valid_command")

    plugin_mock.input.assert_called_with("valid_command")


def test_input_attribute_error_handling():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}

    # Remove the pre_input method to raise an AttributeError
    del plugin_mock.pre_input

    # No exception should be raised when calling input
    try:
        session.input("test_input")
        assert True  # Pass the test if no exception is raised
    except AttributeError:
        assert False  # Fail the test if AttributeError is raised


def test_input_generic_exception_handling():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}

    # Setup the plugin to raise an exception
    plugin_mock.pre_input.side_effect = Exception("Test exception")

    # No exception should be propagated when calling input
    try:
        session.input("test_input")
        assert True  # Pass the test if no exception is raised
    except Exception:
        assert False  # Fail the test if any exception is propagated


def test_input_with_nextcall_successful():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()

    # Setting up nextcall with a function that returns True
    session.nextcall = {"plug": plugin_mock, "function": "test_function"}
    plugin_mock.test_function.return_value = True

    session.input("test_input")

    # Asserting nextcall is processed and cleared
    plugin_mock.test_function.assert_called_with("test_input")
    assert session.nextcall == {}
