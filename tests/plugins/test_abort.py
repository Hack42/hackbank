from unittest.mock import Mock, patch
import plugins.abort as abort_module


class TestAbort:
    def setup_method(self):
        self.master_mock = Mock()
        self.abort = abort_module.abort("SID", self.master_mock)

    def test_help(self):
        assert self.abort.help() == {"abort": "Abort everything"}

    def test_input_abort_with_iets_0(self):
        self.master_mock.iets = 0
        with patch.object(self.abort.master, "callhook") as mock_callhook:
            assert self.abort.input("abort")
            mock_callhook.assert_called_once_with("abort", None)

    def test_input_abort_with_iets_non_0(self):
        self.master_mock.iets = 1
        with patch.object(self.abort.master, "callhook") as mock_callhook:
            assert self.abort.input("abort")
            mock_callhook.assert_not_called()

    def test_input_ok(self):
        with patch.object(self.abort.master, "callhook") as mock_callhook:
            assert self.abort.input("ok")
            mock_callhook.assert_called_once_with("ok", None)

    def test_input_none(self):
        assert self.abort.input("some_other_input") is None

    def test_startup(self):
        # Assuming the startup method is only a pass and does nothing
        assert self.abort.startup() is None
