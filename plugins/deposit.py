import json
from decimal import Decimal, InvalidOperation

from epc_payment import create_payment


class deposit:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.payment_shown = False

    def help(self):
        return {"deposit": "Deposit Money"}

    def input(self, text):
        if text == "deposit":
            self.master.donext(self, "value")
            self.master.send_message(
                True, "message", "How much do you want to deposit?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True
        return None

    def value(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            amount = Decimal(text)
        except InvalidOperation:
            self.master.donext(self, "value")
            self.master.send_message(
                True, "message", "Not a valid number! How much do you want to deposit?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True
        if (
            amount.is_finite()
            and Decimal("0.01") <= amount <= Decimal("999.99")
            and amount == amount.quantize(Decimal("0.01"))
        ):
            self.master.receipt.add(False, float(amount), "Deposit", 1, None, "deposit")
        else:
            self.master.donext(self, "value")
            self.master.send_message(
                True, "message", "Enter an amount between 0.01 and 999.99:"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
        return True

    def hook_post_checkout(self, _user):
        amounts = {}
        for row in self.master.receipt.receipt:
            user = row["beni"]
            if row["product"] == "deposit" and not row["Lose"] and user != "cash":
                amounts[user] = amounts.get(user, Decimal(0)) + (
                    Decimal(str(row["value"])) * Decimal(str(row["count"]))
                )
        if amounts:
            payments = [
                create_payment(user, amount) for user, amount in amounts.items()
            ]
            self.master.send_message(
                True, "deposit_payment", json.dumps({"payments": payments})
            )
            self.payment_shown = True

    def pre_input(self, _text):
        if self.payment_shown:
            self.master.send_message(True, "deposit_payment", "{}")
            self.payment_shown = False

    def startup(self):
        self.master.send_message(True, "deposit_payment", "{}")
