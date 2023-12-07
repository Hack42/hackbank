from unittest.mock import patch, mock_open, MagicMock
import plugins.market as market_module
import json
import re

class TestMarket:
    def setup_method(self, method):
        self.master_mock = MagicMock()
        self.market = market_module.market("SID", self.master_mock)


    def test_readproducts(self):
        market_data = "user1 product1 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            self.market.readproducts()
            print("hooi", self.market.products)
            assert "product1" in self.market.products
            assert self.market.products["product1"]["price"] == 2.50
            assert self.market.products["product1"]["description"] == "description1"

    def test_writeproducts(self):
        self.market.groups = {"group1": {"product1": {"aliases": ["alias1"], "price": 2.50, "description": "description1"}}}
        mo = mock_open()
        with patch("builtins.open", mo):
            self.market.writeproducts()
            mo.assert_called_with("data/revbank.market", "w", encoding="utf-8")
            handle = mo()
            expected_data = "\n"
            handle.write.assert_called_with(expected_data)
    def test_lookupprod(self):
        self.market.products = {"product1": "details1"}
        self.market.aliases = {"alias1": "product1"}
        assert self.market.lookupprod("product1") == "product1"
        assert self.market.lookupprod("alias1") == "product1"
        assert self.market.lookupprod("unknown") is None
    def test_messageandbuttons(self):
        result = self.market.messageandbuttons("nextfunc", "numbers", "Test message")
        self.master_mock.donext.assert_called_with(self.market, "nextfunc")
        self.master_mock.send_message.assert_any_call(True, "message", "Test message")
        self.master_mock.send_message.assert_any_call(True, "buttons", json.dumps({"special": "numbers"}))
        assert result is True

    def test_savealias(self):
        self.market.products = {"product1": {"aliases": []}}
        self.market.aliasprod = "product1"
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            assert self.market.savealias("alias1")

    def test_addalias(self):
        self.market.products = {"product1": {"aliases": []}}
        assert self.market.addalias("product1")
        self.market.aliasprod = "product1"
        assert self.market.addalias("unknownprod")
    def test_setprice(self):
        self.market.products = {"product1": {"price": 2.5}}
        assert self.market.setprice("product1")
        self.market.priceprod = "product1"
        assert self.market.setprice("unknownprod")

    def test_saveprice(self):
        self.market.priceprod = "product1"
        self.market.newprodprice = 3.0
        self.market.products = {"product1": {"price": 2.5}}
        market_data = "user1 product1,alias1,alias2 2.50 1.00 description1\n"
        mo = mock_open(read_data=market_data)
        with patch("builtins.open", mo):
            self.market.saveprice("3.0")
            assert self.market.products["product1"]["price"] == 3.0

    def test_addproductgroup(self):
        self.market.newprod = "product1"
        self.market.newprodprice = 2.5
        self.market.newproddesc = "description"
        self.market.groups = {"group1": {}}
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
        self.market.products = {"product1": {"price": 2.5, "user": "user1", "description": "description", "space": 0.5}}
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
    def test_addproductgroup_short_group_name(self):
        self.market.newprod = "product1"
        self.market.newprodprice = 2.5
        self.market.newproddesc = "description"
        assert self.market.addproductgroup("sh")

    def test_addproductgroup_new_group(self):
        self.market.newprod = "product1"
        self.market.newprodprice = 2.5
        self.market.newproddesc = "description"
        self.market.groups = {}
        assert self.market.addproductgroup("group1")
        assert "group1" in self.market.groups

    def test_addproductprice_invalid_price(self):
        self.market.newprod = "product1"
        self.market.newproddesc = "description"
        assert self.market.addproductprice("invalid")

    def test_addproductdesc_short_description(self):
        self.market.newprod = "product1"
        assert self.market.addproductdesc("sh")

    def test_addproduct_existing_product(self):
        self.market.products = {"product1": {}}
        assert self.market.addproduct("product1")

    def test_input_unknown_product(self):
        self.market.products = {}
        assert not self.market.input("unknownprod")


    def test_input_market(self):
        assert self.market.input("market")
