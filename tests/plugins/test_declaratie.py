from unittest.mock import Mock, patch, mock_open
import plugins.declaratie as declaratie_module
import json


class TestDeclaratie:
    def setup_method(self, method):
        self.master_mock = Mock()
        self.declaratie = declaratie_module.declaratie("SID", self.master_mock)

    def test_help(self):
        assert self.declaratie.help() == {
            "declaratie": "Declaration",
            "afroom": "Remove cash money",
            "verkoop": "Report sales",
        }

    def test_who_known_user(self):
        self.master_mock.accounts.accounts = {"known_user": {}}
        with patch.object(
            self.declaratie.master, "donext"
        ) as mock_donext, patch.object(
            self.declaratie.master, "send_message"
        ) as mock_send_message:
            assert self.declaratie.who("known_user")
            mock_donext.assert_called_with(self.declaratie, "amount")
            mock_send_message.assert_called()

    def test_who_unknown_user(self):
        self.master_mock.accounts.accounts = {}
        with patch.object(
            self.declaratie.master, "donext"
        ) as mock_donext, patch.object(
            self.declaratie.master, "send_message"
        ) as mock_send_message:
            assert self.declaratie.who("unknown_user")
            mock_donext.assert_called_with(self.declaratie, "who")
            mock_send_message.assert_called()

    def test_who_abort(self):
        self.master_mock.accounts.accounts = {}
        with patch.object(self.declaratie.master, "callhook") as mock_callhook:
            assert self.declaratie.who("abort")
            mock_callhook.assert_called_with("abort", None)

    def test_amount_valid(self):
        self.declaratie.soort = "declaratie"
        with patch.object(
            self.declaratie.master, "donext"
        ) as mock_donext, patch.object(
            self.declaratie.master, "send_message"
        ) as mock_send_message:
            assert self.declaratie.amount("100")
            mock_donext.assert_called_with(self.declaratie, "reason")
            mock_send_message.assert_called()

    def test_amount_invalid(self):
        self.declaratie.soort = "declaratie"
        with patch.object(
            self.declaratie.master, "donext"
        ) as mock_donext, patch.object(
            self.declaratie.master, "send_message"
        ) as mock_send_message:
            assert self.declaratie.amount("invalid")
            mock_donext.assert_called_with(self.declaratie, "amount")
            mock_send_message.assert_called()

    def test_amount_abort(self):
        with patch.object(self.declaratie.master, "callhook") as mock_callhook:
            assert self.declaratie.amount("abort")
            mock_callhook.assert_called_with("abort", None)

    def test_reason(self):
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        assert self.declaratie.reason("test reason")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runasbar")
        self.declaratie.master.send_message.assert_called()

    def test_askbar(self):
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        assert self.declaratie.askbar("")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runasbar")
        self.declaratie.master.send_message.assert_called()

    def test_runasbar_valid(self):
        self.declaratie.value = 100
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runasbar("50")
        self.declaratie.master.donext.assert_called()

    def test_runasbar_invalid(self):
        self.declaratie.value = 100
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runasbar("invalid")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runasbar")

    def test_askcash(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        assert self.declaratie.askcash("")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runascash")
        self.declaratie.master.send_message.assert_called()

    def test_runascash_valid(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runascash("25")
        self.declaratie.master.donext.assert_called()

    def test_runascash_invalid(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runascash("invalid")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runascash")

    def test_askbank(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.ascash = 25
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        assert self.declaratie.askbank("")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runasbank")
        self.declaratie.master.send_message.assert_called()

    def test_runasbank_valid(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.ascash = 25
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runasbank("25")
        self.declaratie.master.donext.assert_called()

    def test_runasbank_invalid(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.ascash = 25
        self.declaratie.master.donext = Mock()
        assert self.declaratie.runasbank("invalid")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "runasbank")

    def test_correct_yes(self):
        self.declaratie.ascash = 10
        self.declaratie.asbar = 20
        self.declaratie.asbank = 30
        self.declaratie.master.receipt = Mock()
        self.declaratie.master.callhook = Mock()
        self.declaratie.save = Mock()
        assert self.declaratie.correct("yes")
        self.declaratie.master.receipt.add.assert_called()
        self.declaratie.master.callhook.assert_called()
        self.declaratie.save.assert_called()

    def test_correct_no_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.correct("no")
        assert self.declaratie.correct("abort") is None
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_final(self):
        self.declaratie.bon = Mock()
        self.declaratie.master.send_message = Mock()
        self.declaratie.master.donext = Mock()
        assert self.declaratie.final()

    def test_who_invalid_user(self):
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        self.declaratie.master.accounts.accounts = {}
        assert self.declaratie.who("unknown_user")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "who")
        self.declaratie.master.send_message.assert_called()

    def test_who_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.who("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_amount_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.amount("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_amount_invalid(self):
        self.declaratie.master.donext = Mock()
        assert self.declaratie.amount("invalid")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "amount")

    def test_amount_too_high(self):
        self.declaratie.master.donext = Mock()
        self.declaratie.master.send_message = Mock()
        assert self.declaratie.amount("5000")
        self.declaratie.master.donext.assert_called_with(self.declaratie, "amount")
        self.declaratie.master.send_message.assert_called()

    def test_reason_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.reason("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_runasbar_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.runasbar("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_runasbar_invalid_value(self):
        self.declaratie.value = 100
        assert self.declaratie.runasbar("invalid")
        # No assert here as this results in a call to askbar with an error message

    def test_runascash_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.runascash("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_runascash_invalid_value(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        assert self.declaratie.runascash("invalid")
        # No assert here as this results in a call to askcash with an error message

    def test_runasbank_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.runasbank("abort")
        self.declaratie.master.callhook.assert_called_with("abort", None)

    def test_runasbank_invalid_value(self):
        self.declaratie.value = 100
        self.declaratie.asbar = 50
        self.declaratie.ascash = 25
        assert self.declaratie.runasbank("invalid")
        # No assert here as this results in a call to askbank with an error message

    def test_correct_invalid(self):
        self.declaratie.master.send_message = Mock()
        self.declaratie.master.donext = Mock()
        assert self.declaratie.correct("invalid")
        self.declaratie.master.send_message.assert_called()
        self.declaratie.master.donext.assert_called_with(self.declaratie, "correct")

    def test_input_invalid_command(self):
        assert self.declaratie.input("invalid") is None

    def test_input_abort(self):
        self.declaratie.master.callhook = Mock()
        assert self.declaratie.input("abort") is None
        self.declaratie.master.callhook.assert_called_with("abort", None)
