from unittest.mock import Mock, patch, mock_open, call
import plugins.stock as stock_module
import json


def test_stock_constructor():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    assert stock.SID == "SID"
    assert stock.master == master_mock


def test_stock_help():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    expected_help = {
        "inkoop": "Report buying products",
        "voorraad": "Set stock of a product",
    }
    assert stock.help() == expected_help


def test_stock_addstock():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.stock = {"product1": 15}

    with patch.object(stock, "readstock"), patch.object(stock, "writestock"):
        stock.addstock("product1", 5)
        assert stock.stock["product1"] == 20


def test_stock_setstock():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    with patch.object(stock, "readstock"), patch.object(stock, "writestock"):
        stock.setstock("product1", 15)
        assert stock.stock["product1"] == 15
        master_mock.send_message.assert_called_with(
            True, "stock/product1", json.dumps(15)
        )


def test_stock_hook_checkout():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.stock = {"product1": 20}
    master_mock.receipt = Mock(receipt=[{"product": "product1", "count": 1}])
    master_mock.products = Mock(products={"product1": "data"})

    with patch.object(stock, "readstock"), patch.object(stock, "writestock"):
        stock.hook_checkout(None)
        assert stock.stock["product1"] == 19


def test_stock_voorraad():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value="product1"))

    with patch.object(stock, "voorraad_amount"), patch.object(stock, "master"):
        assert stock.voorraad("product1") == True
        stock.master.donext.assert_called_with(stock, "voorraad_amount")


def test_stock_inkoop():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value="product1"))

    with patch.object(stock, "inkoop_amount"), patch.object(stock, "master"):
        assert stock.inkoop("product1") == True
        stock.master.donext.assert_called_with(stock, "inkoop_amount")


def test_stock_voorraad_amount_valid():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    with patch.object(stock, "setstock"):
        assert stock.voorraad_amount("10") == True
        stock.setstock.assert_called_with("product1", 10)


def test_stock_inkoop_amount_valid():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    with patch.object(stock, "addstock"):
        assert stock.inkoop_amount("10") == True
        stock.addstock.assert_called_with("product1", 10)


def test_stock_hook_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    with patch.object(stock, "startup"):
        stock.hook_abort(None)
        stock.startup.assert_called_with()


def test_stock_startup():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    with patch.object(stock, "readstock"):
        stock.startup()
        stock.readstock.assert_called_with()


def test_stock_readstock():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock_data = "product1 10\nproduct2 20"
    stock_alias_data = "alias1 product1 2\nalias2 product2 3"

    def custom_mock_open_read(filename, *args, **kwargs):
        if filename == "data/revbank.stock":
            return mock_open(read_data=stock_data)()
        elif filename == "data/revbank.stockalias":
            return mock_open(read_data=stock_alias_data)()

    with patch("builtins.open", side_effect=custom_mock_open_read):
        stock.readstock()
        assert stock.stock == {"product1": 10, "product2": 20}
        assert stock.stockalias == {
            "alias1": {"prod": "product1", "multi": 2},
            "alias2": {"prod": "product2", "multi": 3},
        }


def test_stock_writestock():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.stock = {"product1": 10, "product2": 20}

    def custom_mock_open_write(filename, *args, **kwargs):
        return mock_open()()

    with patch("builtins.open", side_effect=custom_mock_open_write) as mock_file:
        stock.writestock()
        mock_file.assert_called_with("data/revbank.stock", "w", encoding="utf-8")


def test_stock_input_voorraad():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    stock.input("voorraad")

    master_mock.donext.assert_called_with(stock, "voorraad")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "What product to set the stock?"),
            call(True, "buttons", json.dumps({"special": "products"})),
        ]
    )


def test_stock_input_inkoop():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    stock.input("inkoop")

    master_mock.donext.assert_called_with(stock, "inkoop")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "What product did you buy?"),
            call(True, "buttons", json.dumps({"special": "products"})),
        ]
    )


def test_stock_voorraad_amount_not_a_number():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("not_a_number") == True
    master_mock.donext.assert_called_with(stock, "voorraad_amount")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Not a number, how much product1 is in stock"),
            call(True, "buttons", json.dumps({"special": "numbers"})),
        ]
    )


