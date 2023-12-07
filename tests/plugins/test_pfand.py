from unittest.mock import Mock, patch, mock_open
import plugins.pfand as pfand_module


class TestPfand:
    def setup_method(self):
        self.master_mock = Mock()
        self.pfand = pfand_module.pfand("SID", self.master_mock)

    def test_hook_addremove(self):
        self.pfand.products = {"prod1": 1.0}
        args = (False, 2.0, "Description", 1, "Beni", "prod1")
        self.pfand.hook_addremove(args)
        self.master_mock.receipt.add.assert_called_with(
            True, 1.0, "Pfand Description", 1, "Beni", "pfand_prod1"
        )

    def test_listpfand(self):
        self.pfand.products = {"prod1": 1.0}
        # Mocking the required properties of master.products
        self.pfand.master.products = Mock()
        self.pfand.master.products.lookupprod.return_value = True
        self.pfand.master.products.products = {'prod1': {'description': 'desc1'}}
    
        with patch.object(self.pfand.master, "send_message") as mock_send:
            self.pfand.listpfand()
            mock_send.assert_called()
    def test_pfand_known_product(self):
        self.pfand.products = {"prod1": 1.0}
        assert self.pfand.pfand("prod1") is True
        self.master_mock.receipt.add.assert_called_with(
            False, 1.0, "Pfand return prod1", 1, None, "return_prod1"
        )

    def test_pfand_unknown_product(self):
        self.pfand.products = {"prod1": 1.0}
        with patch.object(self.pfand, "listpfand"):
            assert self.pfand.pfand("prod2") is True
            self.pfand.listpfand.assert_called()

    def test_input(self):
        with patch.object(self.pfand, "listpfand"):
            assert self.pfand.input("pfand") is True
            self.pfand.listpfand.assert_called()

    def test_loadmarket(self):
        market_data = "prod1 1.0\nprod2 2.0\n"
        mo = patch("builtins.open", mock_open(read_data=market_data))
        with mo:
            self.pfand.loadmarket()
            assert self.pfand.products == {"prod1": 1.0, "prod2": 2.0}

    def test_hook_abort(self):
        with patch.object(self.pfand, "startup"):
            self.pfand.hook_abort(None)
            self.pfand.startup.assert_called()

    def test_startup(self):
        with patch.object(self.pfand, "loadmarket"):
            self.pfand.startup()
            self.pfand.loadmarket.assert_called()


