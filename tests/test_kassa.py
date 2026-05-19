import json
from pathlib import Path
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

    session.input("test_input")


def test_input_generic_exception_handling():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    session.plugins = {"test_plugin": plugin_mock}

    # Setup the plugin to raise an exception
    plugin_mock.pre_input.side_effect = Exception("Test exception")

    session.input("test_input")


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


def test_startup_handles_help_and_plugin_startup_errors():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    class GoodPlugin:
        def __init__(self, SID, master):
            self.SID = SID
            self.master = master

        def help(self):
            return {"good": "Good command"}

        def startup(self):
            return None

    class HelpErrorPlugin(GoodPlugin):
        def help(self):
            raise RuntimeError("help failed")

    class StartupErrorPlugin(GoodPlugin):
        def startup(self):
            raise RuntimeError("startup failed")

    plugin_classes = {
        "receipt": GoodPlugin,
        "accounts": GoodPlugin,
        "products": GoodPlugin,
        "stock": GoodPlugin,
        "log": GoodPlugin,
        "POS": GoodPlugin,
        "badhelp": HelpErrorPlugin,
        "badstartup": StartupErrorPlugin,
    }

    def import_from(_module, name):
        return plugin_classes[name]

    with patch(
        "glob.glob", return_value=[f"plugins/{name}.py" for name in plugin_classes]
    ):
        session.import_from = Mock(side_effect=import_from)
        session.startup()

    assert "badhelp" in session.plugins
    assert "badstartup" in session.plugins
    assert session.help == {"good": "Good command"}


def test_startup_removes_existing_plugin_module():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    sys_modules_name = "existing"

    with patch.dict(kassa.sys.modules, {sys_modules_name: Mock()}), patch(
        "glob.glob", return_value=[f"plugins/{sys_modules_name}.py"]
    ):
        with patch.object(session, "import_from", side_effect=KeyError("stop")):
            try:
                session.startup()
            except KeyError:
                pass

        assert sys_modules_name not in kassa.sys.modules


def test_realcallhook_handles_plugin_hook_exception():
    session = kassa.Session("SID", Mock())
    plugin_mock = Mock()
    plugin_mock.hook_test_hook.side_effect = RuntimeError("boom")
    session.plugins = {"test_plugin": plugin_mock}

    session.realcallhook("test_hook", "test_arg")

    plugin_mock.hook_test_hook.assert_called_with("test_arg")


def test_realcallhook_ignores_plugins_without_hook():
    session = kassa.Session("SID", Mock())
    session.plugins = {"plain": object()}

    session.realcallhook("missing", "arg")


def test_handle_nextcall_missing_and_exception():
    session = kassa.Session("SID", Mock())
    assert session.handle_nextcall("text") is False

    plugin_mock = Mock()
    plugin_mock.fail.side_effect = RuntimeError("boom")
    session.nextcall = {"plug": plugin_mock, "function": "fail"}

    assert session.handle_nextcall("text") is False
    assert session.nextcall == {}


def test_input_unknown_sets_message_and_calls_wrong_hook():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)
    plugin_mock = Mock()
    plugin_mock.input.return_value = False
    withdraw_mock = Mock()
    withdraw_mock.input.return_value = False
    withdraw_mock.withdraw.return_value = False
    accounts_mock = Mock()
    accounts_mock.input.return_value = False
    accounts_mock.newuser.return_value = False
    session.plugins = {
        "test_plugin": plugin_mock,
        "withdraw": withdraw_mock,
        "accounts": accounts_mock,
    }

    with patch.object(session, "callhook") as mock_callhook:
        session.input("unknown")

    mock_callhook.assert_called_with("wrong", ())
    client_mock.publish.assert_any_call(
        "hack42bar/output/session/SID/message",
        "Unknown product, command or username",
        1,
        True,
    )


