import unittest
from unittest.mock import Mock, patch, mock_open
import plugins.products as ProductsModule


class TestProducts(unittest.TestCase):
    def setUp(self):
        self.master_mock = Mock()
        self.products = ProductsModule.products("SID", self.master_mock)

    def test_readproducts(self):
        product_data = "# Group1\nproduct1,alias1 2.50 Description1\n# Group2\nproduct2 1.50 Description2\n"
        with patch("builtins.open", mock_open(read_data=product_data)):
            self.products.readproducts()
            self.assertIn("product1", self.products.products)
            self.assertIn("product2", self.products.products)
            self.assertIn("Group1", self.products.groups)
            self.assertIn("Group2", self.products.groups)

    def test_writeproducts(self):
        self.products.products = {
            "product1": {"aliases": ["alias1"], "price": 2.50, "description": "Description1", "group": "Group1"},
            "product2": {"aliases": [], "price": 1.50, "description": "Description2", "group": "Group2"}
        }
        self.products.groups = {"Group1": ["product1"], "Group2": ["product2"]}
        with patch("builtins.open", mock_open()) as mocked_file:
            self.products.writeproducts()
            mocked_file().write.assert_called()

    def test_lookupprod(self):
        self.products.products = {"product1": {}}
        self.products.aliases = {"alias1": "product1"}
        self.assertEqual(self.products.lookupprod("product1"), "product1")
        self.assertEqual(self.products.lookupprod("alias1"), "product1")
        self.assertIsNone(self.products.lookupprod("nonexistent"))

    def test_messageandbuttons(self):
        self.products.messageandbuttons("next_step", "buttons", "message")
        self.master_mock.donext.assert_called_with(self.products, "next_step")
        self.master_mock.send_message.assert_called_with(True, "message", "message")

    def test_startup(self):
        with patch.object(self.products, "readproducts") as mocked_readproducts:
            self.products.startup()
            mocked_readproducts.assert_called()
            self.assertEqual(self.products.times, 1)

    def test_savealias_valid_alias(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(self.products, "writeproducts"):
            result = self.products.savealias("alias1")
            self.assertTrue(result)
            self.assertIn("alias1", self.products.products["product1"]["aliases"])

    def test_savealias_invalid_alias(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"
        result = self.products.savealias("invalid alias")
        self.assertFalse(result)

    def test_addalias_existing_product(self):
        self.products.products = {"product1": {}}
        result = self.products.addalias("product1")
        self.assertTrue(result)

    def test_setprice_existing_product(self):
        self.products.products = {"product1": {}}
        result = self.products.setprice("product1")
        self.assertTrue(result)


    def test_saveprice_valid_price(self):
        self.products.products = {"product1": {}}
        self.products.priceprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(self.products, "writeproducts"):
            result = self.products.saveprice("10.0")
            self.assertTrue(result)
            self.assertEqual(self.products.products["product1"]["price"], 10.0)

    def test_saveprice_invalid_price(self):
        self.products.priceprod = "product1"
        result = self.products.saveprice("invalid")
        self.assertFalse(result)

    def test_addproductgroup_new_group(self):
        self.products.newprod = "product1"
        self.products.newprodprice = 2.5
        self.products.newproddesc = "description"
        self.products.groups = {}
        with patch.object(self.products, "readproducts"), patch.object(self.products, "writeproducts"):
            result = self.products.addproductgroup("group1")
            self.assertTrue(result)
            self.assertIn("product1", self.products.groups["group1"])

    def test_addproductgroup_existing_group(self):
        self.products.newprod = "product1"
        self.products.newprodprice = 2.5
        self.products.newproddesc = "description"
        self.products.groups = {"group1": []}
        with patch.object(self.products, "readproducts"), patch.object(self.products, "writeproducts"):
            result = self.products.addproductgroup("group1")
            self.assertTrue(result)
            self.assertIn("product1", self.products.groups["group1"])

    def test_addalias_nonexistent_product(self):
        with patch.object(self.products.master, "send_message"):
            self.products.addalias("nonexistent")
            self.products.master.send_message.assert_called_with(
                True, "message", "Unknown product;What product do you want to alias?"
            )
    def test_addalias_nonexistent_product(self):
        with patch.object(self.products.master, "send_message"):
            self.products.addalias("nonexistent")
            self.products.master.send_message.assert_called_with(
                True, "message", "Unknown product;What product do you want to alias?"
            )

    def test_setprice_nonexistent_product(self):
        with patch.object(self.products.master, "send_message"):
            self.products.setprice("nonexistent")
            self.products.master.send_message.assert_called_with(
                True, "message", "Unknown product;What product do you want change price?"
            )

    def test_savealias_valid_alias(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"
        with patch("builtins.open", mock_open()):
            assert self.products.savealias("alias1")
            assert "alias1" in self.products.products["product1"]["aliases"]
    
    def test_saveprice_valid_price(self):
        self.products.products = {"product1": {"price": 2.5}}
        self.products.priceprod = "product1"
        with patch("builtins.open", mock_open()):
            assert self.products.saveprice("3.0")
            assert self.products.products["product1"]["price"] == 3.0

