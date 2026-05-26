import unittest
from unittest.mock import Mock, patch, mock_open, call
import plugins.products as ProductsModule


class TestProducts(unittest.TestCase):
    def setUp(self):
        self.master_mock = Mock()
        self.products = ProductsModule.products("SID", self.master_mock)

    def test_readproducts(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.products.products = {"stale_product": {}}
        self.products.aliases = {"stale_alias": "stale_product"}
        self.products.groups = {"StaleGroup": ["stale_product"]}
        product_data = (
            "\n"
            "# Group1\n"
            "product1,alias1   2.50   Description1\n"
            "deposit,oldalias   1.00   Reserved product\n"
            "product3,deposit,ok   3.00   Reserved aliases\n"
            "\n"
            "# Group2\n"
            "product2\t1.50\tDescription2\n"
            "badprice nope Bad description\n"
            "#\n"
            "malformed\n"
        )
        with patch("builtins.open", mock_open(read_data=product_data)):
            self.products.readproducts()
            self.assertIn("product1", self.products.products)
            self.assertIn("product2", self.products.products)
            self.assertIn("product3", self.products.products)
            self.assertEqual(self.products.products["product3"]["aliases"], [])
            self.assertNotIn("badprice", self.products.products)
            self.assertNotIn("deposit", self.products.products)
            self.assertNotIn("deposit", self.products.aliases)
            self.assertNotIn("ok", self.products.aliases)
            self.assertIn("Group1", self.products.groups)
            self.assertIn("Group2", self.products.groups)
            self.assertNotIn("stale_product", self.products.products)
            self.assertNotIn("stale_alias", self.products.aliases)
            self.assertNotIn("StaleGroup", self.products.groups)

    def test_help(self):
        self.assertEqual(
            self.products.help(),
            {
                "aliasproduct": "Add alias to product",
                "addproduct": "Add new product",
                "setprice": "Change the price of a product",
            },
        )

    def test_writeproducts(self):
        self.products.products = {
            "product1": {
                "aliases": ["alias1"],
                "price": 2.50,
                "description": "Description1",
                "group": "Group1",
            },
            "product2": {
                "aliases": [],
                "price": 1.50,
                "description": "Description2",
                "group": "Group2",
            },
        }
        self.products.groups = {"Group1": ["product1"], "Group2": ["product2"]}
        with patch("plugins.products._atomic_write") as mock_atomic_write:
            self.products.writeproducts()
        mock_atomic_write.assert_called_once_with(
            "data/revbank.products",
            [
                "# Group1\n",
                "%-58s %7.2f  %s\n"
                % ("product1,alias1", 2.50, "Description1"),
                "\n",
                "# Group2\n",
                "%-58s %7.2f  %s\n" % ("product2", 1.50, "Description2"),
                "\n",
            ],
        )
        self.assertEqual(self.products.products["product1"]["aliases"], ["alias1"])
        self.assertEqual(self.products.products["product2"]["aliases"], [])

    def test_lookupprod(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.products.products = {"product1": {}}
        self.products.aliases = {"alias1": "product1", "deposit": "product1"}
        self.assertEqual(self.products.lookupprod("product1"), "product1")
        self.assertEqual(self.products.lookupprod("alias1"), "product1")
        self.assertIsNone(self.products.lookupprod("deposit"))
        self.assertIsNone(self.products.lookupprod("nonexistent"))

    def test_messageandbuttons(self):
        self.products.messageandbuttons("next_step", "buttons", "message")
        self.master_mock.donext.assert_called_with(self.products, "next_step")
        assert self.products.master.send_message.call_args_list == [
            call(True, "message", "message"),
            call(True, "buttons", '{"special": "buttons"}'),
        ]

    def test_startup(self):
        with patch.object(self.products, "readproducts") as mocked_readproducts:
            self.products.startup()
            mocked_readproducts.assert_called()
            self.assertEqual(self.products.times, 1)

    def test_hook_abort(self):
        with patch.object(self.products, "startup") as mocked_startup:
            self.products.hook_abort(None)
            mocked_startup.assert_called_once()

    def test_savealias_valid_alias_original(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            result = self.products.savealias("alias1")
            self.assertTrue(result)
            self.assertIn("alias1", self.products.products["product1"]["aliases"])

    def test_savealias_invalid_alias(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            result = self.products.savealias("invalid alias")
            assert self.products.master.send_message.call_args_list == [
                call(
                    True,
                    "message",
                    "only [A-z0-9] is allowed in any alias and it should be at least 4 chars long",
                ),
                call(True, "buttons", '{"special": "keyboard"}'),
            ]
            self.assertTrue(result)

    def test_addalias_existing_product(self):
        self.products.products = {"product1": {}}
        result = self.products.addalias("product1")
        self.assertTrue(result)

    def test_setprice_existing_product(self):
        self.products.products = {"product1": {}}
        result = self.products.setprice("product1")
        self.assertTrue(result)

    def test_saveprice_invalid_price(self):
        self.products.priceprod = "product1"
        result = self.products.saveprice("invalid")
        self.assertTrue(result)

    def test_addproductgroup_new_group(self):
        self.products.newprod = "product1"
        self.products.newprodprice = 2.5
        self.products.newproddesc = "description"
        self.products.groups = {}
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            result = self.products.addproductgroup("group1")
            self.assertTrue(result)
            self.assertIn("product1", self.products.groups["group1"])

    def test_addproductgroup_existing_group(self):
        self.products.newprod = "product1"
        self.products.newprodprice = 2.5
        self.products.newproddesc = "description"
        self.products.groups = {"group1": []}
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            result = self.products.addproductgroup("group1")
            self.assertTrue(result)
            self.assertIn("product1", self.products.groups["group1"])

    def test_addalias_nonexistent_product_message_only(self):
        with patch.object(self.products.master, "send_message"):
            self.products.addalias("nonexistent")
            self.products.master.send_message.assert_any_call(
                True, "message", "Unknown product;What product do you want to alias?"
            )

    def test_addalias_nonexistent_product(self):
        with patch.object(self.products.master, "send_message"):
            self.products.addalias("nonexistent")
            assert self.products.master.send_message.call_args_list == [
                call(
                    True,
                    "message",
                    "Unknown product;What product do you want to alias?",
                ),
                call(True, "buttons", '{"special": "products"}'),
            ]

    def test_setprice_nonexistent_product(self):
        with patch.object(self.products.master, "send_message"):
            self.products.setprice("nonexistent")
            assert self.products.master.send_message.call_args_list == [
                call(
                    True,
                    "message",
                    "Unknown product;What product do you want change price?",
                ),
                call(True, "buttons", '{"special": "products"}'),
            ]

    def test_savealias_valid_alias(self):
        self.products.groups = {"Group1": ["product1"]}
        self.products.products = {
            "product1": {"aliases": [], "price": 42, "description": "aa"}
        }
        self.products.aliasprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            assert self.products.savealias("alias2")
            assert "alias2" in self.products.products["product1"]["aliases"]

    def test_saveprice_valid_price(self):
        self.products.products = {"product1": {"price": 2.5}}
        self.products.priceprod = "product1"
        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ):
            assert self.products.saveprice("3.0")
            print("hooi", self.products.products)
            assert self.products.products["product1"]["price"] == 3.0

    def test_abort_paths_call_abort_hook(self):
        with patch.object(self.products, "readproducts"):
            for method_name in (
                "savealias",
                "addalias",
                "setprice",
                "saveprice",
                "addproductgroup",
                "addproductprice",
                "addproductdesc",
                "addproduct",
            ):
                self.master_mock.reset_mock()
                result = getattr(self.products, method_name)("abort")
                self.master_mock.callhook.assert_called_with("abort", None)
                assert result == self.master_mock.callhook.return_value

    def test_savealias_existing_alias(self):
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliases = {"alias1": "product1"}
        with patch.object(self.products, "readproducts"):
            assert self.products.savealias("alias1")
        self.master_mock.donext.assert_called_with(self.products, "savealias")

    def test_savealias_rejects_command_alias(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.products.products = {"product1": {"aliases": []}}
        self.products.aliasprod = "product1"

        with patch.object(self.products, "readproducts"), patch.object(
            self.products, "writeproducts"
        ) as mock_writeproducts:
            assert self.products.savealias("deposit")

        mock_writeproducts.assert_not_called()
        assert self.products.products["product1"]["aliases"] == []
        self.master_mock.donext.assert_called_with(self.products, "savealias")

    def test_saveprice_out_of_range(self):
        self.products.products = {"product1": {"price": 2.5}}
        self.products.priceprod = "product1"
        assert self.products.saveprice("1000")
        assert self.master_mock.send_message.call_args_list == [
            call(True, "message", "Price should be between 0 and 1000"),
            call(True, "buttons", '{"special": "numbers"}'),
        ]

    def test_addproductgroup_short_name(self):
        self.products.groups = {"group1": []}
        assert self.products.addproductgroup("abc")
        self.master_mock.donext.assert_called_with(self.products, "addproductgroup")
        assert self.master_mock.send_message.call_args_list == [
            call(True, "message", "Too short,what productgroup to add the product to?"),
            call(
                True,
                "buttons",
                '{"special": "custom", "custom": [{"text": "group1", "display": "group1"}]}',
            ),
        ]

    def test_addproductprice_valid_and_invalid(self):
        self.products.groups = {"group1": []}
        self.products.newprod = "product1"
        assert self.products.addproductprice("2.5")
        assert self.products.newprodprice == 2.5
        self.master_mock.donext.assert_called_with(self.products, "addproductgroup")

        self.master_mock.reset_mock()
        assert self.products.addproductprice("1000")
        self.master_mock.donext.assert_called_with(self.products, "addproductprice")

        self.master_mock.reset_mock()
        assert self.products.addproductprice("not-a-number")
        self.master_mock.donext.assert_called_with(self.products, "addproductprice")

    def test_addproductdesc_short_and_valid(self):
        self.products.newprod = "product1"
        assert self.products.addproductdesc("abc")
        self.master_mock.donext.assert_called_with(self.products, "addproductdesc")

        self.master_mock.reset_mock()
        assert self.products.addproductdesc("valid description")
        assert self.products.newproddesc == "valid description"
        self.master_mock.donext.assert_called_with(self.products, "addproductprice")

    def test_addproduct_existing_invalid_and_valid(self):
        self.products.products = {"product1": {}}
        assert self.products.addproduct("product1")
        self.master_mock.donext.assert_called_with(self.products, "addproduct")

        self.master_mock.reset_mock()
        assert self.products.addproduct("bad name")
        self.master_mock.donext.assert_called_with(self.products, "addproduct")

        self.master_mock.reset_mock()
        assert self.products.addproduct("product2")
        assert self.products.newprod == "product2"
        self.master_mock.donext.assert_called_with(self.products, "addproductdesc")

    def test_addproduct_rejects_command_name(self):
        self.master_mock.help = {"deposit": "Deposit Money"}

        assert self.products.addproduct("deposit")

        assert self.products.newprod == ""
        self.master_mock.donext.assert_called_with(self.products, "addproduct")

    def test_input_product_commands_and_multiplier(self):
        self.master_mock.help = {"deposit": "Deposit Money"}
        self.products.products = {
            "product1": {"price": 2.5, "description": "Description1", "aliases": []},
            "deposit": {"price": 1.0, "description": "Reserved", "aliases": []},
        }
        self.products.aliases = {"deposit": "product1"}

        assert self.products.input("2*")
        assert self.products.times == 2

        assert self.products.input("product1")
        self.master_mock.receipt.add.assert_called_with(
            True, 2.5, "Description1", 2.0, None, "product1"
        )
        assert self.products.times == 1

        self.master_mock.reset_mock()
        assert self.products.input("deposit") is None
        self.master_mock.receipt.add.assert_not_called()

        for command, nextcall in (
            ("aliasproduct", "addalias"),
            ("addproduct", "addproduct"),
            ("setprice", "setprice"),
        ):
            self.master_mock.reset_mock()
            assert self.products.input(command)
            self.master_mock.donext.assert_called_with(self.products, nextcall)

        assert self.products.input("0*") is None
        assert self.products.input("not-a-number*") is None
