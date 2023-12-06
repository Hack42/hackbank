import json


class give:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"give": "Give Money to other user"}

    def who(self, text):
        if text in self.master.accounts.accounts:
            self.userto = text
            self.master.donext(self, "amount")
            self.master.send_message(
                True, "message", "How much do you want to give to " + self.userto + "?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True
        elif text == "abort":
            self.master.callhook("abort", None)
            return True
        else:
            self.master.donext(self, "who")
            self.master.send_message(True, "message", "Unknown User; User to give to?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True

    def amount(self, text):
        try:
            value = float(text)
            if value > 0 and value < 1000:
                self.value = value
                self.master.donext(self, "reason")
                self.master.send_message(
                    True,
                    "message",
                    "Why are you giving "
                    + str(self.value)
                    + " to "
                    + self.userto
                    + "?",
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "keyboard"})
                )
            else:
                self.master.donext(self, "amount")
                self.master.send_message(
                    True, "message", "Enter an amount between 0.01 and 999.99:"
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "numbers"})
                )
            return True
        except:
            if text == "abort":
                self.master.callhook("abort", None)
                return True
            self.master.donext(self, "amount")
            self.master.send_message(
                True,
                "message",
                "Not a valid number! How much do you want to give to "
                + self.userto
                + "?",
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True

    def reason(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        self.myreason = text
        self.master.receipt.add(
            True,
            self.value,
            "Give to " + self.userto + " (" + self.myreason + ")",
            1,
            None,
            "give",
        )
        self.master.receipt.add(
            False,
            self.value,
            "Given from -you- (" + self.myreason + ")",
            1,
            self.userto,
            "give",
        )
        return True

    def input(self, text):
        if text == "give":
            self.master.donext(self, "who")
            self.master.send_message(True, "message", "User to give to?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True

    def startup(self):
        pass
