from unittest.mock import patch, mock_open, MagicMock, call
import plugins.market as market_module
import json
import re


class TestMarket:
    def setup_method(self, method):
        self.master_mock = MagicMock()
        self.market = market_module.market("SID", self.master_mock)

    def test_readproducts(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.market.products = {"stale_product": {}}
        self.market.aliases = {"stale_alias": "stale_product"}
        market_data = (
            "# comment\n"
            "\n"
            "user1   product1   2.50   1.00   description1\n"
            "user1   deposit,oldalias   1.00   0.00   reserved product\n"
            "user1   product3,deposit,ok   3.00   0.50   reserved aliases\n"
            "user1   badprice   nope   1.00   description\n"
            "user1   badspace   2.50   nope   description\n"
            "malformed\n"
        )
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            self.market.readproducts()
            print("hooi", self.market.products)
            assert "product1" in self.market.products
            assert "product3" in self.market.products
            assert self.market.products["product3"]["aliases"] == []
            assert self.market.products["product1"]["price"] == 2.50
            assert self.market.products["product1"]["description"] == "description1"
            assert "deposit" not in self.market.products
            assert "deposit" not in self.market.aliases
            assert "ok" not in self.market.aliases
            assert "badprice" not in self.market.products
            assert "badspace" not in self.market.products
            assert "stale_product" not in self.market.products
            assert "stale_alias" not in self.market.aliases

    def test_instances_do_not_share_state(self):
        self.market.products["product1"] = {}
        self.market.aliases["alias1"] = "product1"
        self.market.groups["group1"] = ["product1"]

        other = market_module.market("SID2", MagicMock())

        assert other.products == {}
        assert other.aliases == {}
        assert other.groups == {}

    def test_help(self):
        assert self.market.help() == {
            "addmarket": "Market: Add alias",
            "delmarket": "Market: Remove a product",
            "changemarket": "Market: Change Price",
            "market": "Market: Products",
        }

    def test_writeproducts(self):
        self.market.products = {
            "product1": {
                "aliases": ["alias1"],
                "price": 2.50,
                "space": 1.00,
                "description": "description1",
                "user": "user1",
            }
        }
        with patch("plugins.market._atomic_write") as mock_atomic_write:
            self.market.writeproducts()
        expected_product = "%-10s %-30s %7.2f %7.2f %s\n" % (
            "user1",
            "product1,alias1",
            2.50,
            1.00,
            "description1",
        )
        mock_atomic_write.assert_called_once_with(
            "data/revbank.market",
            [
                "#                               Price =\n",
                "# Seller   Barcode          Seller + Space  Description\n\n",
                expected_product,
            ],
        )
        assert self.market.products["product1"]["aliases"] == ["alias1"]

    def test_lookupprod(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.market.products = {"product1": "details1"}
        self.market.aliases = {"alias1": "product1", "deposit": "product1"}
        assert self.market.lookupprod("product1") == "product1"
        assert self.market.lookupprod("alias1") == "product1"
        assert self.market.lookupprod("deposit") is None
        assert self.market.lookupprod("unknown") is None

    def test_messageandbuttons(self):
        result = self.market.messageandbuttons("nextfunc", "numbers", "Test message")
        self.master_mock.donext.assert_called_with(self.market, "nextfunc")
        self.master_mock.send_message.assert_any_call(True, "message", "Test message")
        self.master_mock.send_message.assert_any_call(
            True, "buttons", json.dumps({"special": "numbers"})
        )
        assert result is True

    def test_savealias(self):
        self.market.products = {"product1": {"aliases": []}}
        self.market.aliasprod = "product1"
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            assert self.market.savealias("alias1")

    def test_savealias_abort_existing_and_invalid(self):
        self.market.products = {"product1": {"aliases": []}}
        self.market.aliases = {"alias1": "product1"}

        with patch.object(self.market, "readproducts"):
            assert (
                self.market.savealias("abort") is self.master_mock.callhook.return_value
            )
            self.master_mock.callhook.assert_called_with("abort", None)
            assert self.market.savealias("alias1") is True
            assert self.market.savealias("bad!") is True

    def test_savealias_valid_new_alias(self):
        self.market.products = {"product1": {"aliases": []}}
        self.market.aliasprod = "product1"

        with patch.object(self.market, "readproducts"), patch.object(
            self.market, "writeproducts"
        ):
            assert self.market.savealias("alias123") is True

        assert self.market.products["product1"]["aliases"] == ["alias123"]

    def test_savealias_rejects_command_alias(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.market.products = {"product1": {"aliases": []}}
        self.market.aliasprod = "product1"

        with patch.object(self.market, "readproducts"), patch.object(
            self.market, "writeproducts"
        ) as mock_writeproducts:
            assert self.market.savealias("deposit") is True

        mock_writeproducts.assert_not_called()
        assert self.market.products["product1"]["aliases"] == []
        self.master_mock.donext.assert_called_with(self.market, "savealias")

    def test_addalias(self):
        self.market.products = {"product1": {"aliases": []}}
        assert self.market.addalias("product1")
        self.market.aliasprod = "product1"
        assert self.market.addalias("unknownprod")

    def test_addalias_abort(self):
        assert self.market.addalias("abort") is self.master_mock.callhook.return_value
        self.master_mock.callhook.assert_called_with("abort", None)

    def test_setprice(self):
        self.market.products = {"product1": {"price": 2.5}}
        assert self.market.setprice("product1")
        self.market.priceprod = "product1"
        assert self.market.setprice("unknownprod")

    def test_setprice_abort(self):
        assert self.market.setprice("abort") is self.master_mock.callhook.return_value
        self.master_mock.callhook.assert_called_with("abort", None)

    def test_saveprice(self):
        self.market.priceprod = "product1"
        self.market.newprodprice = 3.0
        self.market.products = {"product1": {"price": 2.5, "aliases": []}}
        with patch.object(self.market, "readproducts"), patch.object(
            self.market, "writeproducts"
        ):
            self.market.saveprice("3.0")
            print(self.market.products)
            assert self.market.products["product1"]["price"] == 3.0

    def test_addproductgroup(self):
        self.market.newprod = "product1"
        self.market.newprodprice = 2.5
        self.market.newproddesc = "description"
        self.market.groups = {"group1": []}
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            assert self.market.addproductgroup("group1")

    def test_addproductprice(self):
        self.market.newprod = "product1"
        self.market.newproddesc = "description"
        assert self.market.addproductprice("2.5")

    def test_addproductdesc(self):
        self.market.newprod = "product1"
        assert self.market.addproductdesc("description")

    def test_addproduct(self):
        self.market.products = {}
        assert self.market.addproduct("product1")

    def test_input(self):
        self.market.products = {
            "product1": {
                "price": 2.5,
                "user": "user1",
                "description": "description",
                "space": 0.5,
            }
        }
        self.market.master = self.master_mock
        assert self.market.input("product1")

    def test_hook_abort(self):
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            assert self.market.hook_abort(None) is None

    def test_startup(self):
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            self.market.startup()
            assert "product1" in self.market.products

    def test_addalias_unknown_product(self):
        assert self.market.addalias("unknownprod")

    def test_setprice_unknown_product(self):
        assert self.market.setprice("unknownprod")

    def test_saveprice_invalid_price(self):
        self.market.priceprod = "product1"
        assert self.market.saveprice("invalid")

    def test_saveprice_abort_and_out_of_range(self):
        assert self.market.saveprice("abort") is self.master_mock.callhook.return_value
        self.master_mock.callhook.assert_called_with("abort", None)
        assert self.market.saveprice("0") is True

    def test_addproductgroup_short_group_name(self):
        self.market.newprod = "product1"
        self.market.newprodprice = 2.5
        self.market.newproddesc = "description"
        assert self.market.addproductgroup("sh")

    def test_addproductgroup_abort(self):
        assert (
            self.market.addproductgroup("abort")
            is self.master_mock.callhook.return_value
        )
        self.master_mock.callhook.assert_called_with("abort", None)

    def test_addproductgroup_new_group(self):
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            self.market.newprod = "product1"
            self.market.newprodprice = 2.5
            self.market.newproddesc = "description"
            self.market.groups = {"group": {}}
            self.market.writeproducts = MagicMock()
            assert self.market.addproductgroup("group1")
            assert "group1" in self.market.groups

    def test_delmarket_removes_product_and_aliases(self):
        market_data = (
            "user1 product1,alias1 2.50 1.00 description1\n"
            "user2 product2,alias2 3.50 0.50 description2\n"
        )
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            assert self.market.delmarket("alias1")

        assert "product1" not in self.market.products
        assert "alias1" not in self.market.aliases
        assert "product2" in self.market.products

    def test_addproductprice_invalid_price(self):
        self.market.newprod = "product1"
        self.market.newproddesc = "description"
        assert self.market.addproductprice("invalid")

    def test_addproductprice_abort_and_out_of_range(self):
        assert (
            self.market.addproductprice("abort")
            is self.master_mock.callhook.return_value
        )
        self.master_mock.callhook.assert_called_with("abort", None)
        assert self.market.addproductprice("1000") is True

    def test_addproductdesc_short_description(self):
        self.market.newprod = "product1"
        assert self.market.addproductdesc("sh")

    def test_addproductdesc_abort(self):
        assert (
            self.market.addproductdesc("abort")
            is self.master_mock.callhook.return_value
        )
        self.master_mock.callhook.assert_called_with("abort", None)

    def test_addproduct_existing_product(self):
        self.market.products = {"product1": {}}
        assert self.market.addproduct("product1")

    def test_addproduct_abort_and_invalid_name(self):
        assert self.market.addproduct("abort") is self.master_mock.callhook.return_value
        self.master_mock.callhook.assert_called_with("abort", None)
        assert self.market.addproduct("bad!") is True

    def test_addproduct_rejects_command_name(self):
        self.master_mock.help = {"deposit": "Deposit Money"}

        assert self.market.addproduct("deposit") is True

        assert self.market.newprod == ""
        self.master_mock.donext.assert_called_with(self.market, "addproduct")

    def test_input_unknown_product(self):
        self.market.products = {}
        assert not self.market.input("unknownprod")

    def test_input_market(self):
        self.market.products = {
            "market": {
                "price": 2.0,
                "user": "user1",
                "description": "reserved name",
                "space": 0.5,
            }
        }
        assert self.market.input("market")
        self.master_mock.receipt.add.assert_not_called()

    def test_input_market_lists_products(self):
        self.market.products = {
            "product1": {"description": "Description", "price": 2.0, "space": 0.5}
        }

        assert self.market.input("market")
        payload = self.master_mock.send_message.call_args[0][2]
        assert json.loads(payload)["custom"] == [
            {"text": "product1", "display": "Description", "right": "2.50 (0.50)"}
        ]

    def test_input_market_admin_commands(self):
        assert self.market.input("addmarket")
        self.master_mock.donext.assert_called_with(self.market, "addalias")

        self.master_mock.reset_mock()
        assert self.market.input("changemarket")
        self.master_mock.donext.assert_called_with(self.market, "setprice")

        self.master_mock.reset_mock()
        assert self.market.input("delmarket")
        self.master_mock.donext.assert_called_with(self.market, "delmarket")
