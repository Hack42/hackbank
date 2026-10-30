"""EPC069-12 payment requests, rendered locally without external services."""

import base64
from decimal import Decimal
from io import BytesIO
import re

import pyqrcode

from config import config_get


def create_payment(reference, amount):
    settings = config_get("deposit", "epc", default={})
    name = settings["name"]
    iban = settings["iban"].replace(" ", "").upper()
    for value, limit in ((name, 70), (reference, 140)):
        if not isinstance(value, str) or not 1 <= len(value) <= limit:
            raise ValueError("Invalid EPC recipient or reference length")
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("EPC fields cannot contain control characters")
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        raise ValueError("Invalid EPC IBAN")
    checksum = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in iban[4:] + iban[:4]
    )
    if int(checksum) % 97 != 1:
        raise ValueError("Invalid EPC IBAN checksum")
    amount = Decimal(str(amount))
    if not amount.is_finite() or not Decimal("0.01") <= amount <= Decimal(
        "999999999.99"
    ):
        raise ValueError("Invalid EPC amount")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("EPC amount must be in whole cents")
    amount_text = format(amount, ".2f")
    payload = "\n".join(
        [
            "BCD",
            "002",
            "1",
            "SCT",
            "",
            name,
            iban,
            "EUR" + amount_text,
            "",
            "",
            reference,
        ]
    )
    if len(payload.encode("utf-8")) > 331:
        raise ValueError("EPC payload exceeds 331 bytes")
    code = pyqrcode.create(payload.encode("utf-8"), error="M", mode="binary")
    output = BytesIO()
    code.png(output, scale=8, quiet_zone=4)
    return {
        "name": name,
        "iban": iban,
        "amount": amount_text,
        "reference": reference,
        "qr": "data:image/png;base64,"
        + base64.b64encode(output.getvalue()).decode("ascii"),
    }
