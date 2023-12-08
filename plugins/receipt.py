import json


class receipt:
    receipt = []
    totals = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def is_empty(self):
        print("hooi", self.receipt)
        if self.receipt:
            return False
        return True

    def updatetotals(self):
        self.totals = {}
        for r in range(  # pylint: disable=consider-using-enumerate
            0, len(self.receipt)
        ):  # pylint: disable=consider-using-enumerate
            rr = self.receipt[r]
            beni = rr["beni"]
            count = rr["count"]
            value = rr["value"]
            if rr["Lose"]:
                if beni in self.totals:
                    self.totals[beni] -= count * value
                else:
                    self.totals[beni] = 0 - count * value
            else:
                if beni in self.totals:
                    self.totals[beni] += count * value
                else:
                    self.totals[beni] = count * value
        ret = []
        for usr in self.totals:  # pylint: disable=consider-using-dict-items
            ret.append({"user": usr, "amount": self.totals[usr]})
        self.master.send_message(True, "totals", json.dumps(ret))

    def hook_checkout(self, user):
        self.totals = {}
        for r in range(  # pylint: disable=consider-using-enumerate
            0, len(self.receipt)
        ):  # pylint: disable=consider-using-enumerate
            rr = self.receipt[r]
            beni = rr["beni"]
            if beni is None:
                beni = user
                self.receipt[r]["beni"] = user
            self.receipt[r]["description"] = self.receipt[r]["description"].replace(
                "-you-", user
            )
        self.updatetotals()
        self.master.send_message(True, "receipt", json.dumps(self.receipt))

    def hook_endsession(self, _text):
        self.receipt = []

    def hook_ok(self, _void):
        self.receipt = []
        self.master.send_message(True, "receipt", json.dumps(self.receipt))
        self.updatetotals()

    def hook_abort(self, _void):
        self.receipt = []
        self.master.send_message(True, "receipt", json.dumps(self.receipt))
        self.updatetotals()

    def help(self):
        return {"remove": "Remove Item"}

    def add(  # pylint: disable=too-many-arguments
        self, Lose, Value, Description, Count, Beni, Prod
    ):  # pylint: disable=too-many-arguments
        for r in range(  # pylint: disable=consider-using-enumerate
            0, len(self.receipt)
        ):  # pylint: disable=consider-using-enumerate
            if (
                self.receipt[r]["description"] == Description
                and self.receipt[r]["value"] == Value
                and self.receipt[r]["beni"] == Beni
                and self.receipt[r]["Lose"] == Lose
            ):
                self.receipt[r]["count"] += Count
                self.receipt[r]["total"] = (
                    self.receipt[r]["count"] * self.receipt[r]["value"]
                )
                self.master.send_message(True, "receipt", json.dumps(self.receipt))
                self.updatetotals()
                self.master.callhook(
                    "addremove", (Lose, Value, Description, Count, Beni, Prod)
                )
                return True
        self.receipt.append(
            {
                "Lose": Lose,
                "description": Description,
                "value": Value,
                "count": Count,
                "beni": Beni,
                "total": Count * Value,
                "product": Prod,
            }
        )
        self.master.send_message(True, "receipt", json.dumps(self.receipt))
        self.updatetotals()
        self.master.callhook("addremove", (Lose, Value, Description, Count, Beni, Prod))
        return True

    def input(self, text):
        if text == "remove":
            custom = [
                {"text": r, "display": self.receipt[r]["description"]}
                for r in range(0, len(self.receipt))
            ]
            self.master.send_message(
                True, "buttons", json.dumps({"special": "custom", "custom": custom})
            )
            self.master.donext(self, "remove")
            return True
        return None

    def remove(self, text):
        try:
            num = int(text)
            self.receipt.pop(num)
            self.master.send_message(True, "receipt", json.dumps(self.receipt))
            self.updatetotals()
            self.master.callhook("addremove", ())
            return True
        except:
            return True

    def startup(self):
        self.updatetotals()
        self.master.send_message(True, "receipt", json.dumps(self.receipt))
