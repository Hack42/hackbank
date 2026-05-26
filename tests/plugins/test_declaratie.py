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

    def test_who_abort_original(self):
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

    def test_amount_invalid_original(self):
        self.declaratie.soort = "declaratie"
        with patch.object(
            self.declaratie.master, "donext"
        ) as mock_donext, patch.object(
            self.declaratie.master, "send_message"
        ) as mock_send_message:
            assert self.declaratie.amount("invalid")
            mock_donext.assert_called_with(self.declaratie, "amount")
            mock_send_message.assert_called()

    def test_amount_abort_original(self):
        with patch.object(self.declaratie.master, "callhook") as mock_callhook:
            assert self.declaratie.amount("abort")
            mock_callhook.assert_called_with("abort", None)

    def test_amount_abort_inside_exception_branch(self):
        class DelayedAbort:
            def __init__(self):
                self.calls = 0

            def __eq__(self, other):
                self.calls += 1
                return self.calls > 1 and other == "abort"

            def __float__(self):
                raise ValueError("not numeric")

        assert self.declaratie.amount(DelayedAbort()) is True
        self.master_mock.callhook.assert_called_with("abort", None)

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

    def test_declaratie_specific_ask_messages(self):
        self.declaratie.soort = "declaratie"

        assert self.declaratie.askbar("")
        self.master_mock.send_message.assert_any_call(
            True, "message", "How much do you want on your bar account?"
        )

        self.master_mock.reset_mock()
        assert self.declaratie.askcash("")
        self.master_mock.send_message.assert_any_call(
            True, "message", "How much do you want in cash?"
        )

        self.master_mock.reset_mock()
        assert self.declaratie.askbank("")
        self.master_mock.send_message.assert_any_call(
            True, "message", "How much do you want in your bankaccount?"
        )

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
        self.declaratie.master.accounts.accounts = {}
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

    def test_who_messages_for_verkoop_and_afroom(self):
        self.master_mock.accounts.accounts = {"known_user": {}}

        self.declaratie.soort = "verkoop"
        assert self.declaratie.who("known_user")
        self.master_mock.send_message.assert_any_call(
            True, "message", "How much money did you get?"
        )

        self.master_mock.reset_mock()
        self.declaratie.soort = "afroom"
        assert self.declaratie.who("known_user")
        self.master_mock.send_message.assert_any_call(
            True, "message", "How much money are you taking?"
        )

    def test_amount_verkoop_and_afroom_paths(self):
        self.declaratie.soort = "verkoop"
        assert self.declaratie.amount("10")
        assert self.declaratie.value == -10
        self.master_mock.send_message.assert_any_call(
            True, "message", "Why do you give us E 10.00?"
        )

        self.master_mock.reset_mock()
        self.declaratie.soort = "afroom"
        self.declaratie.final = Mock(return_value=True)
        assert self.declaratie.amount("25")
        assert self.declaratie.reden == "Afroom"
        assert self.declaratie.ascash == -25
        assert self.declaratie.asbank == 25
        self.declaratie.final.assert_called_once()

    def test_amount_invalid_verkoop_message(self):
        self.declaratie.soort = "verkoop"
        assert self.declaratie.amount("invalid")
        self.master_mock.send_message.assert_any_call(
            True, "message", "Not a valid number! How much money did you get?"
        )

    def test_askbar_and_askcash_non_declaratie_messages(self):
        self.declaratie.soort = "verkoop"
        self.declaratie.value = 10
        assert self.declaratie.askbar("err ")
        self.master_mock.send_message.assert_any_call(
            True, "message", "err How much do you want from your bar account?"
        )

        self.master_mock.reset_mock()
        self.declaratie.asbar = 3
        assert self.declaratie.askcash("err ")
        self.master_mock.send_message.assert_any_call(
            True, "message", "err How much do you give in cash?"
        )

    def test_runasbar_boundary_paths(self):
        self.declaratie.value = 10
        self.declaratie.askbar = Mock(return_value=True)
        assert self.declaratie.runasbar("11")
        self.declaratie.askbar.assert_called_with("E 11.00 is larger than E 10.00 ; ")

        self.declaratie.askbar.reset_mock()
        assert self.declaratie.runasbar("5000")
        self.declaratie.askbar.assert_called_with("Not between 0.01 and 4999.99; ")

        self.declaratie.final = Mock(return_value=True)
        assert self.declaratie.runasbar("10")
        self.declaratie.final.assert_called_once()

    def test_runascash_boundary_paths(self):
        self.declaratie.value = 10
        self.declaratie.asbar = 3
        self.declaratie.askcash = Mock(return_value=True)
        assert self.declaratie.runascash("8")
        self.declaratie.askcash.assert_called_with("E 8.00 is larger than E 7.00 ; ")

        self.declaratie.askcash.reset_mock()
        assert self.declaratie.runascash("5000")
        self.declaratie.askcash.assert_called_with("Not between 0 and 4999.99; ")

        self.declaratie.final = Mock(return_value=True)
        assert self.declaratie.runascash("7")
        self.declaratie.final.assert_called_once()

    def test_askbank_and_runasbank_boundary_paths(self):
        self.declaratie.soort = "verkoop"
        self.declaratie.value = 10
        self.declaratie.asbar = 3
        self.declaratie.ascash = 2
        assert self.declaratie.askbank("err ")
        self.master_mock.send_message.assert_any_call(
            True, "message", "err How much do you send from your bankaccount?"
        )

        self.declaratie.askbank = Mock(return_value=True)
        assert self.declaratie.runasbank("6")
        self.declaratie.askbank.assert_called_with("E 6.00 is larger than E 5.00 ; ")

        self.declaratie.askbank.reset_mock()
        assert self.declaratie.runasbank("5000")
        self.declaratie.askbank.assert_called_with("Not between 0.01 and 4999.99; ")

        self.declaratie.askbank.reset_mock()
        assert self.declaratie.runasbank("4")
        self.declaratie.askbank.assert_called_with("The numbers do not match; ")

    def test_correct_yes_negative_bar_and_cash_drawer(self):
        self.declaratie.ascash = 10
        self.declaratie.asbar = -20
        self.declaratie.asbank = 30
        self.declaratie.wie = "user1"
        self.declaratie.master.receipt = Mock()
        self.declaratie.master.callhook = Mock()
        self.declaratie.master.POS = Mock()
        self.declaratie.save = Mock()

        assert self.declaratie.correct("yes")

        self.declaratie.master.receipt.add.assert_called_with(
            True, 20, "Declaratie", 1, "user1", "declaratie"
        )
        self.declaratie.master.POS.drawer.assert_called_once()
        self.declaratie.save.assert_called_once()

    def test_bon_save_startup_and_input_commands(self):
        self.declaratie.wie = "user1"
        self.declaratie.soort = "declaratie"
        self.declaratie.reden = "reason"
        self.declaratie.asbar = 1
        self.declaratie.ascash = 2
        self.declaratie.asbank = 3
        self.declaratie.master.POS = Mock()

        self.declaratie.bon()
        self.declaratie.master.POS.printdeclaratie.assert_called_with(
            ("user1", "declaratie", "reason", 1, 2, 3)
        )

        with patch("builtins.open", mock_open()) as mocked_file, patch(
            "plugins.declaratie.time.strftime", return_value="2026-05-19"
        ):
            self.declaratie.save()
        mocked_file().write.assert_called_once()

        assert self.declaratie.startup() is None

        for command in ("declaratie", "verkoop", "afroom"):
            self.master_mock.reset_mock()
            assert self.declaratie.input(command)
            assert self.declaratie.soort == command
            self.master_mock.donext.assert_called_with(self.declaratie, "who")

    def test_instances_do_not_share_state(self):
        self.declaratie.wie = "user1"
        self.declaratie.value = 10
        self.declaratie.reden = "reason"
        self.declaratie.ascash = 1
        self.declaratie.asbank = 2
        self.declaratie.asbar = 3
        self.declaratie.soort = "declaratie"

        other = declaratie_module.declaratie("SID2", Mock())

        assert other.wie == ""
        assert other.value == 0
        assert other.reden == ""
        assert other.ascash == 0
        assert other.asbank == 0
        assert other.asbar == 0
        assert other.soort == ""
