import json
import os
import tempfile
import threading


def _atomic_write(path, lines):
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".", dir=directory, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)
        os.replace(tmp_path, path)
    except:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


class stock:
    stock = {}
    prod = ""
    stockalias = ""
    write_lock = threading.Lock()

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.stock = {}
        self.prod = ""
        self.stockalias = {}

    def help(self):
        return {
            "inkoop": "Report buying products",
            "voorraad": "Set stock of a product",
        }

    def readstock(self):
        self.stock = {}
        self.stockalias = {}
        with open("data/revbank.stock", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = " ".join(line.split()).split(" ", 2)
            if len(parts) == 2:
                name = parts[0]
                try:
                    self.stock[name] = int(parts[1])
                except ValueError:
                    continue
        f.close()
        with open("data/revbank.stockalias", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = " ".join(line.split()).split(" ", 3)
            if len(parts) == 3:
                name = parts[0]
                try:
                    multiplier = int(parts[2])
                except ValueError:
                    continue
                self.stockalias[name] = {"prod": parts[1], "multi": multiplier}

    def setstock(self, prod, count):
        self.readstock()
        if prod not in self.stock:
            self.stock[prod] = 0
        self.stock[prod] = count
        self.master.send_message(True, "stock/" + prod, json.dumps(self.stock[prod]))
        self.writestock()

    def addstock(self, prod, count):
        self.readstock()
        if prod not in self.stock:
            self.stock[prod] = 0
        self.stock[prod] += count
        self.master.send_message(True, "stock/" + prod, json.dumps(self.stock[prod]))
        self.writestock()

    def hook_checkout(self, _text):
        self.readstock()
        for rid in self.master.receipt.receipt:
            if rid["product"] in self.stockalias:
                rp = rid["product"]
                prod = self.stockalias[rp]["prod"]
                multiplier = self.stockalias[rp]["multi"]
            else:
                prod = rid["product"]
                multiplier = 1
            if prod in self.master.products.products:
                if prod not in self.stock:
                    self.stock[prod] = 0
                self.stock[prod] -= rid["count"] * multiplier
                self.master.send_message(
                    True, "stock/" + prod, json.dumps(self.stock[prod])
                )
        self.writestock()

    def writestock(self):
        with self.write_lock:
            _atomic_write(
                "data/revbank.stock",
                [
                    "%-16s %+9d\n" % (prod, product)
                    for prod, product in self.stock.items()
                ],
            )

    def voorraad_amount(self, text):
        try:
            aantal = int(text)
            if not -1 < aantal < 5000:
                self.master.donext(self, "voorraad_amount")
                self.master.send_message(
                    True,
                    "message",
                    "Please enter a number between 0 and 4999, how much "
                    + self.prod
                    + " is in stock?",
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "numbers"})
                )
                return True
            self.setstock(self.prod, aantal)
            self.master.donext(self, "voorraad")
            self.master.send_message(True, "message", "What product to set the stock?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True
        except:
            if text == "abort":
                self.master.callhook("abort", None)
                return True
            self.master.donext(self, "voorraad_amount")
            self.master.send_message(
                True,
                "message",
                "Not a number, how much " + self.prod + " is in stock",
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True

    def voorraad(self, text):
        prod = self.master.products.lookupprod(text)
        if prod:
            self.prod = prod
            self.master.donext(self, "voorraad_amount")
            self.master.send_message(
                True, "message", "How much " + prod + " is in stock?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        self.master.donext(self, "voorraad")
        self.master.send_message(
            True, "message", "Unknown Product, what product to set the stock?"
        )
        self.master.send_message(True, "buttons", json.dumps({"special": "products"}))
        return True

    def inkoop_amount(self, text):
        try:
            aantal = int(text)
            if not 0 < aantal < 5000:
                self.master.donext(self, "inkoop_amount")
                self.master.send_message(
                    True,
                    "message",
                    "Please enter a number between 1 and 4999, how much "
                    + self.prod
                    + " did you buy?",
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "numbers"})
                )
                return True
            self.addstock(self.prod, aantal)
            self.master.donext(self, "inkoop")
            self.master.send_message(True, "message", "What product did you buy?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True
        except:
            if text == "abort":
                self.master.callhook("abort", None)
                return True
            self.master.donext(self, "inkoop_amount")
            self.master.send_message(
                True,
                "message",
                "Not a number, how much " + self.prod + " did you buy?",
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True

    def inkoop(self, text):
        prod = self.master.products.lookupprod(text)
        if prod:
            self.prod = prod
            self.master.donext(self, "inkoop_amount")
            self.master.send_message(
                True, "message", "How much " + self.prod + " did you buy?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "numbers"})
            )
            return True
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        self.master.donext(self, "inkoop")
        self.master.send_message(
            True, "message", "Unknown Product, what product did you buy?"
        )
        self.master.send_message(True, "buttons", json.dumps({"special": "products"}))
        return True

    def input(self, text):
        if text == "voorraad":
            self.master.donext(self, "voorraad")
            self.master.send_message(True, "message", "What product to set the stock?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True
        if text == "inkoop":
            self.master.donext(self, "inkoop")
            self.master.send_message(True, "message", "What product did you buy?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True
        return None

    def hook_abort(self, _void):
        self.startup()

    def startup(self):
        self.readstock()
        for prod, product in self.stock.items():
            self.master.send_message(True, "stock/" + prod, json.dumps(product))
