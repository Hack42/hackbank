# -*- coding: utf-8 -*-
import traceback
import json
import time
import pickle
import serial

DISPLAY = b"\x1B=\x02\x1B@"
PRINTER = b"\x1B=\x01\x1B@"
LARGE = b"\x1D!\x11"
NORMAL = b"\x1D!\x00"
SMALL = b"\x1B!\x01"

CENTER = b"\x1Ba1"
RIGHT = b"\x1Ba2"
LEFT = b"\x1Ba0"
LOGO = b"\x1Cp\x01\x03"
FEED = b"\n\n\n\n\n"
BARCODE_T = b"\x1DH\x00"  # text around the barcode
BARCODE_H = b"\x1Dh\x60"  # 40 height
BARCODE_W = b"\x1Dw\x60"  # 2 Width

BARCODE = b"\x1Dk\x47%cA%dA\n"

CUT = b"\x1Bm\n"

DRAWER = b"\x1B\x700AA"


class POS:
    bonnetjes = {}
    ser = None
    lastbonID = 0

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def open(self):
        if self.ser is not None:
            return
        self.ser = serial.Serial(  # pylint: disable=no-member
            port="/dev/ttyUSB0",  # pylint: disable=no-member
            baudrate=19200,  # pylint: disable=no-member
            parity=serial.PARITY_NONE,  # pylint: disable=no-member
            stopbits=serial.STOPBITS_ONE,  # pylint: disable=no-member
            bytesize=serial.EIGHTBITS,  # pylint: disable=no-member
        )
        print("Serial open")

    def help(self):
        return {
            "bon": "Print Receipt",
            "bons": "Receipts to print",
            "kassala": "Open cash drawer",
            "printstock": "Print stock overview",
        }

    def printstock(self):
        BON = PRINTER + LARGE + CENTER + LOGO + NORMAL + LEFT
        for name in sorted(self.master.stock.stock.keys()):
            num = self.master.stock.stock[name]
            BON += b"%20s %5d\n" % (name.encode(), num)
        BON += LEFT + FEED + CUT
        self.open()
        self.slowwrite(BON)

    def printdisplay(self, desc, amount, som):
        self.open()
        out = DISPLAY + b"%-14s% 6.2f%-12s% 8.2f" % (
            desc[0:14].encode(),
            amount,
            b"Total",
            som,
        )
        self.ser.write(out)

    def hook_checkout(self, user):
        if user == "cash":
            self.drawer()

    def hook_addremove(self, args):
        # Update display
        pass

    def drawer(self):
        self.open()
        self.ser.write(PRINTER + DRAWER)

    def hook_undo(self, args):
        (transID, _void1, _void2, _void3) = args
        self.loadbons()
        if transID in self.bonnetjes:
            self.bonnetjes[transID]["bon"] = (
                PRINTER
                + LARGE
                + b"\nVOID VOID VOID\nVOID VOID VOID\n"
                + self.bonnetjes[transID]["bon"]
            )
            self.writebons()

    def makebon(self, user):
        BON = PRINTER + LARGE + CENTER + LOGO
        if (
            self.master.accounts.accounts[user]["amount"]
            + self.master.receipt.totals[user]
        ) < -13.37:
            BON += b"SALDO TE LAAG\n"
        BON += NORMAL + b"Bon transactie %d\n" % self.master.transID
        BON += (
            BARCODE_T
            + BARCODE_H
            + BARCODE_W
            + BARCODE % (len(str(self.master.transID)) + 2, self.master.transID)
        )
        BON += RIGHT + b"%s  -  Arnhem\n" % time.strftime("%Y-%m-%d %H:%M:%S").encode()
        BON += LEFT + b"\n" + b" %-26s%12s\n " % (b"Product", b"Aantal   EUR")
        BON += b"-" * 38 + b"\n"
        for r in self.master.receipt.receipt:
            if r["beni"] == user:
                if len(r["description"]) > 25:
                    end = 0
                    while end < len(r["description"]):
                        start = end
                        end += 24
                        desc = r["description"][start : end - 1]
                        if start == 0:
                            BON += b" %-26s % 3d % 7.2f\n" % (
                                desc.encode(),
                                r["count"],
                                r["total"],
                            )
                        else:
                            BON += b" %-26s\n" % desc.encode()
                else:
                    BON += b" %-26s % 3d % 7.2f\n" % (
                        r["description"].encode(),
                        r["count"],
                        r["total"],
                    )
        BON += b" " + b"-" * 38 + b"\n"
        BON += b" %-26s% 12.2f\n" % (b"Totaal", self.master.receipt.totals[user])
        BON += b"\nU bent geholpen door: %s\n" % user.encode()
        if user != b"cash":
            BON += b"\n         Nieuw saldo: %5.2f\n" % (
                self.master.accounts.accounts[user]["amount"]
            )
        BON += (
            b"\n"
            + CENTER
            + SMALL
            + b"De kleine lettertjes: Deze bon kan niet in de       \n"
            + b"hack42 adminstratie gebruikt worden voor declaraties\n"
        )
        BON += LEFT + FEED + CUT
        return BON

    def printdeclaratie(self, args):
        (Name, Type, Reason, Bar, Cash, Bank) = args
        BON = PRINTER + LARGE + CENTER + LOGO
        BON += (
            NORMAL
            + b"Declaratie\n\n"
            + RIGHT
            + b"%s  -  Arnhem\n" % time.strftime("%Y-%m-%d %H:%M:%S").encode()
        )
        BON += LEFT + b"\n\n"
        BON += b"Naam:   %s\n" % Name.encode()
        BON += b"Type:   %s\n" % Type.encode()
        BON += b"Reason:   %s\n" % Reason.encode()
        BON += b"Bartegoed:   %.2f\n" % Bar
        BON += b"Cash Geld:   %.2f\n" % Cash
        BON += b"Via Bank:    %.2f\n" % Bank
        BON += (
            b"Handtekening:\n\n\n\n------------------------------------\n"
            + CENTER
            + SMALL
            + b"De kleine lettertjes: Deze bon kan juist wel in de  \n"
            + b"hack42 adminstratie gebruikt worden voor declaraties\n"
        )
        BON += LEFT + FEED + CUT
        self.open()
        self.slowwrite(BON)

    def hook_post_checkout(self, user):
        self.loadbons()
        BON = b""
        for usr in self.master.receipt.totals:
            BON += self.makebon(usr)
        self.bonnetjes[self.master.transID] = {
            "totals": self.master.receipt.totals,
            "bon": BON,
        }
        self.lastbonID = self.master.transID
        self.writebons()
        if user == "cash":
            self.drawer()
        else:
            for r in self.master.receipt.receipt:
                if r["product"] == "deposit":
                    self.drawer()
                    break

    def slowwrite(self, y):
        for bla in [y[i : i + 32] for i in range(0, len(y), 32)]:
            self.ser.write(bla)
            time.sleep(0.05)

    def bon(self, bonID):
        if bonID in self.bonnetjes:
            self.open()
            self.slowwrite(self.bonnetjes[bonID]["bon"].encode())
            return True
        return False

    def selectbon(self, text):
        if text == "abort":
            self.master.callhook("abort", None)
            return True
        try:
            bonID = int(text)
            if bonID in self.bonnetjes:
                self.bon(bonID)
                return True
            self.listbons()
            return True
        except:
            traceback.print_exc()
            self.listbons()
            return True

    def writebons(self):
        while len(self.bonnetjes) > 50:
            fk = sorted(self.bonnetjes.keys())
            del self.bonnetjes[fk[0]]

        with open("data/revbank.POS", "wb") as output:
            pickle.dump(self.bonnetjes, output)

    def loadbons(self):
        try:
            with open("data/revbank.POS", "rb") as f:
                self.bonnetjes = pickle.load(f)
                f.close()
        except:
            pass

    def listbons(self):
        self.loadbons()
        custom = []
        count = 0
        for bonID in sorted(self.bonnetjes.keys(), reverse=True):
            txt = ""
            for usr in self.bonnetjes[bonID]["totals"].keys():
                txt += usr + " €" + "%.2f" % self.bonnetjes[bonID]["totals"][usr] + " "
            txt += time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(bonID + 1300000000)
            )
            custom.append({"text": bonID, "display": txt})
            count += 1
            if count > 49:
                break
        self.master.send_message(
            True,
            "buttons",
            json.dumps({"special": "custom", "custom": custom, "sort": "text"}),
        )
        self.master.send_message(True, "message", "Select a receipt")
        self.master.donext(self, "selectbon")

    def input(self, text):
        if text == "bon":
            self.bon(self.lastbonID)
            return True
        if text == "bons":
            self.listbons()
            return True
        if text == "kassala":
            self.drawer()
            return True
        if text == "printstock":
            self.printstock()
            return True
        return None

    def startup(self):
        self.loadbons()
