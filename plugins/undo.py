# -*- coding: utf-8 -*-
import json
import copy
import pickle
import time
import logging


logger = logging.getLogger(__name__)


class undo:
    undo = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.undo = {}

    def help(self):
        return {
            "undo": "Undo last transaction",
            "undolist": "Undo a transaction",
            "restore": "Restore a transaction",
        }

    def hook_post_checkout(self, text):
        self.loadundo()
        self.undo[self.master.transID] = {
            "totals": copy.deepcopy(self.master.receipt.totals),
            "receipt": copy.deepcopy(self.master.receipt.receipt),
            "beni": text,
        }
        self.writeundo()

    def hook_undo(self, args):
        transID, totals, _receipt, beni = args
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

        with open("data/revbank.UNDO", "w", encoding="utf-8") as output:
            json.dump(self.undo, output)

    def loadundo(self):
        self.undo = {}
        try:
            with open("data/revbank.UNDO", "rb") as f:
                data = f.read()
        except OSError:
            return

        try:
            try:
                loaded = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                loaded = pickle.loads(data)
            self.undo = {int(transID): value for transID, value in loaded.items()}
        except (
            AttributeError,
            EOFError,
            TypeError,
            ValueError,
            pickle.PickleError,
        ):
            return

    def doundo(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            transID = int(text)
        except (TypeError, ValueError):
            self.listundo()
            return True

        if transID in self.undo:
            entry = self._get_undo_entry(transID)
            if entry is None:
                self.listundo()
                return True
            totals, receipt, beni = entry
            self.master.callhook(
                "undo",
                (transID, totals, receipt, beni),
            )
            return True

        logger.warning(
            "undo_transaction_not_found sid=%s trans_id=%s available=%s",
            self.SID,
            transID,
            sorted(self.undo.keys()),
        )
        self.listundo()
        return True

    def _get_undo_entry(self, transID):
        try:
            return (
                self.undo[transID]["totals"],
                self.undo[transID]["receipt"],
                self.undo[transID]["beni"],
            )
        except (KeyError, TypeError):
            return None

    def _restore_receipt(self, receipt, beni):
        try:
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
        except (KeyError, TypeError):
            self.listundo()
            return True
        return True

    def dorestore(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            transID = int(text)
        except (TypeError, ValueError):
            self.listundo()
            return True

        if transID not in self.undo:
            self.listundo()
            return True

        entry = self._get_undo_entry(transID)
        if entry is None:
            self.listundo()
            return True

        totals, receipt, beni = entry
        self.master.callhook("undo", (transID, totals, receipt, beni))
        return self._restore_receipt(receipt, beni)

    def listundo(self, restore=False):
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
        if text == "restore":
            self.listundo(1)
            return True
        if text == "undo":
            # whatever, works if you just did a transaction
            self.doundo(self.master.transID)
            return True
        return None

    def hook_abort(self, _void):
        self.startup()

    def startup(self):
        self.loadundo()
