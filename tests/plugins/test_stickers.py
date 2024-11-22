import io
import base64

from unittest.mock import Mock, call
from unittest.mock import patch

from plugins.stickers import stickers


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
    master.products.products.get.side_effect = (
        lambda k: product_data if k == product_alias else None
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
