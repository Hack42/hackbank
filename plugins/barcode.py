# -*- coding: utf-8 -*-
import gd
import os
import cups
import pyqrcode
import json
import re

class barcode:
    SMALL=(690,271)
    LOGOSMALLSIZE=(309,200)
    WHITE=(255, 255, 255)
    BLACK=(0,0,0)
    LOGOFILE="images/hack42.png"
    FONT="images/arialbd.ttf"
    printer='QL-710W'
    SPACE=4

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"barcode": "Barcode label"}

    def barcodeprint(self):
        if re.compile('^[0-9A-Z]+$').match(self.barcode):
            print "Qrcode: alphanum"
            qrcode=pyqrcode.create(self.barcode, error='L', version=1, mode='alphanumeric').code
        else:
            print "Qrcode: binary"
            qrcode=pyqrcode.create(self.barcode, error='L', version=2, mode='binary').code
        img=gd.image(self.SMALL)
        WHITE=img.colorAllocate(self.WHITE)
        BLACK=img.colorAllocate(self.BLACK)
        img.filledRectangle((0,0),(10,10),WHITE)
        size=self.SMALL[1]/(len(qrcode)+2*self.SPACE)
        for line in range(0,len(qrcode)):
           for pix in range(0,len(qrcode[line])):
             img.rectangle(((pix+self.SPACE)*size,(line+self.SPACE)*size),((pix+self.SPACE)*size+size,(line+self.SPACE)*size+size),(BLACK if qrcode[line][pix] == 1 else WHITE),(BLACK if qrcode[line][pix] == 1 else WHITE))

        img.string_ttf(self.FONT,40,0,(self.SMALL[1]+10,64),self.name,BLACK)
        img.string_ttf(self.FONT,20,0,(self.SMALL[1]+10,104),self.description,BLACK)
        img.string_ttf(self.FONT,60,0,(self.SMALL[1]+10,200),self.price,BLACK)
        img.string_ttf(self.FONT,12,0,(self.SMALL[1]+10,self.SMALL[1]-16),"deze prijs kan varieren kijk op de kassa voor",BLACK)
        img.string_ttf(self.FONT,12,0,(self.SMALL[1]+10,self.SMALL[1]-2),"meer informatie.",BLACK)
        img.writePng("data/barcode.png")
        os.system("convert -density 300 -units pixelsperinch data/barcode.png data/barcode.jpg")
        conn=cups.Connection()
        printer=conn.getPrinters()[self.printer]
        conn.printFile(printer,"data/barcode.jpg",'Eigendom',{'copies': self.copies > 0 and str(self.copies) or '1','page-ranges':'1'})

    def messageandbuttons(self,donext,buttons,msg):
        self.master.donext(self,donext)
        self.master.send_message(True,'message',msg)
        self.master.send_message(True,'buttons',json.dumps({'special':buttons}))
        return True

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
        
    def input(self,text):
        if text=="barcode":
            return self.messageandbuttons('barcodecount','products','What product do you want a barcode for?')
        
    def startup(self):
        pass

