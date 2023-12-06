# -*- coding: utf-8 -*-
import json
import time


class pfand:
    products = {}

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"pfand": "Return deposit"}

    def hook_addremove(self, args):
        (Lose, Value, Description, Count, Beni, Prod) = args
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
        for prod in self.products:
            desc = ""
            if self.master.products.lookupprod(prod):
                desc = self.master.products.products[prod]["description"]
            custom.append(
                {
                    "text": prod,
                    "display": "Pfand " + desc,
                    "right": self.products[prod],
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
        elif text == "abort":
            self.master.callhook("abort", None)
            return True
        else:
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

    def loadmarket(self):
        groupname = ""
        with open("data/revbank.pfand", "r") as f:
            lines = f.readlines()
        for line in lines:
            parts = " ".join(line.split()).split(" ", 2)
            if line.startswith("#"):
                groupname = line.replace("#", "").strip(" \t\n\r")
            elif len(parts) == 2:
                name = parts[0]
                self.products[name] = float(parts[1])

    def hook_abort(self, void):
        self.startup()

    def startup(self):
        self.loadmarket()
