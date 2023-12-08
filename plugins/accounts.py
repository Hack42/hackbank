import json
import time
import codecs


class accounts:
    accounts = {}
    aliases = {}
    members = []
    newaccount = ""
    adduseralias = ""

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"adduseralias": "Add user key alias"}

    # Internal functions
    def readaccounts(self):
        with codecs.open("data/revbank.accounts", "r", "utf-8") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.split()
            self.accounts[parts[0]] = {
                "amount": float(parts[1]),
                "lastupdate": parts[2],
            }
        with codecs.open("data/revbank.aliases", "r", "utf-8") as f:
            y = f.readlines()
            self.aliases = {}
            for x in y:
                s = x.split(" ")
                if len(s) == 2:
                    self.aliases[s[0]] = s[1].rstrip()

    def updateaccount(self, usr, value):
        print("Updating account", usr)
        if usr == "cash":
            return
        had = self.accounts[usr]["amount"]
        self.accounts[usr]["amount"] += value
        has = self.accounts[usr]["amount"]
        self.accounts[usr]["lastupdate"] = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.master.callhook("balance", (usr, had, has, self.master.transID))

    def writeaccount(self):
        with open("data/revbank.accounts", "w", encoding="utf-8") as f:
            for usr, account in self.accounts.items():
                f.write(
                    "%-18s %+7.2f %s\n"
                    % (
                        usr,
                        round(account["amount"], 2),
                        account["lastupdate"],
                    )
                )
        with open("data/revbank.aliases", "w", encoding="utf-8") as f:
            for usr, alias in self.aliases.items():
                f.write("%s %s\n" % (usr, alias))

    # Hooks
    def hook_balance(self, args):
        (usr, _had, _has, _transID) = args
        self.master.send_message(
            False, "infobox/account/" + usr, json.dumps(self.accounts[usr])
        )
        self.master.send_message(
            True, "accounts/" + usr, json.dumps(self.accounts[usr])
        )

    def hook_endsession(self, _text):
        self.writeaccount()

    def hook_abort(self, _void):
        self.readaccounts()
        for name, account in self.accounts.items():
            self.master.send_message(True, "accounts/" + name, json.dumps(account))

    def createnew(self, text):
        if text == "yes":
            self.accounts[self.newaccount] = {"amount": 0, "lastupdate": 0}
            return self.input(self.newaccount)
        if text == "no":
            return True
        if text == "abort":
            self.master.callhook("abort", None)
            return None
        self.master.send_message(
            True,
            "message",
            "Invalid answer; Account "
            + self.newaccount
            + " does not exist do you want to create?",
        )
        custom = [
            {"text": "yes", "display": "Yes"},
            {"text": "no", "display": "No"},
        ]
        self.master.send_message(
            True, "buttons", json.dumps({"special": "custom", "custom": custom})
        )
        self.master.donext(self, "createnew")
        return True

    def startup(self):
        self.readaccounts()
        for name, account in self.accounts.items():
            self.master.send_message(True, "accounts/" + name, json.dumps(account))
        with open("data/revbank.members", encoding="utf-8") as f:
            self.members = f.readlines()
        self.members = [m.rstrip() for m in self.members]
        self.master.send_message(True, "members", json.dumps(self.members))

    def hook_pre_checkout(self, _text):
        self.readaccounts()
        self.master.transID = int(time.time() - 1300000000)

    def hook_post_checkout(self, _text):
        self.master.send_message(True, "buttons", json.dumps({"special": "infobox"}))
        # self.master.send_message(True,'buttons',json.dumps({'special':'final'}))
        for usr in self.master.receipt.totals:
            self.updateaccount(usr, self.master.receipt.totals[usr])

    def messageandbuttons(self, donext, buttons, msg):
        self.master.donext(self, donext)
        self.master.send_message(True, "message", msg)
        self.master.send_message(True, "buttons", json.dumps({"special": buttons}))
        return True

    def addalias(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        if len(text) > 4 and not text in self.accounts and not text in self.aliases:
            self.aliases[text] = self.adduseralias
            self.writeaccount()
            return True
        return None

    def askalias(self, text):
        self.adduseralias = text
        if text == "abort":
            return self.master.callhook("abort", None)
        if text in self.accounts:
            return self.messageandbuttons("addalias", "keyboard", "What alias to add?")
        return None

    # This handles the input
    def input(self, text):
        if self.master.receipt.is_empty() and (
            text in self.accounts or text in self.aliases
        ):
            if text in self.aliases:
                text = self.aliases[text]
            self.master.send_message(
                False, "infobox/account", json.dumps(self.accounts[text])
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "infobox"})
            )
            return True
        if text in self.accounts or text in self.aliases:
            if text in self.aliases:
                text = self.aliases[text]
            self.master.callhook("checkout", text)
            self.master.callhook("endsession", text)
            return True
        if text == "adduseralias":
            return self.messageandbuttons(
                "askalias", "accounts", "What user do you want to alias?"
            )
        return None

    def newuser(self, text):
        for rid in self.master.receipt.receipt:
            if rid["value"] > 0 and not rid["Lose"]:
                self.master.send_message(
                    True,
                    "message",
                    "Account " + text + " does not exist do you want to create?",
                )
                custom = [
                    {"text": "yes", "display": "Yes"},
                    {"text": "no", "display": "No"},
                ]
                self.master.send_message(
                    True, "buttons", json.dumps({"special": "custom", "custom": custom})
                )
                self.master.donext(self, "createnew")
                self.newaccount = text
                return True
        return None
