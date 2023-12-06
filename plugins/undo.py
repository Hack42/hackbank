# -*- coding: utf-8 -*-
import json
import pickle
import time


class undo:
    undo = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {
            "undo": "Undo last transaction",
            "undolist": "Undo a transaction",
            "restore": "Restore a transaction",
        }

    def hook_checkout(self, text):
        self.loadundo()
        self.undo[self.master.transID] = {
            "totals": self.master.receipt.totals,
            "receipt": self.master.receipt.receipt,
            "beni": text,
        }
        self.writeundo()

    def hook_undo(self, args):
        (transID, totals, receipt, beni) = args
        self.loadundo()
        if transID in self.undo:
            del self.undo[transID]
            self.writeundo()
        for usr in totals:
            if totals[usr] > 0:
                self.master.receipt.add(
                    True, totals[usr], "Undo " + str(transID), 1, usr, "undo"
                )
            else:
                self.master.receipt.add(
                    False, 0 - totals[usr], "Undo " + str(transID), 1, usr, "undo"
                )
        self.master.callhook("checkout", beni)
        self.master.callhook("endsession", beni)

    def writeundo(self):
        while len(self.undo) > 50:
            fk = sorted(self.undo.keys())
            del self.undo[fk[0]]

        output = open("data/revbank.UNDO", "wb")
        pickle.dump(self.undo, output)
        output.close()

    def loadundo(self):
        try:
            with open("data/revbank.UNDO", "rb") as f:
                self.undo = pickle.load(f)
                f.close()
        except:
            pass

    def doundo(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            transID = int(text)
            if transID in self.undo:
                self.master.callhook(
                    "undo",
                    (
                        transID,
                        self.undo[transID]["totals"],
                        self.undo[transID]["receipt"],
                        self.undo[transID]["beni"],
                    ),
                )
                return True
            else:
                self.listundo()
                return True
        except:
            import traceback

            traceback.print_exc()
            self.listundo()
            return True

    def dorestore(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            transID = int(text)
            if transID in self.undo:
                receipt = self.undo[transID]["receipt"]
                beni = self.undo[transID]["beni"]
                self.master.callhook(
                    "undo",
                    (
                        transID,
                        self.undo[transID]["totals"],
                        self.undo[transID]["receipt"],
                        self.undo[transID]["beni"],
                    ),
                )
                for rr in receipt:
                    nowbeni = None
                    if rr["beni"] != beni:
                        nowbeni = rr["beni"]
                    self.master.receipt.add(
                        rr["Lose"],
                        rr["value"],
                        rr["description"],
                        rr["count"],
                        nowbeni,
                        rr["product"],
                    )
                return True
            else:
                self.listundo()
                return True
        except:
            import traceback

            traceback.print_exc()
            self.listundo()
            return True

    def listundo(self, restore):
        self.loadundo()
        custom = []
        count = 0
        for transID in self.undo.keys():
            txt = ""
            for usr in self.undo[transID]["totals"].keys():
                txt += usr + " €" + "%.2f" % self.undo[transID]["totals"][usr] + " "
            txt += time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(transID + 1300000000)
            )
            custom.insert(0, {"text": transID, "display": txt})
            count += 1
            if count > 49:
                break
        self.master.send_message(
            True,
            "buttons",
            json.dumps({"special": "custom", "custom": custom, "sort": "text"}),
        )
        if restore:
            self.master.send_message(True, "message", "Select a transaction to restore")
            self.master.donext(self, "dorestore")
        else:
            self.master.send_message(True, "message", "Select a transaction to undo")
            self.master.donext(self, "doundo")

    def input(self, text):
        if text == "undolist":
            self.listundo(0)
            return True
        elif text == "restore":
            self.listundo(1)
            return True
        elif text == "undo":
            # whatever, works if you just did a transaction
            self.doundo(self.master.transID)
            return True

    def hook_abort(self, void):
        self.startup()

    def startup(self):
        self.loadundo()
