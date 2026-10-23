# -*- coding: utf-8 -*-
import json
import logging
import re
from pos_sound_settings import POSSoundSettings

logger = logging.getLogger(__name__)

SOUND_SAMPLES = {
    "ns": "soundboard/ns.wav",
    "vergaderen": "soundboard/vergaderen.mp3",
    "vergaderenextreme": "soundboard/vergaderen_extreme.wav",
    "vergaderen_extreme": "soundboard/vergaderen_extreme.wav",
    "throw": "soundboard/throw.wav",
    "yeet": "soundboard/yeet.wav",
}


class sounds:
    def __init__(self, SID, master, settings=None):
        self.master = master
        self.SID = SID
        self.settings = settings or POSSoundSettings()

    def help(self):
        return {"sounds": "All sound commands"}

    def hook_checkout(self, _text):
        for r in self.master.receipt.receipt:
            if r["product"] == "deposit":
                self.master.send_message(
                    False, "sound", self.settings.sample("deposit")
                )
                break
        self.master.send_message(False, "sound", self.settings.sample("sale"))

    def hook_balance(self, args):
        _usr, _had, has, _transID = args
        if has < -13.37:
            self.master.send_message(
                False, "sound", self.settings.sample("insufficient_funds")
            )

    def hook_undo(self, args):
        _transID, _totals, _receipt, _beni = args

    def showsounds(self):
        custom = []
        custom.append({"text": "ns", "display": "Ding Dong"})
        custom.append({"text": "deuron", "display": "Deur on"})
        custom.append({"text": "deuroff", "display": "Deur off"})
        custom.append({"text": "kassaon", "display": "Kassa on"})
        custom.append({"text": "kassaoff", "display": "Kassa off"})
        custom.append({"text": "killsounds", "display": "Kill Music"})
        custom.append({"text": "groovesalad", "display": "Groove Salad"})
        custom.append({"text": "blues", "display": "Jazz Radio Blues"})
        custom.append({"text": "quieter", "display": "Quieter"})
        custom.append({"text": "louder", "display": "Louder"})
        custom.append({"text": "vergaderen", "display": "Vergaderen!"})
        custom.append({"text": "vergaderenextreme", "display": "Vergaderen Extreme"})
        custom.append({"text": "throw", "display": "Throw"})
        custom.append({"text": "yeet", "display": "Yeet"})
        self.master.send_message(
            True, "buttons", json.dumps({"special": "custom", "custom": custom})
        )
        self.master.send_message(True, "message", "Please select a command")

    def input(
        self, text
    ):  # pylint: disable=too-many-return-statements, too-many-branches
        if text == "sounds":
            self.showsounds()
            return True
        if text in SOUND_SAMPLES:
            self.master.send_message(False, "sound", SOUND_SAMPLES[text])
            return True
        if text == "deuron":
            pass
        if text == "deuroff":
            pass
        if text == "kassaon":
            pass
        if text == "kassaoff":
            pass
        if text == "killsounds":
            self.master.send_message(False, "groove", "off")
            return True
        if text == "groovesalad":
            self.master.send_message(False, "groove", "on")
            return True
        if text == "christmas":
            self.master.send_message(False, "christmas", "on")
            return True
        if text == "blues":
            self.master.send_message(False, "blues", "on")
            return True
        if text == "louder":
            self.master.send_message(False, "vol", "up")
            return True
        if text == "quieter":
            self.master.send_message(False, "vol", "down")
            return True
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        return None

    def pre_input(self, text):
        command = text.strip()
        if command not in ("abort", "sounds") and command not in SOUND_SAMPLES:
            self.master.send_message(False, "sound", self.settings.sample("command"))

    def hook_wrong(self, _text):
        self.master.send_message(False, "sound", self.settings.sample("error"))
        self.master.send_message(False, "sound", self.settings.sample("error"))

    def publish_settings(self, state=None):
        state = state or self.settings.state()
        self.master.client.publish(
            "hack42bar/output/settings/sounds", json.dumps(state), qos=1, retain=True
        )

    def configure(self, payload):
        request_id = ""
        try:
            if len(payload) > 512:
                raise ValueError("Invalid sound setting.")
            request = json.loads(payload)
            if not isinstance(request, dict):
                raise ValueError("Invalid sound setting.")
            request_id = request.get("request", "")
            if not isinstance(request_id, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,80}", request_id
            ):
                raise ValueError("Invalid sound request.")
            preview = None
            if set(request) == {"request"}:
                state = self.settings.state()
            elif set(request) == {"request", "feature", "sound"}:
                state = self.settings.set(request["feature"], request["sound"])
                preview = request["feature"]
            elif set(request) == {"request", "preview"}:
                state = self.settings.state()
                preview = request["preview"]
                if not isinstance(preview, str) or not any(
                    item["id"] == preview for item in state["features"]
                ):
                    raise ValueError("Unknown POS sound feature.")
            elif set(request) == {"request", "reset"}:
                feature = request["reset"]
                if not isinstance(feature, str):
                    raise ValueError("Invalid sound feature.")
                state = self.settings.reset(None if feature == "all" else feature)
                preview = "command" if feature == "all" else feature
            else:
                raise ValueError("Invalid sound setting.")
            self.publish_settings(state)
            self.master.send_message(
                False,
                "sound_settings",
                json.dumps(
                    {
                        "request": request_id,
                        "ok": True,
                        "settings": state,
                    }
                ),
            )
            if preview:
                self.master.send_message(False, "sound", self.settings.sample(preview))
        except (ValueError, TypeError, OSError) as error:
            logger.warning("sound_settings_failed sid=%s error=%s", self.SID, error)
            message = (
                str(error)
                if isinstance(error, ValueError)
                else "Sound settings could not be saved. Please try again."
            )
            self.master.send_message(
                False,
                "sound_settings",
                json.dumps(
                    {
                        "request": request_id,
                        "ok": False,
                        "error": message,
                    }
                ),
            )

    def startup(self):
        self.publish_settings()
