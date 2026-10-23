import base64
from io import BytesIO
from unittest.mock import patch

from PIL import Image
import pytest

from epc_payment import create_payment
import epc_payment


def test_epc_payload_contains_exact_payment_fields_and_scannable_png():
    with patch(
        "epc_payment.pyqrcode.create", wraps=epc_payment.pyqrcode.create
    ) as create:
        payment = create_payment("test_user", "12.34")
    assert create.call_args.args[0].decode("utf-8").split("\n") == [
        "BCD",
        "002",
        "1",
        "SCT",
        "",
        "Hack42",
        "NL43ABNA0136777643",
        "EUR12.34",
        "",
        "",
        "test_user",
    ]
    assert create.call_args.kwargs["error"] == "M"
    assert payment["amount"] == "12.34"
    assert payment["reference"] == "test_user"
    with Image.open(BytesIO(base64.b64decode(payment["qr"].split(",")[1]))) as image:
        assert image.width == image.height
        assert image.width >= 300
        assert image.getpixel((0, 0)) != image.getpixel((32, 32))


@pytest.mark.parametrize(
    "amount", ["0", "-1", "0.001", "12.345", "NaN", "Infinity", "1000000000"]
)
def test_epc_rejects_invalid_or_fractional_cent_amounts(amount):
    with pytest.raises(ValueError):
        create_payment("test_user", amount)


@pytest.mark.parametrize(
    "user", ["", "x" * 141, "test\nuser", "test\ruser", "test\x00user"]
)
def test_epc_rejects_invalid_reference(user):
    with pytest.raises(ValueError):
        create_payment(user, "1.00")


@pytest.mark.parametrize("iban", ["not-an-iban", "NL00ABNA0136777643"])
def test_epc_rejects_invalid_bank_configuration(iban):
    with patch("epc_payment.config_get", return_value={"name": "Hack42", "iban": iban}):
        with pytest.raises(ValueError):
            create_payment("test_user", "1.00")


def test_epc_rejects_oversized_utf8_payload():
    with pytest.raises(ValueError, match="331"):
        create_payment("\u00e9" * 140, "12.34")
