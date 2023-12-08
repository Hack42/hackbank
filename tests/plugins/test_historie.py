from unittest.mock import Mock, patch, mock_open, MagicMock
import plugins.historie as historie_module


class TestHistorie:
    def setup_method(self):
        self.master_mock = Mock()
        self.historie = historie_module.historie("SID", self.master_mock)

    def mock_seek(self, *args):
        # This function can handle any number of arguments
        pass

    def test_reverse_readline(self):
        test_data = "Line1\nLine2\nLine3\nLine4"
        mo = mock_open(read_data=test_data)
        with patch("builtins.open", mo) as mock_file:
            file_handle = mo.return_value
            file_handle.tell.return_value = len(test_data)
            file_handle.read.side_effect = [test_data, ""]
            file_handle.seek.side_effect = self.mock_seek
            result = list(self.historie.reverse_readline("testfile.txt"))
            assert result == ["Line4", "Line3", "Line2", "Line1"]

    def test_history_valid_user(self):
        self.historie.master.accounts.accounts = {"user1": {}}
        with patch.object(
            self.historie, "reversesearch", return_value=["Line1", "Line2"]
        ), patch.object(self.historie.master, "send_message"):
            assert self.historie.history("user1")
            self.historie.master.send_message.assert_called()

    def test_history_abort(self):
        self.historie.master.accounts.accounts = {}
        with patch.object(self.historie.master, "callhook"):
            assert self.historie.history("abort")
            self.historie.master.callhook.assert_called_with("abort", None)

    def test_history_unknown_user(self):
        self.historie.master.accounts.accounts = {}
        with patch.object(self.historie.master, "donext"), patch.object(
            self.historie.master, "send_message"
        ):
            assert self.historie.history("unknown_user")
            self.historie.master.donext.assert_called_with(self.historie, "history")
            self.historie.master.send_message.assert_called()

    def test_input_history(self):
        with patch.object(self.historie.master, "donext"), patch.object(
            self.historie.master, "send_message"
        ):
            assert self.historie.input("history")
            self.historie.master.donext.assert_called_with(self.historie, "history")
            self.historie.master.send_message.assert_called()

    def test_input_other(self):
        assert not self.historie.input("other")

    def test_history_unknown_user(self):
        self.master_mock.accounts.accounts = {}
        result = self.historie.history("nonexistent_user")
        assert result is True
