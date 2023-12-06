#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import math


class take:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"take": "Take money from other user(s)"}

    def who(self, text):
        if text in self.master.accounts.accounts:
            self.totakefrom.append(text)
            self.master.donext(self, "who")
            self.master.send_message(
                True,
                "message",
                "User to take from or amount to end? ("
                + ", ".join(self.totakefrom)
                + ")",
            )
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accountsamount"})
            )
            return True
        elif text == "abort":
            self.master.callhook("abort", None)
            return True
        elif len(self.totakefrom) > 0:
            try:
                value = round(float(text), 2)
                if value > 0 and value < 1000:
                    self.value = value
                    self.peruser = (
                        math.ceil((self.value / len(self.totakefrom)) * 100) / 100
                    )
                    self.master.donext(self, "reason")
                    self.master.send_message(
                        True,
                        "message",
                        "Why are you taking E"
                        + str(self.value)
                        + " from "
                        + str(len(self.totakefrom))
                        + " users? ( E"
                        + str(self.peruser)
                        + " per user)",
                    )
                    self.master.send_message(
                        True, "buttons", json.dumps({"special": "keyboard"})
                    )
                else:
                    self.master.donext(self, "who")
                    self.master.send_message(
                        True, "message", "Enter an amount between 0.01 and 999.99:"
                    )
                    self.master.send_message(
                        True, "buttons", json.dumps({"special": "numbers"})
                    )
                return True
            except:
                import traceback

                traceback.print_exc()
        self.master.donext(self, "who")
        self.master.send_message(
            True,
            "message",
            "Unknown User; User to take from? (" + ", ".join(self.totakefrom) + ")",
        )
        self.master.send_message(
            True, "buttons", json.dumps({"special": "accountsamount"})
        )
        return True

    def reason(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        self.myreason = text
        vanline = ""
        for van in self.totakefrom:
            self.master.receipt.add(
                True,
                self.peruser,
                "Taken by -you- (" + self.myreason + ")",
                1,
                van,
                "take",
            )
            if vanline != "":
                vanline += ", "
            vanline += van
        self.master.receipt.add(
            False,
            self.peruser * len(self.totakefrom),
            "Taken from " + vanline + " (" + self.myreason + ")",
            1,
            None,
            "take",
        )
        return True

    def input(self, text):
        if text == "take":
            self.totakefrom = []
            self.master.donext(self, "who")
            self.master.send_message(True, "message", "User to take from?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True

    def startup(self):
        pass
