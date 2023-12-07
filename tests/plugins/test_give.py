from unittest.mock import Mock, patch
import plugins.give as give_module
import json


class TestGive:
    def setup_method(self):
        self.master_mock = Mock()
        self.give = give_module.give("SID", self.master_mock)

    def test_help(self):
        assert self.give.help() == {"give": "Give Money to other user"}

    def test_who_valid_user(self):
        self.master_mock.accounts = Mock(accounts={"user1": {}})
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.who("user1")
            self.give.master.donext.assert_called_with(self.give, "amount")
            self.give.master.send_message.assert_called()

    def test_who_abort(self):
        self.master_mock.accounts.accounts = {}
        with patch.object(self.give.master, 'callhook'):
            assert self.give.who("abort")
            self.give.master.callhook.assert_called_with("abort", None)

    def test_who_unknown_user(self):
        self.master_mock.accounts = Mock(accounts={})
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.who("user2")
            self.give.master.donext.assert_called_with(self.give, "who")
            self.give.master.send_message.assert_called()

    def test_amount_valid(self):
        self.give.userto = "user1"
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.amount("10")
            self.give.master.donext.assert_called_with(self.give, "reason")
            self.give.master.send_message.assert_called()

    def test_amount_invalid(self):
        self.give.userto = "user1"
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.amount("invalid")
            self.give.master.donext.assert_called_with(self.give, "amount")
            self.give.master.send_message.assert_called()

    def test_amount_abort(self):
        with patch.object(self.give.master, 'callhook'):
            assert self.give.amount("abort")
            self.give.master.callhook.assert_called_with("abort", None)

    def test_reason(self):
        self.give.userto = "user1"
        self.give.value = 10
        with patch.object(self.give.master.receipt, 'add'):
            assert self.give.reason("reason")
            self.give.master.receipt.add.assert_called()

    def test_reason_abort(self):
        with patch.object(self.give.master, 'callhook'):
            assert self.give.reason("abort")
            self.give.master.callhook.assert_called_with("abort", None)

    def test_input_give(self):
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.input("give")
            self.give.master.donext.assert_called_with(self.give, "who")
            self.give.master.send_message.assert_called()

    def test_input_other(self):
        assert self.give.input("other") is None

    def test_startup(self):
        # Since startup method passes, just call it to ensure coverage
        self.give.startup()
    def test_amount_large_value(self):
        self.give.userto = "user1"
        with patch.object(self.give.master, 'donext'), patch.object(self.give.master, 'send_message'):
            assert self.give.amount("1001")
            self.give.master.donext.assert_called_with(self.give, "amount")
            self.give.master.send_message.assert_called()
