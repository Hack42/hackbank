# -*- coding: utf-8 -*-
import json
import math
import time
import pickle
import serial

DISPLAY = "\x1B=\x02\x1B@"
PRINTER = "\x1B=\x01\x1B@"
LARGE = "\x1D!\x11"
NORMAL = "\x1D!\x00"
SMALL = "\x1B!\x01"

CENTER = "\x1Ba1"
RIGHT = "\x1Ba2"
LEFT = "\x1Ba0"
LOGO = "\x1Cp\x01\x03"
FEED = "\n\n\n\n\n"
BARCODE_T = "\x1DH\x00"  # text around the barcode
BARCODE_H = "\x1Dh\x60"  # 40 height
BARCODE_W = "\x1Dw\x60"  # 2 Width

BARCODE = "\x1Dk\x47%cA%dA\n"

CUT = "\x1Bm\n"

DRAWER = "\x1B\x700AA"


class POS:
    bonnetjes = {}
    ser = None

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def open(self):
        if self.ser != None:
            return
        self.ser = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        print "Serial open"

    def help(self):
        return {"bon": "Print Receipt", "bons": "Receipts to print", "kassala": "Open cash drawer", "printstock": "Print stock overview"}

    def printstock(self):
        BON = PRINTER + LARGE + CENTER + LOGO + NORMAL + LEFT
        for name in sorted(self.master.stock.stock.keys()):
            num = self.master.stock.stock[name]
            BON += "%20s %5d\n" % (name, num)
        BON += LEFT + FEED + CUT
        self.open()
        self.slowwrite(BON)

    def printdisplay(self, desc, amount, som):
        self.open()
        self.ser.write(DISPLAY + "%-14s% 6.2f%-12s% 8.2f" % (desc[0:14], amount, "Total", som))

    def hook_checkout(self, user):
        if user is 'cash':
            self.drawer()

    def hook_addremove(self, args):
        # Update display
        pass

    def drawer(self):
        self.open()
        self.ser.write(PRINTER + DRAWER)

    def hook_undo(self, (transID, void1, void2, void3)):
        self.loadbons()
        if transID in self.bonnetjes:
            self.bonnetjes[transID]['bon'] = PRINTER + LARGE + "\nVOID VOID VOID\nVOID VOID VOID\n" + self.bonnetjes[transID]['bon']
            self.writebons()

    def makebon(self, user):
        BON = PRINTER + LARGE + CENTER + LOGO
        if (self.master.accounts.accounts[user]['amount'] + self.master.receipt.totals[user]) < -13.37:
            BON += "SALDO TE LAAG\n"
        BON += NORMAL + "Bon transactie %d\n" % self.master.transID
        BON += BARCODE_T + BARCODE_H + BARCODE_W + BARCODE % (len(str(self.master.transID)) + 2, self.master.transID)
        BON += RIGHT + "%s  -  Arnhem\n" % time.strftime('%Y-%m-%d %H:%M:%S')
        BON += LEFT + "\n" + " %-26s%12s\n " % ("Product", "Aantal   EUR")
        BON += "-" * 38 + "\n"
        for r in self.master.receipt.receipt:
            if r['beni'] == user:
                if len(r['description']) > 25:
                    end = 0
                    while end < len(r['description']):
                        start = end
                        end += 24
                        desc = r['description'][start:end - 1]
                        if start == 0:
                            BON += " %-26s % 3d % 7.2f\n" % (desc, r['count'], r['total'])
                        else:
                            BON += " %-26s\n" % desc
                else:
                    BON += " %-26s % 3d % 7.2f\n" % (r['description'], r['count'], r['total'])
        BON += " " + "-" * 38 + "\n"
        BON += " %-26s% 12.2f\n" % ("Totaal", self.master.receipt.totals[user])
        BON += "\nU bent geholpen door: %s\n" % user
        if user != 'cash':
            BON += "\n         Nieuw saldo: %5.2f\n" % (self.master.accounts.accounts[user]['amount'])
        BON += "\n" + CENTER + SMALL + "De kleine lettertjes: Deze bon kan niet in de       \n" + \
            "hack42 adminstratie gebruikt worden voor declaraties\n"
        BON += LEFT + FEED + CUT
        return BON

    def printdeclaratie(self, (Name, Type, Reason, Bar, Cash, Bank)):
        BON = PRINTER + LARGE + CENTER + LOGO
        BON += NORMAL + "Declaratie\n\n" + RIGHT + "%s  -  Arnhem\n" % time.strftime('%Y-%m-%d %H:%M:%S')
        BON += LEFT + "\n\n"
        BON += "Naam:   %s\n" % Name
        BON += "Type:   %s\n" % Type
        BON += "Reason:   %s\n" % Reason
        BON += "Bartegoed:   %.2f\n" % Bar
        BON += "Cash Geld:   %.2f\n" % Cash
        BON += "Via Bank:    %.2f\n" % Bank
        BON += "Handtekening:\n\n\n\n------------------------------------\n" + CENTER + SMALL + \
            "De kleine lettertjes: Deze bon kan juist wel in de  \nhack42 adminstratie gebruikt worden voor declaraties\n"
        BON += LEFT + FEED + CUT
        self.open()
        self.slowwrite(BON)

    def hook_post_checkout(self, user):
        self.loadbons()
        BON = ""
        for usr in self.master.receipt.totals:
            BON += self.makebon(usr)
        self.bonnetjes[self.master.transID] = {"totals": self.master.receipt.totals, "bon": BON}
        self.lastbonID = self.master.transID
        self.writebons()
        if user is 'cash':
            self.drawer()
        else:
            for r in self.master.receipt.receipt:
                if r['product'] == 'deposit':
                    self.drawer()
                    break

    def slowwrite(self, y):
        for bla in [y[i:i + 32] for i in range(0, len(y), 32)]:
            self.ser.write(bla)
            time.sleep(0.05)

    def bon(self, bonID):
        if bonID in self.bonnetjes:
            self.open()
            self.slowwrite(self.bonnetjes[bonID]['bon'])
        return True

    def selectbon(self, text):
        if text == "abort":
            self.master.callhook('abort', None)
            return True
        try:
            bonID = int(text)
            if bonID in self.bonnetjes:
                self.bon(bonID)
                return True
            else:
                self.listbons()
                return True
        except:
            import traceback
            traceback.print_exc()
            self.listbons()
            return True

    def writebons(self):
        while len(self.bonnetjes) > 50:
            fk = sorted(self.bonnetjes.keys())
            del self.bonnetjes[fk[0]]

        output = open('data/revbank.POS', 'wb')
        pickle.dump(self.bonnetjes, output)
        output.close()

    def loadbons(self):
        try:
            with open('data/revbank.POS', 'rb') as f:
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
            for usr in self.bonnetjes[bonID]['totals'].keys():
                txt += usr + " €" + "%.2f" % self.bonnetjes[bonID]['totals'][usr] + " "
            txt += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bonID + 1300000000))
            custom.append({'text': bonID, 'display': txt})
            count += 1
            if count > 49:
                break
        self.master.send_message(True, 'buttons', json.dumps({'special': 'custom', 'custom': custom, 'sort': 'text'}))
        self.master.send_message(True, 'message', 'Select a receipt')
        self.master.donext(self, 'selectbon')

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

    def startup(self):
        self.loadbons()
