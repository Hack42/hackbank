import json
import traceback


class deposit:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

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
        try:
            value = float(text)
            if 0 < value < 1000:
                self.master.receipt.add(False, value, "Deposit", 1, None, "deposit")
            else:
                self.master.donext(self, "value")
                self.master.send_message(
                    True, "message", "Enter an amount between 0.01 and 999.99:"
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "numbers"})
                )
            return True
        except:

            traceback.print_exc()
            if text == "abort":
                self.master.callhook("abort", None)
                return True
            self.master.donext(self, "value")
            self.master.send_message(
                True, "message", "Not a valid number! How much do you want to deposit?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True

    def startup(self):
        pass
