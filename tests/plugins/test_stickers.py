import io
import base64

from unittest.mock import Mock, call
from unittest.mock import patch

from plugins.stickers import stickers


def test_uses_configured_printer_host():
    with patch(
        "plugins.stickers.config_get",
        return_value={
            "model": "QL-820NWB",
            "host": "printer.example.test",
            "port": 9101,
        },
    ):
        sticky = stickers("main", Mock())

    assert sticky.MODEL == "QL-820NWB"
    assert sticky.PRINTER == "tcp://printer.example.test:9101"


def test_uses_configured_printer_identifier():
    with patch(
        "plugins.stickers.config_get",
        return_value={
            "model": "QL-710W",
            "identifier": "tcp://printer-id.example.test:9100",
        },
    ):
        sticky = stickers("main", Mock())

    assert sticky.PRINTER == "tcp://printer-id.example.test:9100"


@patch("builtins.open")
@patch("plugins.stickers.brother_ql.backends.helpers")
def test_eigendom(_cups, _open):
    master = Mock()
    sticky = stickers("main", master)
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )

    # Call the input method with 'eigendom'
    result = sticky.input("eigendom")

    # Assert that the input method returns True
    assert result == True

    # Assert that donext is called with the correct arguments
    sticky.master.donext.assert_called_with(sticky, "eigendomcount")

    expected_calls = [
        call(True, "message", "Who are you?"),
        call(
            True, "buttons", '{"special": "accounts"}'
        ),  # Make sure the JSON string matches exactly
    ]

    # Assert that send_message is called with the expected arguments
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.eigendomcount("BugBlue")
    assert result == True
    sticky.master.donext.assert_called_with(sticky, "eigendomnum")
    expected_calls = [
        call(True, "message", "How many do you want?"),
        call(True, "buttons", '{"special": "numbers"}'),
    ]
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.eigendomnum("1")
    assert result == True
    expected_calls = []
    assert sticky.master.send_message.call_args_list == expected_calls
    assert sticky.copies == 1
    assert sticky.name == "BugBlue"


@patch("builtins.open")
@patch("plugins.stickers.brother_ql.backends.helpers")
def test_foodlabel(_cups, _open):
    master = Mock()
    sticky = stickers("main", master)
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )

    # Call the input method with 'eigendom'
    result = sticky.input("foodlabel")

    # Assert that the input method returns True
    assert result == True

    # Assert that donext is called with the correct arguments
    sticky.master.donext.assert_called_with(sticky, "foodname")

    expected_calls = [
        call(True, "message", "Who are you?"),
        call(
            True, "buttons", '{"special": "accounts"}'
        ),  # Make sure the JSON string matches exactly
    ]

    # Assert that send_message is called with the expected arguments
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.foodname("BugBlue")
    assert result == True
    sticky.master.donext.assert_called_with(sticky, "foodnum")
    expected_calls = [
        call(True, "message", "How many do you want?"),
        call(True, "buttons", '{"special": "numbers"}'),
    ]
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.foodnum("1")
    assert result == True
    expected_calls = []
    assert sticky.master.send_message.call_args_list == expected_calls
    assert sticky.copies == 1
    assert sticky.name == "BugBlue"


@patch("builtins.open")
@patch("plugins.stickers.brother_ql.backends.helpers")
def test_thtlabel(_cups, _open):
    master = Mock()
    sticky = stickers("main", master)
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )

    # Call the input method with 'eigendom'
    result = sticky.input("thtlabel")

    # Assert that the input method returns True
    assert result == True

    # Assert that donext is called with the correct arguments
    sticky.master.donext.assert_called_with(sticky, "thtname")

    expected_calls = [
        call(True, "message", "What is the date?"),
        call(True, "buttons", '{"special": "accounts"}'),
    ]

    # Assert that send_message is called with the expected arguments
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.thtname("BugBlue")
    assert result == True
    sticky.master.donext.assert_called_with(sticky, "thtnum")
    expected_calls = [
        call(True, "message", "How many do you want?"),
        call(True, "buttons", '{"special": "numbers"}'),
    ]
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.thtnum("1")
    assert result == True
    expected_calls = []
    assert sticky.master.send_message.call_args_list == expected_calls
    assert sticky.copies == 1
    assert sticky.datum == "BugBlue"


@patch("builtins.open")
@patch("plugins.stickers.brother_ql.backends.helpers")
def test_barcode(_cups, _open):
    master = Mock()
    product_alias = "testproduct"
    master.products.lookupprod.return_value = product_alias

    # Make master.products.products behave like a dictionary
    product_data = {
        "aliases": ["1234"],
        "price": 10.0,
        "description": "Test Description",
    }
    master.products.products = Mock()
    master.products.products.get.side_effect = lambda k: (
        product_data if k == product_alias else None
    )

    sticky = stickers("main", master)
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )

    # Call the input method with 'barcode'
    result = sticky.input("barcode")
    assert result == True

    # Assert that donext is called with the correct arguments
    sticky.master.donext.assert_called_with(sticky, "barcodecount")

    # Prepare expected calls to send_message
    expected_calls = [
        call(True, "message", "What product do you want a barcode for?"),
        call(True, "buttons", '{"special": "products"}'),
    ]

    # Assert that send_message is called with the expected arguments
    assert sticky.master.send_message.call_args_list == expected_calls

    # Now test the barcodecount method
    result = sticky.barcodecount("testproduct")
    assert result == True
    sticky.master.donext.assert_called_with(sticky, "barcodenum")
    expected_calls = [
        call(True, "message", "What product do you want a barcode for?"),
        call(True, "buttons", '{"special": "products"}'),
        call(True, "message", "How many do you want?"),
        call(True, "buttons", '{"special": "numbers"}'),
    ]
    assert sticky.master.send_message.call_args_list == expected_calls

    sticky.master = Mock()
    result = sticky.barcodenum("1")
    assert result == True
    expected_calls = []
    assert sticky.master.send_message.call_args_list == expected_calls
    assert sticky.copies == 1
    assert sticky.barcode == "1234"


