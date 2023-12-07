# -*- coding: utf-8 -*-


class withdraw:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def withdraw(self, text):
        try:
            value = float(text)
            if 0 < value < 1000:
                self.master.receipt.add(
                    True, value, "Withdrawal or unlisted product", 1, None, "withdraw"
                )
                return True
            self.master.send_message(
                True,
                "message",
                "Enter an amount between 0.01 and 999.99 or scan a product",
            )
            return True
        except:
            pass
        return None

    def input(self, text):
        pass

    def startup(self):
        pass
