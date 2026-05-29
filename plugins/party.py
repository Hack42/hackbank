import json
import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

PARTY_USER = "party"
STATE_FILE = "data/revbank.party"


def _atomic_write(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".", dir=directory, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


class party:
    active = False
    started_amount = 0.0
    started_at = ""

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID
        self.active = False
        self.started_amount = 0.0
        self.started_at = ""

    def help(self):
        return {
            "partymodeon": "Enable party mode",
            "partymodeoff": "Disable party mode",
        }

    def member_override(self):
        if self.active:
            return [PARTY_USER]
        return None

    def loadstate(self):
        self.active = False
        self.started_amount = 0.0
        self.started_at = ""
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.active = bool(data.get("active", False))
            self.started_amount = float(data.get("started_amount", 0.0))
            self.started_at = str(data.get("started_at", ""))
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("party_state_load_failed sid=%s error=%s", self.SID, exc)

    def writestate(self):
        _atomic_write(
            STATE_FILE,
            {
                "active": self.active,
                "started_amount": self.started_amount,
                "started_at": self.started_at,
            },
        )

    def _ensure_party_account(self):
        accounts = self.master.accounts
        if PARTY_USER not in accounts.accounts:
            accounts.accounts[PARTY_USER] = {
                "amount": 0.0,
                "lastupdate": time.strftime("%Y-%m-%d_%H:%M:%S"),
            }
            accounts.writeaccount()
        self.master.send_message(
            True, "accounts/" + PARTY_USER, json.dumps(accounts.accounts[PARTY_USER])
        )
        return float(accounts.accounts[PARTY_USER]["amount"])

    def _publish_members(self):
        self.master.accounts.publish_members()

    def _enable(self):
        self.loadstate()
        self.master.accounts.readaccounts()
        current_amount = self._ensure_party_account()
        if self.active:
            self._publish_members()
            self.master.send_message(True, "message", "Party mode is already on")
            return True
        self.active = True
        self.started_amount = current_amount
        self.started_at = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.writestate()
        self._publish_members()
        self.master.send_message(
            True,
            "message",
            "Party mode on; started with EUR %.2f" % self.started_amount,
        )
        return True

    def _disable(self):
        self.loadstate()
        if not self.active:
            self.master.send_message(True, "message", "Party mode is not on")
            return True
        self.master.accounts.readaccounts()
        current_amount = self._ensure_party_account()
        settled_amount = round(self.started_amount - current_amount, 2)
        try:
            self.master.POS.printparty(
                self.started_amount,
                current_amount,
                settled_amount,
                self.started_at,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("party_receipt_print_failed sid=%s", self.SID)
            self.master.send_message(
                True,
                "message",
                "Party mode receipt print failed: %s" % exc,
            )
            return True

        self.active = False
        self.writestate()
        self._publish_members()
        self.master.send_message(
            True,
            "message",
            "Party mode off; started EUR %.2f, left EUR %.2f, settled EUR %.2f"
            % (self.started_amount, current_amount, settled_amount),
        )
        return True

    def input(self, text):
        if text == "partymodeon":
            return self._enable()
        if text == "partymodeoff":
            return self._disable()
        return None

    def startup(self):
        self.loadstate()
        if self.active:
            self.master.accounts.readaccounts()
            self._ensure_party_account()
            self._publish_members()