def test_handle_part_plugin_attribute_and_generic_exceptions_then_withdraw():
    session = kassa.Session("SID", Mock())
    missing_input_plugin = Mock()
    del missing_input_plugin.input
    failing_plugin = Mock()
    failing_plugin.input.side_effect = RuntimeError("boom")
    withdraw_mock = Mock()
    withdraw_mock.input.return_value = False
    withdraw_mock.withdraw.return_value = True
    session.plugins = {
        "missing": missing_input_plugin,
        "failing": failing_plugin,
        "withdraw": withdraw_mock,
    }

    assert session.handle_part("10") == 1
    withdraw_mock.withdraw.assert_called_with("10")


def test_handle_part_falls_back_to_newuser():
    session = kassa.Session("SID", Mock())
    plugin_mock = Mock()
    plugin_mock.input.return_value = False
    withdraw_mock = Mock()
    withdraw_mock.input.return_value = False
    withdraw_mock.withdraw.return_value = False
    accounts_mock = Mock()
    accounts_mock.input.return_value = False
    accounts_mock.newuser.return_value = True
    session.plugins = {
        "plugin": plugin_mock,
        "withdraw": withdraw_mock,
        "accounts": accounts_mock,
    }

    assert session.handle_part("newuser") == 1
    accounts_mock.newuser.assert_called_with("newuser")


def test_send_message_updates_prompt_buttons_and_skips_cached_long_topic():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    session.send_message(True, "message", "hello")
    session.send_message(True, "buttons", "{}")
    session.send_message(True, "longtopic", "same")
    session.send_message(True, "longtopic", "same")

    assert session.prompt == "hello"
    assert session.buttons == "{}"
    assert client_mock.publish.call_count == 3


def test_get_session_reuses_existing_session():
    client_mock = Mock()
    existing_session = Mock()
    with patch.dict(kassa.sessions, {"SID": existing_session}, clear=True):
        assert kassa.get_session("SID", client_mock) is existing_session
        client_mock.publish.assert_not_called()


def test_get_session_starts_new_session():
    client_mock = Mock()
    session_mock = Mock()

    with patch.dict(kassa.sessions, {}, clear=True), patch(
        "kassa.Session", return_value=session_mock
    ) as session_class:
        assert kassa.get_session("SID", client_mock) is session_mock

    session_class.assert_called_with("SID", client_mock)
    session_mock.startup.assert_called_once()
    client_mock.publish.assert_called_with("hack42bar/output/sessions", '["SID"]')


def test_run_session_unhandled_action(capsys):
    kassa.run_session(Mock(), "SID", "unknown", b"data")
    assert "unhandled unknown" in capsys.readouterr().out


def test_on_message_short_topic_is_ignored():
    client_mock = Mock()
    msg_mock = Mock()
    msg_mock.topic = "short/topic"
    msg_mock.payload = b"data"

    with patch("kassa.run_session") as mock_run_session:
        kassa.on_message(client_mock, None, msg_mock)

    mock_run_session.assert_not_called()


def test_run_sets_up_client_and_stops_on_keyboard_interrupt():
    client_mock = Mock()

    with patch("kassa.mqtt.Client", return_value=client_mock), patch(
        "kassa.time.sleep", side_effect=[KeyboardInterrupt, KeyboardInterrupt]
    ):
        try:
            kassa.run()
        except KeyboardInterrupt:
            pass

    client_mock.connect.assert_called_with("localhost", 1883, 60)
    client_mock.loop_start.assert_called_once()


def test_startup_removes_module_in_second_import_pass():
    client_mock = Mock()
    session = kassa.Session("SID", client_mock)

    class GoodPlugin:
        def __init__(self, SID, master):
            self.SID = SID
            self.master = master

        def help(self):
            return {}

        def startup(self):
            return None

    names = ["receipt", "accounts", "products", "stock", "log", "POS", "existing"]

    with patch.dict(kassa.sys.modules, {"existing": Mock()}), patch(
        "glob.glob", side_effect=[[], [f"plugins/{name}.py" for name in names]]
    ):
        session.import_from = Mock(return_value=GoodPlugin)
        session.startup()

    assert "existing" not in kassa.sys.modules


def test_module_main_guard_calls_run_without_looping():
    source_path = Path(kassa.__file__).resolve()
    source = source_path.read_text(encoding="utf-8")
    source = source.replace("    while 1:\n", "    if False:\n", 1)

    exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
