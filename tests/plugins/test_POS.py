from unittest.mock import Mock, patch, call, mock_open
import plugins.POS as POS_module
import json
import pickle


class TestPOS:
    def setup_method(self, method):
        self.master_mock = Mock()
        self.POS = POS_module.POS("SID", self.master_mock)

    def test_open(self):
        with patch("plugins.POS.serial", new=Mock()):
            self.POS.open()
            assert self.POS.ser is not None

    def test_printstock(self):
        self.master_mock.stock = Mock(stock={"item1": 10, "item2": 20})
        with patch.object(self.POS, "open"), patch.object(self.POS, "slowwrite"):
            self.POS.printstock()
            self.POS.open.assert_called()
            self.POS.slowwrite.assert_called()

    def test_printdisplay(self):
        self.POS.ser = Mock()
        with patch.object(self.POS, "open"), patch("plugins.POS.serial", new=Mock()):
            self.POS.printdisplay("Test", 1.0, 2.0)
            self.POS.open.assert_called()

    def test_drawer(self):
        self.POS.ser = Mock()
        with patch.object(self.POS, "open"), patch("plugins.POS.serial", new=Mock()):
            self.POS.drawer()
            self.POS.open.assert_called()

    def test_hook_undo(self):
        self.POS.bonnetjes = {123: {"bon": b"Test"}}
        with patch.object(self.POS, "loadbons"), patch.object(self.POS, "writebons"):
            self.POS.hook_undo((123, None, None, None))
            assert b"VOID" in self.POS.bonnetjes[123]["bon"]
            self.POS.writebons.assert_called()

    def test_makebon(self):
        self.POS.master.receipt = Mock(
            receipt=[
                {
                    "product": "test",
                    "beni": "user",
                    "count": 1,
                    "total": 1.0,
                    "description": "test",
                }
            ],
            totals={"user": 10},
        )
        self.POS.master.transID = 42
        self.POS.master.accounts.accounts = {"user": {"amount": 10}}
        bon = self.POS.makebon("user")
        assert b"test" in bon

    def test_hook_checkout(self):
        with patch.object(self.POS, "drawer"):
            self.POS.hook_checkout("cash")
            self.POS.drawer.assert_called()

    def test_printdeclaratie(self):
        with patch.object(self.POS, "open"), patch.object(self.POS, "slowwrite"):
            self.POS.printdeclaratie(("Test", "Type", "Reason", 1.0, 2.0, 3.0))
            self.POS.open.assert_called()
            self.POS.slowwrite.assert_called()

    def test_hook_post_checkout(self):
        self.POS.master.receipt = Mock(totals={"user1": 1.0, "user2": 2.0})
        with patch.object(self.POS, "loadbons"), patch.object(
            self.POS, "writebons"
        ), patch.object(self.POS, "makebon", return_value=b"Test"), patch.object(
            self.POS, "drawer"
        ):
            self.POS.hook_post_checkout("cash")
            self.POS.loadbons.assert_called()
            self.POS.writebons.assert_called()
            self.POS.drawer.assert_called()

    def test_slowwrite(self):
        with patch("plugins.POS.serial", return_value=Mock()):
            self.POS.open()
            self.POS.slowwrite(b"Test")
            self.POS.ser.write.assert_called()

    def test_bon(self):
        self.POS.bonnetjes = {123: {"bon": "Test"}}
        with patch.object(self.POS, "open"), patch.object(self.POS, "slowwrite"):
            assert self.POS.bon(123)
            self.POS.open.assert_called()
            self.POS.slowwrite.assert_called()

    def test_selectbon(self):
        self.POS.bonnetjes = {123: {"bon": "Test"}}
        with patch.object(self.POS, "bon"):
            assert self.POS.selectbon("123")
            self.POS.bon.assert_called_with(123)

    def test_writebons(self):
        with patch("builtins.open", new_callable=mock_open):
            self.POS.bonnetjes = {123: {"bon": "Test"}}
            self.POS.writebons()
            # Assert file operation

    def test_loadbons(self):
        with patch(
            "builtins.open", mock_open(read_data=pickle.dumps({123: {"bon": "Test"}}))
        ):
            self.POS.loadbons()
            assert 123 in self.POS.bonnetjes

    def test_listbons(self):
        self.POS.bonnetjes = {123: {"totals": {"user": 1.0}, "bon": "Test"}}
        with patch.object(self.POS, "loadbons"), patch.object(
            self.POS.master, "send_message"
        ):
            self.POS.listbons()
            self.POS.master.send_message.assert_called()

    def test_input(self):
        with patch.object(self.POS, "bon"), patch.object(
            self.POS, "listbons"
        ), patch.object(self.POS, "drawer"), patch.object(self.POS, "printstock"):
            assert self.POS.input("bon")
            assert self.POS.input("bons")
            assert self.POS.input("kassala")
            assert self.POS.input("printstock")

    def test_printstock_content(self):
        self.master_mock.stock = Mock(stock={"item1": 10, "item2": 20})
        with patch.object(self.POS, "open"), patch.object(
            self.POS, "slowwrite"
        ) as mock_slowwrite:
            self.POS.printstock()
            assert b"item1" in mock_slowwrite.call_args[0][0]
            assert b"item2" in mock_slowwrite.call_args[0][0]

    def test_printdisplay_output(self):
        self.POS.ser = Mock()
        with patch.object(self.POS, "open"):
            self.POS.printdisplay("Test", 1.0, 2.0)
            expected_output = b"\x1b=\x02\x1b@Test            1.00Total           2.00"
            self.POS.ser.write.assert_called_with(expected_output)

    def test_hook_checkout_non_cash(self):
        with patch.object(self.POS, "drawer") as mock_drawer:
            self.POS.hook_checkout("non-cash")
            mock_drawer.assert_not_called()

    def test_hook_undo_nonexistent_transID(self):
        with patch.object(self.POS, "loadbons"), patch.object(self.POS, "writebons"):
            self.POS.hook_undo((9999, None, None, None))
            assert 9999 not in self.POS.bonnetjes

    def test_makebon_long_description(self):
        self.POS.master.receipt = Mock(
            receipt=[
                {
                    "product": "test",
                    "beni": "user",
                    "count": 1,
                    "total": 1.0,
                    "description": "a" * 26,
                },
            ],
            totals={"user": 10},
        )
        self.POS.master.transID = 42
        self.POS.master.accounts.accounts = {"user": {"amount": 10}}
        bon = self.POS.makebon("user")
        assert b"a" * 22 in bon

    def test_slowwrite_long_string(self):
        self.POS.ser = Mock()
        self.POS.open()
        long_string = b"a" * 100
        self.POS.slowwrite(long_string)
        assert self.POS.ser.write.call_count == 4  # 100 / 32 rounded up

    def test_bon_nonexistent_bonID(self):
        with patch.object(self.POS, "open"), patch.object(self.POS, "slowwrite"):
            assert not self.POS.bon(9999)

    def test_selectbon_invalid_bonID(self):
        self.setup_method(None)
        self.POS.bonnetjes = {}
        with patch.object(self.POS, "bon"), patch(
            "plugins.POS.traceback.print_exc"
        ) as mock_traceback:
            assert self.POS.selectbon("invalid")
            mock_traceback.assert_called()

    def test_writebons_max_receipts(self):
        with patch("builtins.open", new_callable=mock_open()):
            self.POS.bonnetjes = {i: {"bon": "Test"} for i in range(60)}
            self.POS.writebons()
            assert len(self.POS.bonnetjes) == 50

    def test_loadbons_file_error(self):
        self.POS.bonnetjes = {}
        with patch("builtins.open", new_callable=mock_open(), side_effect=Exception):
            self.POS.loadbons()
            assert self.POS.bonnetjes == {}  # remains empty

    def test_listbons_max_receipts(self):
        self.POS.bonnetjes = {
            i: {"totals": {"user": 1.0}, "bon": "Test"} for i in range(60)
        }
        with patch.object(self.POS, "loadbons"), patch.object(
            self.POS.master, "send_message"
        ):
            self.POS.listbons()
            jsons = self.POS.master.send_message.call_args_list[0][0][2]
            assert len(json.loads(jsons)["custom"]) == 50
