import time


class log:
    def __init__(self, SID, master):
        self.SID = SID
        self.master = master

    def help(self):
        return {}

    def startup(self):
        self.master.send_message(False, "log", "Log has startup")

    def log(self, action, text):
        with open("data/revbank.log", "a", encoding="utf-8") as logfile:
            logfile.write(
                time.strftime("%Y-%m-%d_%H:%M:%S") + " " + action + " " + text + "\n"
            )
            logfile.close()
        self.master.send_message(False, "log", action + " >> " + text)

    def hook_balance(self, args):
        (usr, had, has, trxID) = args
        if had > has:
            self.log(
                "BALANCE",
                "%-10d %s had %+.02f, lost %+.02f, now has %+.02f"
                % (trxID, usr, had, 0 - (had - has), has),
            )
        else:
            self.log(
                "BALANCE",
                "%-10d %s had %+.02f, gained %+.02f, now has %+.02f"
                % (trxID, usr, had, has - had, has),
            )

    def hook_post_checkout(self, _text):
        for rr in self.master.receipt.receipt:
            self.log(
                "CHECKOUT",
                "%-10d %s %d * %10.2f %s EUR %10.2f # %s"
                % (
                    self.master.transID,
                    rr["beni"],
                    rr["count"],
                    rr["value"],
                    ("LOSE" if rr["Lose"] else "GAIN"),
                    rr["count"] * rr["value"],
                    rr["description"],
                ),
            )

    def input(self, text):
        pass

    def pre_input(self, text):
        self.log("PROMPT", self.master.prompt.decode() + " >> " + text)
        # self.master.send_message(False,'log',self.master.prompt+" >> "+text)