def test_stock_voorraad_amount_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_stock_voorraad_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value=None))

    assert stock.voorraad("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_stock_inkoop_amount_too_large_number():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.inkoop_amount("5000") == True
    master_mock.donext.assert_called_with(stock, "inkoop_amount")
    print(master_mock.send_message.call_args_list)
    master_mock.send_message.assert_has_calls(
        [
            call(
                True,
                "message",
                "Please enter a number between 1 and 4999, how much product1 did you buy?",
            ),
            call(True, "buttons", '{"special": "numbers"}'),
        ]
    )


def test_stock_inkoop_amount_not_a_number():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.inkoop_amount("not_a_number") == True
    master_mock.donext.assert_called_with(stock, "inkoop_amount")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Not a number, how much product1 did you buy?"),
            call(True, "buttons", '{"special": "numbers"}'),
        ]
    )


def test_stock_inkoop_amount_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.inkoop_amount("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_stock_inkoop_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value=None))

    assert stock.inkoop("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_stock_inkoop_unknown_product():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value=None))

    assert stock.inkoop("unknown_product") == True
    master_mock.donext.assert_called_with(stock, "inkoop")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Unknown Product, what product did you buy?"),
            call(True, "buttons", '{"special": "products"}'),
        ]
    )


def test_stock_input_unhandled_command():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    assert stock.input("unhandled_command") is None


def test_stock_voorraad_amount_valid():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("10") == True
    master_mock.donext.assert_called_with(stock, "voorraad_amount")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Not a number, how much product1 is in stock"),
            call(True, "buttons", '{"special": "numbers"}'),
        ]
    )


def test_stock_voorraad_amount_too_large_number():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("5000") == True
    master_mock.donext.assert_called_with(stock, "voorraad_amount")
    master_mock.send_message.assert_has_calls(
        [
            call(
                True,
                "message",
                "Please enter a number between 0 and 4999, how much product1 is in stock?",
            ),
            call(True, "buttons", '{"special": "numbers"}'),
        ]
    )


def test_stock_voorraad_amount_not_a_number():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("not_a_number") == True
    master_mock.donext.assert_called_with(stock, "voorraad_amount")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Not a number, how much product1 is in stock"),
            call(True, "buttons", '{"special": "numbers"}'),
        ]
    )


def test_stock_voorraad_amount_abort():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    assert stock.voorraad_amount("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_stock_voorraad_unknown_product():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value=None))

    assert stock.voorraad("unknown_product") == True
    master_mock.donext.assert_called_with(stock, "voorraad")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Unknown Product, what product to set the stock?"),
            call(True, "buttons", '{"special": "products"}'),
        ]
    )


def test_stock_inkoop_unknown_product():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    master_mock.products = Mock(lookupprod=Mock(return_value=None))

    assert stock.inkoop("unknown_product") == True
    master_mock.donext.assert_called_with(stock, "inkoop")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Unknown Product, what product did you buy?"),
            call(True, "buttons", '{"special": "products"}'),
        ]
    )


def test_stock_hook_checkout_no_product():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.stock = {}  # Reset the stock
    master_mock.receipt = Mock(receipt=[{"product": "product1", "count": 1}])
    master_mock.products = Mock(products={})

    with patch.object(stock, "readstock"), patch.object(stock, "writestock"):
        stock.hook_checkout(None)
        # Verify stock is not modified
        assert "product1" not in stock.stock


def test_stock_startup():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)

    with patch.object(stock, "readstock"):
        stock.startup()
        stock.readstock.assert_called()
        for prod, product in stock.stock.items():
            master_mock.send_message.assert_called_with(
                True, "stock/" + prod, json.dumps(product)
            )


def test_stock_hook_checkout_error_handling():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.stock = {"product1": 10}
    master_mock.receipt = Mock(receipt=[{"product": "product1", "count": 1}])
    master_mock.products = Mock(products={"product1": "data"})
    stock.stockalias = {"product1": {"prod": "nonexistent", "multi": 1}}

    with patch.object(stock, "readstock"), patch.object(stock, "writestock"):
        stock.hook_checkout(None)
        # Verify that no change in stock occurs for non-existent alias product
        assert stock.stock["product1"] == 10


def test_stock_voorraad_amount_error_handling():
    master_mock = Mock()
    stock = stock_module.stock("SID", master_mock)
    stock.prod = "product1"

    with patch.object(stock, "setstock", side_effect=Exception("Set stock error")):
        assert stock.voorraad_amount("1000") == True
        # Check that error handling branches are covered
        master_mock.send_message.assert_has_calls(
            [
                call(True, "message", "Not a number, how much product1 is in stock"),
                call(True, "buttons", '{"special": "numbers"}'),
            ]
        )
