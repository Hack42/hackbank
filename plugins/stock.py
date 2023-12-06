import json


class stock:
    stock = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {
            "inkoop": "Report buying products",
            "voorraad": "Set stock of a product",
        }

    def readstock(self):
        groupname = ""
        with open("data/revbank.stock", "r") as f:
            lines = f.readlines()
        for line in lines:
            parts = " ".join(line.split()).split(" ", 2)
            if len(parts) == 2:
                name = parts[0]
                self.stock[name] = int(parts[1])
        f.close()
        self.stockalias = {}
        with open("data/revbank.stockalias", "r") as f:
            lines = f.readlines()
        for line in lines:
            parts = " ".join(line.split()).split(" ", 3)
            if len(parts) == 3:
                name = parts[0]
                self.stockalias[name] = {"prod": parts[1], "multi": int(parts[2])}

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

    def hook_checkout(self, text):
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
        with open("data/revbank.stock", "w") as f:
            for prod in self.stock:
                f.write("%-16s %+9d\n" % (prod, self.stock[prod]))
            f.close()

    def voorraad_amount(self, text):
        try:
            aantal = int(text)
            if aantal < 0 or aantal > 5000:
                self.master.donext(self, "voorraad_amount")
                self.master.send_message(
                    True,
                    "message",
                    "Please enter a number between 1 and 4999, how much "
                    + self.prod
                    + " is in stock?",
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "numbers"})
                )
                return True
            else:
                self.setstock(self.prod, aantal)
                self.master.donext(self, "voorraad")
                self.master.send_message(
                    True, "message", "What product to set the stock?"
                )
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "products"})
                )
                return True
        except:
            if text == "abort":
                self.master.callhook("abort", None)
                return True
            else:
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
        elif text == "abort":
            self.master.callhook("abort", None)
            return True
        else:
            self.master.donext(self, "voorraad")
            self.master.send_message(
                True, "message", "Unknown Product, what product to set the stock?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True

    def inkoop_amount(self, text):
        try:
            aantal = int(text)
            if aantal < 0 or aantal > 5000:
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
            else:
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
            else:
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
        elif text == "abort":
            self.master.callhook("abort", None)
            return True
        else:
            self.master.donext(self, "inkoop")
            self.master.send_message(
                True, "message", "Unknown Product, what product did you buy?"
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True

    def input(self, text):
        if text == "voorraad":
            self.master.donext(self, "voorraad")
            self.master.send_message(True, "message", "What product to set the stock?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True
        elif text == "inkoop":
            self.master.donext(self, "inkoop")
            self.master.send_message(True, "message", "What product did you buy?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "products"})
            )
            return True

    def hook_abort(self, void):
        self.startup()

    def startup(self):
        self.readstock()
        for prod in self.stock:
            self.master.send_message(
                True, "stock/" + prod, json.dumps(self.stock[prod])
            )
