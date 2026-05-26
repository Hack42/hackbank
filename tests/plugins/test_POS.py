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

    def test_open_uses_configured_serial_port(self):
        serial_mock = Mock()
        with patch("plugins.POS.serial", new=serial_mock), patch(
            "plugins.POS.config_get",
            return_value={"port": "/dev/test-printer", "baudrate": 9600},
        ):
            self.POS.open()

        serial_mock.Serial.assert_called_with(
            port="/dev/test-printer",
            baudrate=9600,
            parity=serial_mock.PARITY_NONE,
            stopbits=serial_mock.STOPBITS_ONE,
            bytesize=serial_mock.EIGHTBITS,
        )

    def test_open_when_already_open(self):
        self.POS.ser = Mock()

        self.POS.open()

        self.POS.ser.write.assert_not_called()

    def test_instances_do_not_share_state(self):
        self.POS.bonnetjes[123] = {"bon": b"Test"}
        self.POS.ser = Mock()
        self.POS.lastbonID = 123

        other = POS_module.POS("SID2", Mock())

        assert other.bonnetjes == {}
        assert other.ser is None
        assert other.lastbonID == 0

    def test_help_and_hook_addremove(self):
        assert self.POS.help() == {
            "bon": "Print Receipt",
            "bons": "Receipts to print",
            "kassala": "Open cash drawer",
            "printstock": "Print stock overview",
        }
        assert self.POS.hook_addremove(()) is None

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

    def test_makebon_low_balance_warning(self):
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
            totals={"user": -10},
        )
        self.POS.master.transID = 42
        self.POS.master.accounts.accounts = {"user": {"amount": -5}}

        bon = self.POS.makebon("user")

        assert b"SALDO TE LAAG" in bon

    def test_makebon_cash_does_not_require_account(self):
        self.POS.master.receipt = Mock(
            receipt=[
                {
                    "product": "test",
                    "beni": "cash",
                    "count": 1,
                    "total": 1.0,
                    "description": "cash sale",
                }
            ],
            totals={"cash": -100},
        )
        self.POS.master.transID = 42
        self.POS.master.accounts.accounts = {}

        bon = self.POS.makebon("cash")

        assert b"cash sale" in bon
        assert b"Nieuw saldo" not in bon
        assert b"SALDO TE LAAG" not in bon

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

    def test_hook_post_checkout_deposit_opens_drawer_for_non_cash(self):
        self.POS.master.receipt = Mock(
            totals={"user1": 1.0},
            receipt=[{"product": "deposit"}, {"product": "other"}],
        )
        self.POS.master.transID = 123
        with patch.object(self.POS, "loadbons"), patch.object(
            self.POS, "writebons"
        ), patch.object(self.POS, "makebon", return_value=b"Test"), patch.object(
            self.POS, "drawer"
        ):
            self.POS.hook_post_checkout("user1")
            self.POS.drawer.assert_called_once()

    def test_hook_post_checkout_non_cash_without_deposit_keeps_drawer_closed(self):
        self.POS.master.receipt = Mock(totals={"user1": 1.0}, receipt=[])
        self.POS.master.transID = 123
        with patch.object(self.POS, "loadbons"), patch.object(
            self.POS, "writebons"
        ), patch.object(self.POS, "makebon", return_value=b"Test"), patch.object(
            self.POS, "drawer"
        ):
            self.POS.hook_post_checkout("user1")
            self.POS.drawer.assert_not_called()

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

    def test_selectbon_abort_and_missing_int(self):
        self.POS.bonnetjes = {}
        with patch.object(self.POS, "listbons") as mock_listbons:
            assert self.POS.selectbon("abort")
            self.master_mock.callhook.assert_called_with("abort", None)
            assert self.POS.selectbon("123")
            mock_listbons.assert_called_once()

    def test_writebons(self):
        with patch("builtins.open", mock_open()) as mocked_file:
            self.POS.bonnetjes = {123: {"totals": {"user": 1.0}, "bon": b"Test"}}
            self.POS.writebons()
            mocked_file.assert_called_with("data/revbank.POS", "w", encoding="utf-8")
            written = "".join(
                call.args[0] for call in mocked_file().write.call_args_list
            )
            loaded = json.loads(written)
            assert loaded["123"]["bon"]["encoding"] == "base64"

    def test_loadbons_pickle_backwards_compatible(self):
        with patch(
            "builtins.open", mock_open(read_data=pickle.dumps({123: {"bon": "Test"}}))
        ):
            self.POS.loadbons()
            assert 123 in self.POS.bonnetjes

    def test_loadbons_json(self):
        data = json.dumps(
            {
                "123": {
                    "totals": {"user": 1.0},
                    "bon": {"encoding": "base64", "data": "VGVzdA=="},
                }
            }
        ).encode("utf-8")
        with patch("builtins.open", mock_open(read_data=data)):
            self.POS.loadbons()
            assert self.POS.bonnetjes == {
                123: {"totals": {"user": 1.0}, "bon": b"Test"}
            }

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
            assert self.POS.input("other") is None

    def test_startup_loads_bons(self):
        with patch.object(self.POS, "loadbons") as mock_loadbons:
            self.POS.startup()
            mock_loadbons.assert_called_once()

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
        with patch("builtins.open", mock_open()):
            self.POS.bonnetjes = {i: {"bon": "Test"} for i in range(60)}
            self.POS.writebons()
            assert len(self.POS.bonnetjes) == 50

    def test_loadbons_file_error(self):
        self.POS.bonnetjes = {123: {"bon": "stale"}}
        with patch("builtins.open", new_callable=mock_open(), side_effect=Exception):
            self.POS.loadbons()
            assert self.POS.bonnetjes == {}

    def test_loadbons_invalid_data_clears_stale_bons(self):
        self.POS.bonnetjes = {123: {"bon": "stale"}}
        with patch("builtins.open", mock_open(read_data=b"not json or pickle")):
            self.POS.loadbons()

        assert self.POS.bonnetjes == {}

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
