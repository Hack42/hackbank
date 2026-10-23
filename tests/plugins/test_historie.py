from unittest.mock import Mock, patch, mock_open, MagicMock
import json
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

    def test_reverse_readline_yields_segment_on_newline_boundary(self, tmp_path):
        log_file = tmp_path / "revbank.log"
        log_file.write_text("abc\ndef\n", encoding="utf-8")

        assert list(self.historie.reverse_readline(log_file, buf_size=4)) == [
            "def",
            "abc",
        ]

    def test_reverse_readline_joins_segment_across_chunks(self, tmp_path):
        log_file = tmp_path / "revbank.log"
        log_file.write_text("abc\ndef", encoding="utf-8")

        assert list(self.historie.reverse_readline(log_file, buf_size=4)) == [
            "def",
            "abc",
        ]

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

    def test_history_unknown_user_without_patches(self):
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

    def test_checkout_refreshes_profile_and_celebrates_once_after_session_ends(self):
        self.master_mock.receipt.receipt = [
            {"Lose": True, "count": 1, "value": 2, "product": "cola"}
        ]
        self.master_mock.accounts.accounts = {"Jos": {"amount": 20}}
        self.historie.hook_post_checkout("Jos")
        self.master_mock.send_message.assert_not_called()
        self.master_mock.accounts.accounts["Jos"]["amount"] = 18
        with patch.object(
            self.historie,
            "account_details",
            return_value={"user": "Jos", "purchases": [{"description": "Cola"}]},
        ):
            self.historie.hook_post_endsession("Jos")
        messages = self.master_mock.send_message.call_args_list
        profile = json.loads(messages[0].args[2])
        assert profile == {
            "user": "Jos",
            "amount": 18,
            "purchases": [{"description": "Cola"}],
            "checkout": True,
        }
        assert messages[0].args[:2] == (False, "infobox/account")
        assert messages[1].args[:2] == (True, "buttons")
        assert messages[2].args == (False, "effects", '{"type": "sale"}')
        self.historie.hook_post_endsession("Jos")
        assert self.master_mock.send_message.call_count == 3

    def test_cash_sale_celebrates_without_an_account_profile(self):
        self.master_mock.receipt.receipt = [
            {"Lose": True, "count": 1, "value": 2, "product": "cola"}
        ]
        self.master_mock.accounts.accounts = {}
        self.historie.hook_post_checkout("cash")
        self.historie.hook_post_endsession("cash")
        self.master_mock.send_message.assert_called_once_with(
            False, "effects", '{"type": "sale"}'
        )

    def test_refunds_transfers_and_undo_do_not_celebrate_as_sales(self):
        self.master_mock.accounts.accounts = {}
        for product in ("undo", "give", "take", "declaratie", "pfand_cola"):
            self.master_mock.receipt.receipt = [
                {"Lose": True, "count": 1, "value": 2, "product": product}
            ]
            self.historie.hook_post_checkout("cash")
            self.historie.hook_post_endsession("cash")
        self.master_mock.receipt.receipt = [
            {"Lose": False, "count": 1, "value": 20, "product": "deposit"}
        ]
        self.historie.hook_post_checkout("cash")
        self.historie.hook_post_endsession("cash")
        self.master_mock.send_message.assert_not_called()

    def test_history_unknown_user(self):
        self.master_mock.accounts.accounts = {}
        result = self.historie.history("nonexistent_user")
        assert result is True

    def test_help_and_startup(self):
        assert self.historie.help() == {"history": "User History"}
        assert self.historie.startup() is None

    def test_reversesearch_returns_after_201_matches(self):
        with patch.object(
            self.historie,
            "reverse_readline",
            return_value=[f"{i} needle" for i in range(250)],
        ):
            lines = self.historie.reversesearch("needle")

        assert len(lines) == 201
        assert lines[0] == "200 needle"
        assert lines[-1] == "0 needle"

    def test_reversesearch_ignores_lines_without_match_after_position_zero(self):
        with patch.object(
            self.historie,
            "reverse_readline",
            return_value=["needle at zero", "x needle", "nope"],
        ):
            lines = self.historie.reversesearch("needle")

        assert lines == ["x needle"]
