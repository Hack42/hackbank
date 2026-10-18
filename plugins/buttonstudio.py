"""Separate UI settings route: never consumes a POS command or pending question."""

import json
import logging
import re
from urllib.parse import quote

from button_themes import ButtonThemes, MAX_REQUEST

logger = logging.getLogger(__name__)


class buttonstudio:
    def __init__(self, SID, master, store=None):
        self.SID = SID
        self.master = master
        self.store = store or ButtonThemes()

    def help(self):
        return {}

    def publish(self, user, theme):
        self.master.client.publish(
            "hack42bar/output/settings/buttons/" + quote(user, safe=""),
            json.dumps({"user": user, "theme": theme}),
            qos=1,
            retain=True,
        )

    def startup(self):
        for user, theme in self.store.all().items():
            self.publish(user, theme)

    def configure(self, payload):
        request_id = ""
        try:
            if len(payload) > MAX_REQUEST:
                raise ValueError("This button design is too large.")
            request = json.loads(payload)
            if not isinstance(request, dict):
                raise ValueError("Invalid button request.")
            request_id = request.get("request", "")
            if not isinstance(request_id, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,80}", request_id
            ):
                raise ValueError("Invalid button request.")
            if set(request) not in ({"request", "user"}, {"request", "user", "theme"}):
                raise ValueError("Invalid button request.")
            user = request["user"]
            if not isinstance(user, str) or user not in self.master.accounts.accounts:
                raise ValueError("Choose an existing user for this button.")
            if "theme" in request:
                theme = self.store.save(user, request["theme"])
            else:
                theme = self.store.all().get(user)
            self.publish(user, theme)
            reply = {"request": request_id, "ok": True, "user": user, "theme": theme}
        except (ValueError, TypeError, OSError) as error:
            logger.warning("button_studio_failed sid=%s error=%s", self.SID, error)
            reply = {
                "request": request_id,
                "ok": False,
                "error": (
                    str(error)
                    if isinstance(error, ValueError)
                    else "Your button could not be saved. Please try again."
                ),
            }
        self.master.send_message(False, "button_studio", json.dumps(reply))
