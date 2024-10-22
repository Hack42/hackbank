# -*- coding: utf-8 -*-
import os
import traceback
import json
import re
import time
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import pyqrcode
import cups


class stickers:
    SMALL = (690, 271)
    LOGOSMALLSIZE = (309, 200)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    LOGOFILE = "images/hack42.png"
    FONT = "images/arialbd.ttf"
    printer = "QL710W"
    printer = "QL710W"
    SPACE = (
        0  # spacing around qrcode, should be 4 but our printer prints on white labels
    )

    copies = 0
    barcode = ""
    name = ""
    price = 0
    description = ""
    datum = ""
    large = False

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        return {"stickers": "All sticker commands"}

    def barcodeprint(self):
        if re.compile("^[0-9A-Z]+$").match(self.barcode):
            print("Qrcode: alphanum")
            qrcode_image = pyqrcode.create(
                self.barcode, error="L", version=1, mode="alphanumeric"
            ).png_as_base64_str(scale=5)
        else:
            print("Qrcode: binary")
            qrcode_image = pyqrcode.create(
                self.barcode, error="L", version=2, mode="binary"
            ).png_as_base64_str(scale=5)

        # Create an image object
        img = Image.new("RGB", self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)

        # Load the QR code as an image
        qrcode_img = Image.open(io.BytesIO(base64.b64decode(qrcode_image)))

        # Calculate size for QR code
        size = self.SMALL[1] // (qrcode_img.size[0] + 2 * self.SPACE)
        qrcode_img = qrcode_img.resize(
            (size * qrcode_img.size[0], size * qrcode_img.size[1]),
            resample=Image.LANCZOS,  # pylint: disable=no-member
        )

        # Place QR code on the image
        img.paste(qrcode_img, (self.SPACE, self.SPACE))

        # Load a font
        font = ImageFont.truetype(self.FONT, 40)

        # Add text to the image
        draw.text((self.SMALL[1] + 10, 64), self.name, fill=self.BLACK, font=font)
        draw.text(
            (self.SMALL[1] + 10, 104), self.description, fill=self.BLACK, font=font
        )
        draw.text((self.SMALL[1] + 10, 200), self.price, fill=self.BLACK, font=font)
        draw.text(
            (self.SMALL[1] + 10, self.SMALL[1] - 16),
            "deze prijs kan varieren kijk op de kassa voor",
            fill=self.BLACK,
            font=font,
        )
        draw.text(
            (self.SMALL[1] + 10, self.SMALL[1] - 2),
            "meer informatie.",
            fill=self.BLACK,
            font=font,
        )

        # Save the image
        img.save("data/barcode.jpg", "JPEG", dpi=(300, 300))

        # Print the file
        cups.Connection().printFile(  # pylint: disable=no-member
            self.printer,
            "data/barcode.jpg",
            "Eigendom",
            {"copies": str(self.copies), "page-ranges": "1"},
        )

    def thtprint(self):
        # Create an image
        img = Image.new("RGB", self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)

        # Load the logo
        LOGO = Image.open(self.LOGOFILE)
        LOGO = LOGO.resize(
            self.LOGOSMALLSIZE, resample=Image.LANCZOS  # pylint: disable=no-member
        )

        # Paste the logo onto the image
        img.paste(LOGO, (0, 0))

        # Load a font
        font = ImageFont.truetype(self.FONT, 40)

        # Add text
        draw.text((0, self.SMALL[1] - 15), "THT Datum", fill=self.BLACK, font=font)
        font = ImageFont.truetype(self.FONT, 50)
        draw.text((320, 120), self.datum, fill=self.BLACK, font=font)

        # Save the image
        img.save("data/foodout.png")

        # Print the file
        cups.Connection().printFile(  # pylint: disable=no-member
            self.printer,
            "data/foodout.png",
            title="Voedsel",
            options={"copies": str(self.copies), "page-ranges": "1"},
        )

    def toolprint(self):
        if re.compile("^[0-9A-Z]+$").match(self.name):
            print("Qrcode: alphanum")
            qrcode_image = pyqrcode.create(
                self.name, error="L", version=1, mode="alphanumeric"
            ).png_as_base64_str(scale=5)
        else:
            print("Qrcode: binary")
            qrcode_image = pyqrcode.create(
                self.name, error="L", version=2, mode="binary"
            ).png_as_base64_str(scale=5)

        # Create an image object
        img = Image.new("RGB", self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)

        # Load the QR code as an image
        qrcode_img = Image.open(io.BytesIO(base64.b64decode(qrcode_image)))

        # Calculate size for QR code
        size = self.SMALL[1] // (qrcode_img.size[0] + 4 * self.SPACE)
        qrcode_img = qrcode_img.resize(
            (size * qrcode_img.size[0], size * qrcode_img.size[1]),
            resample=Image.LANCZOS,  # pylint: disable=no-member
        )

        # Place QR code on the image
        img.paste(qrcode_img, (self.SPACE, self.SPACE))

        # Load a font
        font = ImageFont.truetype(self.FONT, 40)

        # Add text to the image
        draw.text((64, self.SMALL[1]), self.name, fill=self.BLACK, font=font)

        # Save the image
        img.save("data/toollabel.jpg", "JPEG", dpi=(300, 300))

        # Print the file
        options={"copies": str(self.copies), "page-ranges": "1", "media": "media=custom_61.98x100mm_61.98x100mm"}
        cups.Connection().printFile(  # pylint: disable=no-member
            self.printer,
            "data/toollabel.jpg",
            title="Toollabel",
            options=options,
        )



    def eigendomprint(self):
        img = Image.new("RGB", self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)

        LOGO = Image.open(self.LOGOFILE)
        LOGO = LOGO.resize(
            self.LOGOSMALLSIZE, resample=Image.LANCZOS  # pylint: disable=no-member
        )
        img.paste(LOGO, (0, 0))

        first = 10
        last = 190
        step = (last-first)/5

        steps = [10+step*i for i in range(0,6)]


        font = ImageFont.truetype(self.FONT, 40)
        draw.text((0, self.SMALL[1] - 55), self.name, fill=self.BLACK, font=font)
        font = ImageFont.truetype(self.FONT, 30)
        draw.text((320, steps[0]-1), "Don't                           Ask", fill=self.BLACK, font=font)
        draw.text((320, steps[0]-0), "Don't                           Ask", fill=self.BLACK, font=font)
        draw.text((320, steps[1]-1), "☐          Look ", fill=self.BLACK, font=font)
        draw.text((321, steps[1]-0), "☐", fill=self.BLACK, font=font)
        draw.text((320, steps[2]-1), "☐          Hack ", fill=self.BLACK, font=font)
        draw.text((321, steps[2]-0), "☐", fill=self.BLACK, font=font) 
        draw.text((320, steps[3]-1), "☐          Repair ", fill=self.BLACK, font=font)
        draw.text((321, steps[3]-0), "☐", fill=self.BLACK, font=font)
        draw.text((320, steps[4]-1), "☐          Destroy ", fill=self.BLACK, font=font)
        draw.text((321, steps[4]-0), "☐", fill=self.BLACK, font=font)
        draw.text((320, steps[5]-1), "☐          Steal  ", fill=self.BLACK, font=font)
        draw.text((321, steps[5]-0), "☐", fill=self.BLACK, font=font)
        for mystep in steps[1:]:
            draw.text((650, mystep-1), "☐", fill=self.BLACK, font=font)
            draw.text((651, mystep-0), "☐", fill=self.BLACK, font=font)
        img.save("data/output.jpg", "JPEG", dpi=(300, 300))
        if self.large:
            options={"copies": str(self.copies), "page-ranges": "1", "media": "media=custom_61.98x100mm_61.98x100mm"}
        else:
            options={"copies": str(self.copies), "page-ranges": "1"}
        cups.Connection().printFile(  # pylint: disable=no-member
            self.printer,
            "data/output.jpg",
            title="Eigendom",
            options=options,
        )

    def barcodenum(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            self.copies = int(text)
            if not 0 < self.copies < 100:
                return self.messageandbuttons(
                    "barcodenum",
                    "numbers",
                    "Only 1 <> 99 allowed; How many do you want?",
                )
            self.barcodeprint()
            return True
        except:
            traceback.print_exc()
            return self.messageandbuttons(
                "barcodenum", "numbers", "NaN ; How many do you want?"
            )

    def barcodecount(self, text):
        prod = self.master.products.lookupprod(text)
        if not prod:
            return self.messageandbuttons(
                "barcodecount",
                "products",
                "Unknown Product; What product do you want a barcode for?",
            )
        prod = self.master.products.products.get(prod)
        self.barcode = None
        for a in prod["aliases"]:
            if re.compile("^[0-9]+$").match(a):
                self.barcode = a
        if not self.barcode:
            self.barcode = text
            for a in prod["aliases"]:
                if len(a) < len(self.barcode):
                    self.barcode = a
        self.name = text
        self.price = "    € %.2f" % prod["price"]
        self.description = prod["description"]
        return self.messageandbuttons("barcodenum", "numbers", "How many do you want?")

    def messageandbuttons(self, donext, buttons, msg):
        self.master.donext(self, donext)
        self.master.send_message(True, "message", msg)
        self.master.send_message(True, "buttons", json.dumps({"special": buttons}))
        return True

    def eigendomnum(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            self.copies = int(text)
            if not 0 < self.copies < 100:
                return self.messageandbuttons(
                    "eigendomnum",
                    "numbers",
                    "Only 1 <> 99 allowed; How many do you want?",
                )
            self.eigendomprint()
            return True
        except:
            traceback.print_exc()
            return self.messageandbuttons(
                "eigendomnum", "numbers", "NaN ; How many do you want?"
            )

    def eigendomcount(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        self.name = text
        return self.messageandbuttons("eigendomnum", "numbers", "How many do you want?")

    def foodnum(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            self.copies = int(text)
            if not 0 < self.copies < 100:
                return self.messageandbuttons(
                    "foodnum", "numbers", "Only 1 <> 99 allowed; How many do you want?"
                )
            self.foodprint()
            return True
        except:
            traceback.print_exc()
            return self.messageandbuttons(
                "foodnum", "numbers", "NaN ; How many do you want?"
            )

    def thtnum(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            self.copies = int(text)
            if not 0 < self.copies < 100:
                return self.messageandbuttons(
                    "thtnum", "numbers", "Only 1 <> 99 allowed; How many do you want?"
                )
            self.thtprint()
            return True
        except:
            traceback.print_exc()
            return self.messageandbuttons(
                "thtnum", "numbers", "NaN ; How many do you want?"
            )

    def toolnum(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        try:
            self.copies = int(text)
            if not 0 < self.copies < 100:
                return self.messageandbuttons(
                    "toolnum", "numbers", "Only 1 <> 99 allowed; How many do you want?"
                )
            self.toolprint()
            return True
        except:
            traceback.print_exc()
            return self.messageandbuttons(
                "toolnum", "numbers", "NaN ; How many do you want?"
            )

    def foodname(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        self.name = text
        return self.messageandbuttons("foodnum", "numbers", "How many do you want?")

    def thtname(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        self.datum = text
        return self.messageandbuttons("thtnum", "numbers", "How many do you want?")

    def toolname(self, text):
        if text == "abort":
            return self.master.callhook("abort", None)
        self.name = text
        return self.messageandbuttons("toolnum", "numbers", "How many do you want?")

    def input(self, text):
        if text == "eigendom":
            self.large = False
            self.master.donext(self, "eigendomcount")
            self.master.send_message(True, "message", "Who are you?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True
        if text == "eigendomlarge":
            self.large = True
            self.master.donext(self, "eigendomcount")
            self.master.send_message(True, "message", "Who are you?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True
        if text == "foodlabel":
            self.master.donext(self, "foodname")
            self.master.send_message(True, "message", "Who are you?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True
        if text == "thtlabel":
            self.master.donext(self, "thtname")
            self.master.send_message(True, "message", "What is the date?")
            self.master.send_message(
                True, "buttons", json.dumps({"special": "accounts"})
            )
            return True
        if text == "toollabel":
            self.master.donext(self, "toolname")
            self.master.send_message(True, "message", "What is the Toolname?")
            return True
        if text == "barcode":
            return self.messageandbuttons(
                "barcodecount", "products", "What product do you want a barcode for?"
            )
        if text == "stickers":
            custom = []
            custom.append({"text": "barcode", "display": "Barcode label"})
            custom.append({"text": "eigendom", "display": "Property label"})
            custom.append({"text": "eigendomlarge", "display": "Large Property label"})
            custom.append({"text": "foodlabel", "display": "Food label"})
            custom.append({"text": "thtlabel", "display": "THT label"})
            custom.append({"text": "toollabel", "display": "Tool label"})
            self.master.send_message(
                True, "buttons", json.dumps({"special": "custom", "custom": custom})
            )
            self.master.send_message(True, "message", "Please select a command")
            return True
        return None

    def startup(self):
        pass
