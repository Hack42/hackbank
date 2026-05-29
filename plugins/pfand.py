# -*- coding: utf-8 -*-
import json


class pfand:
    products = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.products = {}

    def help(self):
        return {"pfand": "Return deposit"}

    def hook_addremove(self, args):
        _Lose, _Value, Description, Count, Beni, Prod = args
        if Prod in self.products:
            self.master.receipt.add(
                True,
                self.products[Prod],
                "Pfand " + Description,
                Count,
                Beni,
                "pfand_" + Prod,
            )

    def listpfand(self):
        custom = []
        for prod, product in self.products.items():
            desc = ""
            if self.master.products.lookupprod(prod):
                desc = self.master.products.products[prod]["description"]
            custom.append(
                {
                    "text": prod,
                    "display": "Pfand " + desc,
                    "right": product,
                    "rightclass": "green",
                }
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "custom", "custom": custom})
            )
            self.master.donext(self, "pfand")

    def pfand(self, text):
        if text in self.products:
            self.master.receipt.add(
                False,
                self.products[text],
                "Pfand return " + text,
                1,
                None,
                "return_" + text,
            )
            return True
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        self.listpfand()
        self.master.send_message(
            True, "message", "Unknown product, what product are you returning?"
        )
        return True

    def input(self, text):
        if text == "pfand":
            self.listpfand()
            self.master.send_message(True, "message", "What product are you returning?")
            return True
        return None

    def loadmarket(self):
        self.products = {}
        with open("data/revbank.pfand", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = " ".join(line.split()).split(" ", 2)
            if len(parts) == 2:
                name = parts[0]
                try:
                    self.products[name] = float(parts[1])
                except ValueError:
                    continue

    def hook_abort(self, _void):
        self.startup()

    def startup(self):
        self.loadmarket()
