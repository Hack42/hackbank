# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os
import cups
import json
import pyqrcode
import re
import time

class stickers:
    SMALL=(690,271)
    LOGOSMALLSIZE=(309,200)
    WHITE=(255, 255, 255)
    BLACK=(0,0,0)
    LOGOFILE="images/hack42.png"
    FONT="images/arialbd.ttf"
    printer='QL710W'
    printer='QL710W'
    SPACE=0 # spacing around qrcode, should be 4 but our printer prints on white labels

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"stickers": "All sticker commands"}

    def barcodeprint(self):
        if re.compile('^[0-9A-Z]+$').match(self.barcode):
            print("Qrcode: alphanum")
            qrcode_image = pyqrcode.create(self.barcode, error='L', version=1, mode='alphanumeric').png_as_base64_str(scale=5)
        else:
            print("Qrcode: binary")
            qrcode_image = pyqrcode.create(self.barcode, error='L', version=2, mode='binary').png_as_base64_str(scale=5)

        # Create an image object
        img = Image.new('RGB', self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)

        # Load the QR code as an image
        qrcode_img = Image.open(io.BytesIO(base64.b64decode(qrcode_image)))

        # Calculate size for QR code
        size = self.SMALL[1] // (len(qrcode_img) + 2 * self.SPACE)
        qrcode_img = qrcode_img.resize((size * len(qrcode_img), size * len(qrcode_img)), Image.ANTIALIAS)

        # Place QR code on the image
        img.paste(qrcode_img, (self.SPACE, self.SPACE))

        # Load a font
        font = ImageFont.truetype(self.FONT, 40)

        # Add text to the image
        draw.text((self.SMALL[1] + 10, 64), self.name, fill=self.BLACK, font=font)
        draw.text((self.SMALL[1] + 10, 104), self.description, fill=self.BLACK, font=font)
        draw.text((self.SMALL[1] + 10, 200), self.price, fill=self.BLACK, font=font)
        draw.text((self.SMALL[1] + 10, self.SMALL[1] - 16), "deze prijs kan varieren kijk op de kassa voor", fill=self.BLACK, font=font)
        draw.text((self.SMALL[1] + 10, self.SMALL[1] - 2), "meer informatie.", fill=self.BLACK, font=font)

        # Save the image
        img.save("data/barcode.png")

        # Convert PNG to JPG (if needed)
        os.system("convert -density 300 -units pixelsperinch data/barcode.png data/barcode.jpg")

        # Print the file
        cups.Connection().printFile(self.printer, "data/barcode.jpg", 'Eigendom', {'copies': str(self.copies), 'page-ranges': '1'})

    def thtprint(self):
        # Create an image
        img = Image.new('RGB', self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)
    
        # Load the logo
        LOGO = Image.open(self.LOGOFILE)
        LOGO = LOGO.resize(self.LOGOSMALLSIZE, Image.ANTIALIAS)
    
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
        cups.Connection().printFile(self.printer, "data/foodout.png", title="Voedsel", options={'copies': str(self.copies), 'page-ranges': '1'})

    def foodprint(self):
        img = Image.new('RGB', self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)
    
        LOGO = Image.open(self.LOGOFILE)
        LOGO = LOGO.resize(self.LOGOSMALLSIZE, Image.ANTIALIAS)
        img.paste(LOGO, (0, 0))
    
        font = ImageFont.truetype(self.FONT, 40)
        draw.text((0, self.SMALL[1] - 15), self.name, fill=self.BLACK, font=font)
    
        font = ImageFont.truetype(self.FONT, 50)
        draw.text((320, 120), time.strftime('%Y-%m-%d'), fill=self.BLACK, font=font)
    
        img.save("data/foodout.png")
        cups.Connection().printFile(self.printer, "data/foodout.png", title="Voedsel", options={'copies': str(self.copies), 'page-ranges': '1'})

    def eigendomprint(self):

        img = Image.new('RGB', self.SMALL, self.WHITE)
        draw = ImageDraw.Draw(img)
    
        LOGO = Image.open(self.LOGOFILE)
        LOGO = LOGO.resize(self.LOGOSMALLSIZE, Image.ANTIALIAS)
        img.paste(LOGO, (0, 0))
    
        font = ImageFont.truetype(self.FONT, 40)
        draw.text((0, self.SMALL[1] - 15), self.name, fill=self.BLACK, font=font)
        font = ImageFont.truetype(self.FONT, 25)
        draw.text((320, 64), "☐          Look ", fill=self.BLACK, font=font)
        draw.text((321, 65), "☐", fill=self.BLACK, font=font)
        draw.text((320, 99), "☐          Hack ", fill=self.BLACK, font=font)
        draw.text((321, 100), "☐", fill=(0, 0, 0, 0), font=font) # Assuming 0 is transparent
        draw.text((320, 134), "☐          Repair ", fill=self.BLACK, font=font)
        draw.text((321, 135), "☐", fill=self.BLACK, font=font)
        draw.text((320, 169), "☐          Destroy ", fill=self.BLACK, font=font)
        draw.text((321, 170), "☐", fill=(0, 0, 0, 0), font=font) # Assuming 0 is transparent
        draw.text((320, 204), "☐          Steal  ", fill=self.BLACK, font=font)
        draw.text((321, 205), "☐", fill=self.BLACK, font=font)
        draw.text((650, 64), "☐", fill=self.BLACK, font=font)
        draw.text((651, 65), "☐", fill=self.BLACK, font=font)
        draw.text((650, 99), "☐", fill=self.BLACK, font=font)
        draw.text((651, 100), "☐", fill=(0, 0, 0, 0), font=font) # Assuming 0 is transparent
        draw.text((650, 134), "☐", fill=self.BLACK, font=font)
        draw.text((651, 135), "☐", fill=self.BLACK, font=font)
        draw.text((650, 169), "☐", fill=self.BLACK, font=font)
        draw.text((651, 170), "☐", fill=(0, 0, 0, 0), font=font) # Assuming 0 is transparent
        draw.text((650, 204), "☐", fill=self.BLACK, font=font)
        draw.text((651, 205), "☐", fill=self.BLACK, font=font)
        img.save("data/output.jpg", "JPEG", dpi=(300, 300))
        os.system("convert -density 300 -units pixelsperinch data/output.png data/output.jpg")
        cups.Connection().printFile(self.printer,"data/output.jpg",title="Eigendom",options={'copies':str(self.copies),'page-ranges':'1'})

    def barcodenum(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            self.copies=int(text)
            if self.copies<1 or self.copies>99:
                return self.messageandbuttons('barcodenum','numbers','Only 1 <> 99 allowed; How many do you want?')
            else:
                self.barcodeprint()
                return True
        except:
            import traceback
            traceback.print_exc()
            return self.messageandbuttons('barcodenum','numbers','NaN ; How many do you want?')

    def barcodecount(self,text):
        prod=self.master.products.lookupprod(text)
        if not prod:
            return self.messageandbuttons('barcodecount','products','Unknown Product; What product do you want a barcode for?')
        else:
            prod=self.master.products.products[prod]
            self.barcode=None
            for a in prod['aliases']:
                if re.compile('^[0-9]+$').match(a):
                   self.barcode=a
            if not self.barcode:
                self.barcode=text
                for a in prod['aliases']:
                    if len(a)<len(self.barcode):
                        self.barcode=a
            self.name=text
            self.price="    € %.2f" % prod['price']
            self.description=prod['description']
            return self.messageandbuttons('barcodenum','numbers','How many do you want?')
        

    def messageandbuttons(self,donext,buttons,msg):
        self.master.donext(self,donext)
        self.master.send_message(True,'message',msg)
        self.master.send_message(True,'buttons',json.dumps({'special':buttons}))
        return True

    def eigendomnum(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            self.copies=int(text)
            if self.copies<1 or self.copies>99:
                return self.messageandbuttons('eigendomnum','numbers','Only 1 <> 99 allowed; How many do you want?')
            else:
                self.eigendomprint()
                return True
        except:
            import traceback
            traceback.print_exc()
            return self.messageandbuttons('eigendomnum','numbers','NaN ; How many do you want?')

    def eigendomcount(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        self.name=text
        return self.messageandbuttons('eigendomnum','numbers','How many do you want?')

    def foodnum(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            self.copies=int(text)
            if self.copies<1 or self.copies>99:
                return self.messageandbuttons('foodnum','numbers','Only 1 <> 99 allowed; How many do you want?')
            else:
                self.foodprint()
                return True
        except:
            import traceback
            traceback.print_exc()
            return self.messageandbuttons('foodnum','numbers','NaN ; How many do you want?')

    def thtnum(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            self.copies=int(text)
            if self.copies<1 or self.copies>99:
                return self.messageandbuttons('thtnum','numbers','Only 1 <> 99 allowed; How many do you want?')
            else:
                self.thtprint()
                return True
        except:
            import traceback
            traceback.print_exc()
            return self.messageandbuttons('foodnum','numbers','NaN ; How many do you want?')

    def foodname(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        self.name=text
        return self.messageandbuttons('foodnum','numbers','How many do you want?')

    def thtname(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        self.datum=text
        return self.messageandbuttons('thtnum','numbers','How many do you want?')
        
    def input(self,text):
        if text=="eigendom":
            self.master.donext(self,'eigendomcount')
            self.master.send_message(True,'message','Who are you?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True
        elif text=="foodlabel":
            self.master.donext(self,'foodname')
            self.master.send_message(True,'message','Who are you?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True
        elif text=="thtlabel":
            self.master.donext(self,'thtname')
            self.master.send_message(True,'message','What is the date?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True
        elif text=="barcode":
            return self.messageandbuttons('barcodecount','products','What product do you want a barcode for?')
        elif text=="stickers":
            custom=[]
            custom.append({'text': 'barcode','display': 'Barcode label'})
            custom.append({'text': 'eigendom','display': 'Property label'})
            custom.append({'text': 'foodlabel','display': 'Food label'})
            custom.append({'text': 'thtlabel','display': 'THT label'})
            self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
            self.master.send_message(True,'message','Please select a command')
            return True
        
    def startup(self):
        pass
