from unittest.mock import patch, mock_open, MagicMock
import plugins.log as log_module
import time


class TestLog:
    def setup_method(self, method):
        self.master_mock = MagicMock()
        self.log = log_module.log("SID", self.master_mock)

    def test_startup(self):
        with patch.object(self.master_mock, "send_message") as mock_send_message:
            self.log.startup()
            mock_send_message.assert_called_with(False, "log", "Log has startup")

    def test_log(self):
        test_action = "TEST_ACTION"
        test_text = "Test text"
        mo = mock_open()
        with patch("builtins.open", mo):
            self.log.log(test_action, test_text)
            mo.assert_called_with("data/revbank.log", "a", encoding="utf-8")
            handle = mo()
            handle.write.assert_called_with(
                time.strftime("%Y-%m-%d_%H:%M:%S")
                + " "
                + test_action
                + " "
                + test_text
                + "\n"
            )

    def test_hook_balance(self):
        test_args = ("user", 100.0, 90.0, 123)
        mo = mock_open()
        with patch("builtins.open", mo):
            self.log.hook_balance(test_args)
            mo.assert_called_with("data/revbank.log", "a", encoding="utf-8")
            handle = mo()
            expected_log = f"{time.strftime('%Y-%m-%d_%H:%M:%S')} BALANCE 123        user had +100.00, lost -10.00, now has +90.00\n"
            handle.write.assert_called_with(expected_log)

    def test_hook_post_checkout(self):
        self.log.master.receipt = MagicMock(
            receipt=[
                {
                    "beni": "user",
                    "count": 2,
                    "value": 50.0,
                    "Lose": True,
                    "description": "Test",
                }
            ]
        )
        self.log.master.transID = 456
        mo = mock_open()
        with patch("builtins.open", mo):
            self.log.hook_post_checkout(None)
            mo.assert_called_with("data/revbank.log", "a", encoding="utf-8")
            handle = mo()
            expected_log = f"{time.strftime('%Y-%m-%d_%H:%M:%S')} CHECKOUT 456        user 2 *      50.00 LOSE EUR     100.00 # Test\n"
            handle.write.assert_called_with(expected_log)

    def test_pre_input(self):
        test_text = "input text"
        self.log.master.prompt = b"Test Prompt"
        mo = mock_open()
        with patch("builtins.open", mo), patch.object(
            self.master_mock, "send_message"
        ) as mock_send_message:
            self.log.pre_input(test_text)
            mo.assert_called_with("data/revbank.log", "a", encoding="utf-8")
            handle = mo()
            expected_log = f"{time.strftime('%Y-%m-%d_%H:%M:%S')} PROMPT Test Prompt >> {test_text}\n"
            handle.write.assert_called_with(expected_log)
