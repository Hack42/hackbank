import json
import os
import re
import tempfile
import threading
from input_validation import filter_reserved_aliases, is_reserved_input


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


class products:
    products = {}
    aliases = {}
    groups = {}
    times = 1

    aliasprod = ""
    priceprod = ""
    newprodprice = 0
    newprodgroup = ""
    newproddesc = ""
    newprod = ""
    write_lock = threading.Lock()

    def help(self):
        return {
            "aliasproduct": "Add alias to product",
            "addproduct": "Add new product",
            "setprice": "Change the price of a product",
        }

    def is_reserved_input(self, text):
        return is_reserved_input(text, master=self.master, plugin_help=self.help())

    def readproducts(self):
        self.products = {}
        self.aliases = {}
        self.groups = {}
        groupname = ""
        with open("data/revbank.products", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if not line.strip():
                continue
            parts = " ".join(line.split()).split(" ", 2)
            if line.startswith("#"):
                groupname = line.replace("#", "").strip(" \t\n\r")
                if not groupname:
                    continue
                self.groups[groupname] = []
            elif len(parts) == 3:
                aliases = parts[0].split(",")
                name = aliases.pop(0)
                if self.is_reserved_input(name):
                    continue
                aliases = filter_reserved_aliases(
                    aliases, master=self.master, plugin_help=self.help()
                )
                try:
                    price = float(parts[1])
                except ValueError:
                    continue
                self.groups[groupname].append(name)
                for alias in aliases:
                    self.aliases[alias] = name
                self.products[name] = {
                    "price": price,
                    "description": parts[2],
                    "group": groupname,
                    "aliases": aliases,
                }
        for prod in self.products:  # pylint: disable=consider-using-dict-items
            self.master.send_message(
                True, "products/" + prod, json.dumps(self.products[prod])
            )
        print("readproducts done")

    def writeproducts(self):
        lines = []
        with self.write_lock:
            for group in self.groups:  # pylint: disable=consider-using-dict-items
                lines.append("# " + group + "\n")
                for prod in self.groups[group]:
                    names = [prod] + self.products[prod]["aliases"]
                    lines.append(
                        "%-58s %7.2f  %s\n"
                        % (
                            ",".join(names),
                            self.products[prod]["price"],
                            self.products[prod]["description"],
                        )
                    )
                lines.append("\n")
            _atomic_write("data/revbank.products", lines)

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.products = {}
        self.aliases = {}
        self.groups = {}
        self.times = 1
        self.aliasprod = ""
        self.priceprod = ""
        self.newprodprice = 0
        self.newprodgroup = ""
        self.newproddesc = ""
        self.newprod = ""

    def lookupprod(self, text):
        if self.is_reserved_input(text):
            return None
        prod = None
        if text in self.products:
            prod = text
        if text in self.aliases:
            prod = self.aliases[text]
        return prod

    def messageandbuttons(self, donext, buttons, msg):
        self.master.donext(self, donext)
        self.master.send_message(True, "message", msg)
        self.master.send_message(True, "buttons", json.dumps({"special": buttons}))
        return True

    def savealias(self, text):
        self.readproducts()
        if text == "abort":
            return self.master.callhook("abort", None)
        prod = self.lookupprod(text)
        if prod:
            return self.messageandbuttons(
                "savealias",
                "keyboard",
                "Already known alias " + text + " for " + prod + "! Try again.",
            )
        if self.is_reserved_input(text):
            return self.messageandbuttons(
                "savealias",
                "keyboard",
                "That alias is a command; choose another alias.",
            )
        if len(text) < 6 or not re.compile("^[A-z0-9]+$").match(text):
            return self.messageandbuttons(
                "savealias",
                "keyboard",
                "only [A-z0-9] is allowed in any alias and it should be at least 4 chars long",
            )
        self.products[self.aliasprod]["aliases"].append(text)
        self.writeproducts()
        self.readproducts()
        return True

    def addalias(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        prod = self.lookupprod(text)
        if prod:
            self.aliasprod = prod
            return self.messageandbuttons(
                "savealias", "keyboard", "What alias to add for " + prod + "?"
            )
        return self.messageandbuttons(
            "addalias",
            "products",
            "Unknown product;What product do you want to alias?",
        )

    def setprice(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        prod = self.lookupprod(text)
        if prod:
            self.priceprod = prod
            return self.messageandbuttons(
                "saveprice", "numbers", "What is the new price for " + prod + "?"
            )
        return self.messageandbuttons(
            "setprice",
            "products",
            "Unknown product;What product do you want change price?",
        )

    def saveprice(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            price = float(text)
            print(price)
            if not 0 < price < 1000:
                return self.messageandbuttons(
                    "saveprice", "numbers", "Price should be between 0 and 1000"
                )
            self.newprodprice = price
            self.products[self.priceprod]["price"] = self.newprodprice
            self.writeproducts()
            self.readproducts()
            return True
        except:
            return self.messageandbuttons(
                "saveprice",
                "numbers",
                "Not a valid number; What is the price for" + self.newprod + "?",
            )

    def addproductgroup(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        if len(text) < 4:
            self.master.donext(self, "addproductgroup")
            self.master.send_message(
                True, "message", "Too short,what productgroup to add the product to?"
            )
            self.master.send_message(
                True,
                "buttons",
                json.dumps(
                    {
                        "special": "custom",
                        "custom": [{"text": n, "display": n} for n in self.groups],
                    }
                ),
            )
            return True
        self.newprodgroup = text
        if self.newprodgroup not in self.groups:
            self.groups[self.newprodgroup] = [self.newprod]
            self.products[self.newprod] = {
                "price": self.newprodprice,
                "description": self.newproddesc,
                "group": self.newprodgroup,
                "aliases": [],
            }
            self.writeproducts()
            self.readproducts()
            return True
        self.groups[self.newprodgroup].append(self.newprod)
        self.products[self.newprod] = {
            "price": self.newprodprice,
            "description": self.newproddesc,
            "group": self.newprodgroup,
            "aliases": [],
        }
        self.writeproducts()
        self.readproducts()
        return True

    def addproductprice(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            price = float(text)
            if not 0 < price < 1000:
                return self.messageandbuttons(
                    "addproductprice",
                    "numbers",
                    "Price should be between 0 and 1000",
                )
            self.newprodprice = price
            self.master.donext(self, "addproductgroup")
            self.master.send_message(
                True, "message", "what productgroup to add the product to?"
            )
            self.master.send_message(
                True,
                "buttons",
                json.dumps(
                    {
                        "special": "custom",
                        "custom": [{"text": n, "display": n} for n in self.groups],
                    }
                ),
            )
            return True
        except:
            return self.messageandbuttons(
                "addproductprice",
                "numbers",
                "Not a valid number; What is the price for" + self.newprod + "?",
            )

    def addproductdesc(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        if len(text) < 4:
            return self.messageandbuttons(
                "addproductdesc",
                "keyboard",
                "Too short, What is the description for " + self.newprod + "?",
            )
        self.newproddesc = text
        return self.messageandbuttons(
            "addproductprice",
            "numbers",
            "What is the price for " + self.newprod + "?",
        )

    def addproduct(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        prod = self.lookupprod(text)
        if prod:
            return self.messageandbuttons(
                "addproduct", "keyboard", "Product already exists? What product to add?"
            )
        if self.is_reserved_input(text):
            return self.messageandbuttons(
                "addproduct",
                "keyboard",
                "That product name is a command; choose another name.",
            )
        if len(text) < 4 or not re.compile("^[A-z0-9]+$").match(text):
            return self.messageandbuttons(
                "addproduct",
                "keyboard",
                "only [A-z0-9] is allowed as product name, what name do you want to add?",
            )
        self.newprod = text
        return self.messageandbuttons(
            "addproductdesc",
            "keyboard",
            "What is the description for " + text + "?",
        )

    def input(self, text):
        prod = self.lookupprod(text)
        if prod:
            self.master.receipt.add(
                True,
                self.products[prod]["price"],
                self.products[prod]["description"],
                self.times,
                None,
                prod,
            )
            self.times = 1
            return True
        if text == "aliasproduct":
            return self.messageandbuttons(
                "addalias", "products", "What product do you want to alias?"
            )
        if text == "addproduct":
            return self.messageandbuttons(
                "addproduct",
                "keyboard",
                "What is the name of the product you want to add?",
            )
        if text == "setprice":
            return self.messageandbuttons(
                "setprice", "products", "What product to change the price for?"
            )
        if text.endswith("*"):
            try:
                value = float(text[:-1])
                if 0 < value < 100:
                    self.times = value
                    self.master.send_message(
                        True, "message", "What are you buying %d from?" % self.times
                    )
                    self.master.send_message(
                        True, "buttons", json.dumps({"special": "products"})
                    )
                    return True
            except:
                pass
        return None

    def hook_abort(self, _void):
        self.startup()

    def startup(self):
        self.readproducts()
        self.times = 1