def test_stickers_generic():
    master = Mock()
    sticky = stickers("main", master)

    # Call the input method with 'eigendom'
    result = sticky.input("0.01")

    # Assert that the input method returns True
    assert result == None


def test_help_and_stickers_menu():
    master = Mock()
    sticky = stickers("main", master)

    assert sticky.help() == {"stickers": "All sticker commands"}
    assert sticky.input("stickers")
    assert master.send_message.call_args_list == [
        call(
            True,
            "buttons",
            '{"special": "custom", "custom": [{"text": "barcode", "display": "Barcode label"}, {"text": "eigendom", "display": "Property label"}, {"text": "eigendomlarge", "display": "Large Property label"}, {"text": "foodlabel", "display": "Food label"}, {"text": "thtlabel", "display": "THT label"}, {"text": "toollabel", "display": "Tool label"}]}',
        ),
        call(True, "message", "Please select a command"),
    ]


def test_toollabel_flow():
    master = Mock()
    sticky = stickers("main", master)

    assert sticky.input("toollabel")
    sticky.master.donext.assert_called_with(sticky, "toolname")
    assert sticky.master.send_message.call_args_list == [
        call(True, "message", "What is the Toolname?")
    ]

    sticky.master = Mock()
    assert sticky.toolname("TOOL42")
    sticky.master.donext.assert_called_with(sticky, "toolnum")


@patch("plugins.stickers.brother_ql.backends.helpers")
def test_toolnum_prints_label(_cups):
    master = Mock()
    sticky = stickers("main", master)
    sticky.name = "TOOL42"

    assert sticky.toolnum("1")
    assert sticky.copies == 1


@patch("plugins.stickers.brother_ql.backends.helpers")
def test_toolprint_binary_qrcode_path(_cups):
    sticky = stickers("main", Mock())
    sticky.name = "tool-42"
    sticky.copies = 1

    sticky.toolprint()


@patch("plugins.stickers.brother_ql.backends.helpers")
def test_direct_print_methods_cover_binary_and_food_paths(_cups):
    master = Mock()
    sticky = stickers("main", master)
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )
    sticky.copies = 1
    sticky.barcode = "lowercase"
    sticky.name = "BugBlue"
    sticky.price = "EUR 1.00"
    sticky.description = "Description"
    sticky.datum = "2026-05-19"

    sticky.barcodeprint()
    sticky.foodprint()
    sticky.thtprint()


def test_barcodecount_unknown_and_shortest_alias_fallback():
    master = Mock()
    master.products.lookupprod.return_value = None
    sticky = stickers("main", master)

    assert sticky.barcodecount("unknown")
    sticky.master.donext.assert_called_with(sticky, "barcodecount")

    master = Mock()
    master.products.lookupprod.return_value = "product1"
    master.products.products.get.return_value = {
        "aliases": ["longalias", "shrt"],
        "price": 2.5,
        "description": "Description",
    }
    sticky = stickers("main", master)

    assert sticky.barcodecount("product1")
    assert sticky.barcode == "shrt"


def test_number_and_name_abort_and_invalid_paths():
    master = Mock()
    sticky = stickers("main", master)

    for method_name in (
        "barcodenum",
        "eigendomnum",
        "foodnum",
        "thtnum",
        "toolnum",
        "eigendomcount",
        "foodname",
        "thtname",
        "toolname",
    ):
        master.reset_mock()
        assert getattr(sticky, method_name)("abort") == master.callhook.return_value
        master.callhook.assert_called_with("abort", None)

    for method_name in ("barcodenum", "eigendomnum", "foodnum", "thtnum", "toolnum"):
        sticky.master = Mock()
        assert getattr(sticky, method_name)("0")
        sticky.master.donext.assert_called_with(sticky, method_name)

        sticky.master = Mock()
        assert getattr(sticky, method_name)("not-a-number")
        sticky.master.donext.assert_called_with(sticky, method_name)


def test_large_property_label_sets_large_flag():
    master = Mock()
    sticky = stickers("main", master)

    assert sticky.input("eigendomlarge")
    assert sticky.large is True
    sticky.master.donext.assert_called_with(sticky, "eigendomcount")


@patch("plugins.stickers.brother_ql.backends.helpers")
def test_eigendomprint_large_options(_cups):
    sticky = stickers("main", Mock())
    sticky.LOGOFILE = io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
        )
    )
    sticky.name = "BugBlue"
    sticky.copies = 1
    sticky.large = True

    sticky.eigendomprint()


def test_startup_is_noop():
    sticky = stickers("main", Mock())
    assert sticky.startup() is None
