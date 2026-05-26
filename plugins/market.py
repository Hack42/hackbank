import json
import os
import re
import tempfile
import threading

RESERVED_INPUTS = {"abort", "ok"}


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


class market:
    products = {}
    aliases = {}
    groups = {}
    times = 1
    aliasprod = ""
    priceprod = 0
    newprodprice = 0
    newprodgroup = ""
    newproddesc = ""
    newprod = ""
    write_lock = threading.Lock()

    def help(self):
        return {
            "addmarket": "Market: Add alias",
            "delmarket": "Market: Remove a product",
            "changemarket": "Market: Change Price",
            "market": "Market: Products",
        }

    def reserved_inputs(self):
        reserved = set(RESERVED_INPUTS)
        reserved.update(self.help().keys())
        master_help = getattr(self.master, "help", {})
        if isinstance(master_help, dict):
            reserved.update(master_help.keys())
        return reserved

    def is_reserved_input(self, text):
        return text in self.reserved_inputs()

    def readproducts(self):
        self.products = {}
        self.aliases = {}
        with open("data/revbank.market", "r", encoding="utf-8") as f:
            lines = f.readlines()
        print("ok", lines)
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = " ".join(line.split()).split(" ", 4)
            print(parts)
            if len(parts) == 5:
                aliases = parts[1].split(",")
                name = aliases.pop(0)
                if self.is_reserved_input(name):
                    continue
                aliases = [
                    alias for alias in aliases if not self.is_reserved_input(alias)
                ]
                try:
                    price = float(parts[2])
                    space = float(parts[3])
                except ValueError:
                    continue
                self.products[name] = {
                    "price": price,
                    "space": space,
                    "description": parts[4],
                    "aliases": aliases,
                    "user": parts[0],
                }
                for alias in aliases:
                    self.aliases[alias] = name
        for prod, product in self.products.items():
            self.master.send_message(True, "market/" + prod, json.dumps(product))

    def writeproducts(self):
        lines = [
            "#                               Price =\n",
            "# Seller   Barcode          Seller + Space  Description\n\n",
        ]
        with self.write_lock:
            for prod, product in self.products.items():
                names = [prod] + product["aliases"]
                lines.append(
                    "%-10s %-30s %7.2f %7.2f %s\n"
                    % (
                        product.get("user", self.newprodgroup),
                        ",".join(names),
                        product["price"],
                        product.get("space", 0.0),
                        product["description"],
                    )
                )
            _atomic_write("data/revbank.market", lines)

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.products = {}
        self.aliases = {}
        self.groups = {}
        self.times = 1
        self.aliasprod = ""
        self.priceprod = 0
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

    def delmarket(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        self.readproducts()
        prod = self.lookupprod(text)
        if prod:
            del self.products[prod]
            self.aliases = {}
            for product_name, product in self.products.items():
                for alias in product["aliases"]:
                    self.aliases[alias] = product_name
            self.writeproducts()
            return True
        return self.messageandbuttons(
            "delmarket",
            "keyboard",
            "Unknown market product;What market product do you want to remove?",
        )

    def saveprice(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            price = float(text)
            if not 0 < price < 1000:
                return self.messageandbuttons(
                    "saveprice", "numbers", "Price should be between 0 and 1000"
                )
            self.newprodprice = price
            self.products[self.priceprod]["price"] = price
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
                "Give to "
                + self.products[prod]["user"]
                + " (Market:"
                + self.products[prod]["description"]
                + ")",
                self.master.products.times,
                None,
                prod,
            )
            self.master.receipt.add(
                False,
                self.products[prod]["price"],
                "Given from -you- (Market:" + self.products[prod]["description"] + ")",
                self.master.products.times,
                self.products[prod]["user"],
                prod,
            )
            self.master.receipt.add(
                True,
                self.products[prod]["space"],
                self.products[prod]["description"],
                self.master.products.times,
                None,
                prod,
            )
            self.master.products.times = 1
            return True
        if text == "market":
            custom = []
            for prod, product in self.products.items():
                custom.append(
                    {
                        "text": prod,
                        "display": product["description"],
                        "right": "%0.2f (%0.2f)"
                        % (
                            product["price"] + product["space"],
                            product["space"],
                        ),
                    }
                )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "custom", "custom": custom})
            )
            return True
        if text == "addmarket":
            return self.messageandbuttons(
                "addalias", "keyboard", "What market product do you want to alias?"
            )
        if text == "changemarket":
            return self.messageandbuttons(
                "setprice", "keyboard", "What market product to change price for?"
            )
        if text == "delmarket":
            return self.messageandbuttons(
                "delmarket", "keyboard", "What market product do you want to remove?"
            )

        #        elif text=="aliasproduct":
        #            return self.messageandbuttons('addalias','products','What product do you want to alias?')
        #        elif text=="addproduct":
        #            return self.messageandbuttons('addproduct','keyboard','What is the name of the product you want to add?')
        #        elif text=="setprice":
        #            return self.messageandbuttons('setprice','products','What product to change the price for?')
        #        elif text.endswith('*'):
        #            try:
        #                value=float(text[:-1])
        #                if value>0 and value<100:
        #                    self.times=value
        #                    self.master.send_message(True,'message',"What are you buying %d from?" % self.times)
        #                    self.master.send_message(True,'buttons',json.dumps({'special':'products'}))
        #                    return True
        #            except:
        #                pass
        return None

    def hook_abort(self, _void):
        self.startup()

    def startup(self):
        self.readproducts()
