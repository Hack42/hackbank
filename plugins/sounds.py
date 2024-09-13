# -*- coding: utf-8 -*-
import json


class sounds:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"sounds": "All sound commands"}

    def hook_checkout(self, _text):
        for r in self.master.receipt.receipt:
            if r["product"] == "deposit":
                self.master.send_message(False, "sound", "itsgone.wav")
                break
        self.master.send_message(False, "sound", "katsjing.wav")

    def hook_balance(self, args):
        (_usr, _had, has, _transID) = args
        if has < -13.37:
            self.master.send_message(False, "sound", "sinterklaas.wav")

    def hook_undo(self, args):
        (_transID, _totals, _receipt, _beni) = args

    def showsounds(self):
        custom = []
        custom.append({"text": "abort", "display": "Abort"})
        custom.append({"text": "ns", "display": "Ding Dong"})
        custom.append({"text": "deuron", "display": "Deur on"})
        custom.append({"text": "deuroff", "display": "Deur off"})
        custom.append({"text": "kassaon", "display": "Kassa on"})
        custom.append({"text": "kassaoff", "display": "Kassa off"})
        custom.append({"text": "killsounds", "display": "Kill Music"})
        custom.append({"text": "groovesalad", "display": "Groove Salad"})
        custom.append({"text": "christmas", "display": "christmas"})
        custom.append({"text": "blues", "display": "Jazz Radio Blues"})
        custom.append({"text": "quieter", "display": "Quieter"})
        custom.append({"text": "louder", "display": "Louder"})
        custom.append({"text": "vergaderen", "display": "Vergaderen!"})
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
        if text == "ns":
            self.master.send_message(False, "sound", "ns.wav")
            return True
        if text == "vergaderen":
            self.master.send_message(False, "sound", "vergaderen.mp3")
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
        if text != "abort":
            self.master.send_message(False, "sound", "KDE_Beep_ClassicBeep.wav")

    def hook_wrong(self, _text):
        self.master.send_message(False, "sound", "KDE_Beep_Beep.wav")
        self.master.send_message(False, "sound", "KDE_Beep_Beep.wav")

    def startup(self):
        pass
