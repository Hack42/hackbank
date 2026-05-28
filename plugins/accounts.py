import json
import os
import tempfile
import threading
import time
import codecs
import logging

logger = logging.getLogger(__name__)


def _atomic_write(path, lines):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".", dir=directory, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


class accounts:
    accounts = {}
    aliases = {}
    members = []
    newaccount = ""
    adduseralias = ""
    checkout_balances = {}
    write_lock = threading.Lock()

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.accounts = {}
        self.aliases = {}
        self.members = []
        self.newaccount = ""
        self.adduseralias = ""
        self.checkout_balances = {}

    def help(self):
        return {
            "addmember": "Add user to members",
            "adduseralias": "Add user key alias",
            "delmember": "Remove user from members",
            "members": "Manage members",
        }

    def get_last_updated_accounts(self):
        logger.debug("accounts_state sid=%s accounts=%s", self.SID, self.accounts)
        # Sort the accounts based on last update time, in descending order
        sorted_accounts = sorted(
            self.accounts.items(), key=lambda x: x[1]["lastupdate"], reverse=True
        )
        # Extract the account names from the sorted list
        visible_members = self.visible_members()
        account_names = [
            account[0]
            for account in sorted_accounts
            if account[0] not in visible_members
        ][0:125]
        self.master.send_message(True, "nonmembers", json.dumps(account_names))

    # Internal functions
    def readaccounts(self):
        self.accounts = {}
        self.aliases = {}
        with codecs.open("data/revbank.accounts", "r", "utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            self.accounts[parts[0]] = {
                "amount": float(parts[1]),
                "lastupdate": parts[2],
            }
        with codecs.open("data/revbank.aliases", "r", "utf-8") as f:
            y = f.readlines()
            for x in y:
                if not x.strip() or x.lstrip().startswith("#"):
                    continue
                s = x.split()
                if len(s) == 2:
                    self.aliases[s[0]] = s[1]

    def readmembers(self):
        with open("data/revbank.members", encoding="utf-8") as f:
            self.members = [
                member.strip()
                for member in f.readlines()
                if member.strip() and not member.lstrip().startswith("#")
            ]

    def visible_members(self):
        plugins = getattr(self.master, "plugins", {})
        if isinstance(plugins, dict):
            party = plugins.get("party")
            if party is not None:
                member_override = getattr(party, "member_override", None)
                if member_override is not None:
                    override = member_override()
                    if override is not None:
                        return override
        return list(self.members)

    def _writemembers(self):
        with self.write_lock:
            _atomic_write(
                "data/revbank.members", ["%s\n" % member for member in self.members]
            )

    def _publish_members(self):
        self.get_last_updated_accounts()
        self.master.send_message(True, "members", json.dumps(self.visible_members()))

    def updateaccount(self, usr, value):
        logger.debug("update_account sid=%s user=%s value=%s", self.SID, usr, value)
        if usr == "cash":
            return
        had = self.accounts[usr]["amount"]
        self.accounts[usr]["amount"] += value
        has = self.accounts[usr]["amount"]
        self.accounts[usr]["lastupdate"] = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.master.callhook("balance", (usr, had, has, self.master.transID))

    def writeaccount(self):
        with self.write_lock:
            _atomic_write(
                "data/revbank.accounts",
                [
                    "%-18s %+7.2f %s\n"
                    % (usr, round(account["amount"], 2), account["lastupdate"])
                    for usr, account in self.accounts.items()
                ],
            )
            _atomic_write(
                "data/revbank.aliases",
                ["%s %s\n" % (usr, alias) for usr, alias in self.aliases.items()],
            )

    # Hooks
    def hook_balance(self, args):
        usr, _had, _has, _transID = args
        self.master.send_message(
            False, "infobox/account/" + usr, json.dumps(self.accounts[usr])
        )
        self.master.send_message(
            True, "accounts/" + usr, json.dumps(self.accounts[usr])
        )

    def hook_endsession(self, _text):
        self.writeaccount()
        self.get_last_updated_accounts()

    def hook_abort(self, _void):
        self.readaccounts()
        self.get_last_updated_accounts()
        for name, account in self.accounts.items():
            self.master.send_message(True, "accounts/" + name, json.dumps(account))

    def createnew(self, text):
        if text == "yes":
            self.accounts[self.newaccount] = {
                "amount": 0,
                "lastupdate": time.strftime("%Y-%m-%d_%H:%M:%S"),
            }
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
        self.readmembers()
        self.get_last_updated_accounts()
        for name, account in self.accounts.items():
            self.master.send_message(True, "accounts/" + name, json.dumps(account))
        self.master.send_message(True, "members", json.dumps(self.visible_members()))

    def hook_pre_checkout(self, _text):
        self.readaccounts()
        self.checkout_balances = {
            usr: account["amount"] for usr, account in self.accounts.items()
        }
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

    def _messageandcustom(self, donext, custom, msg):
        self.master.donext(self, donext)
        self.master.send_message(True, "message", msg)
        self.master.send_message(
            True, "buttons", json.dumps({"special": "custom", "custom": custom})
        )
        return True

    def _membersmenu(self):
        custom = [
            {"text": "addmember", "display": "Add member"},
            {"text": "delmember", "display": "Remove member"},
        ]
        self.master.send_message(True, "message", "Please select a members command")
        self.master.send_message(
            True, "buttons", json.dumps({"special": "custom", "custom": custom})
        )
        return True

    def _addmember(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        if text not in self.accounts:
            return self.messageandbuttons(
                "_addmember",
                "accounts",
                "Unknown account; What user do you want to add?",
            )
        if text in self.members:
            return self.messageandbuttons(
                "_addmember",
                "accounts",
                "Already a member; What user do you want to add?",
            )
        self.members.append(text)
        self._writemembers()
        self._publish_members()
        self.master.send_message(True, "message", "Member added: " + text)
        return True

    def _delmember(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        if text not in self.members:
            custom = [{"text": member, "display": member} for member in self.members]
            return self._messageandcustom(
                "_delmember",
                custom,
                "Unknown member; What member do you want to remove?",
            )
        self.members.remove(text)
        self._writemembers()
        self._publish_members()
        self.master.send_message(True, "message", "Member removed: " + text)
        return True

    def _delmember_prompt(self):
        custom = [{"text": member, "display": member} for member in self.members]
        return self._messageandcustom(
            "_delmember", custom, "What member do you want to remove?"
        )

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
        command_handlers = {
            "adduseralias": lambda: self.messageandbuttons(
                "askalias", "accounts", "What user do you want to alias?"
            ),
            "members": self._membersmenu,
            "addmember": lambda: self.messageandbuttons(
                "_addmember", "accounts", "What user do you want to add?"
            ),
            "delmember": self._delmember_prompt,
        }
        if text in command_handlers:
            return command_handlers[text]()
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
