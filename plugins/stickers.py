# -*- coding: utf-8 -*-
import gd
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
    printer='QL-710W'
    printer='QL-710W'
    SPACE=0 # spacing around qrcode, should be 4 but our printer prints on white labels

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"stickers": "All sticker commands"}

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
        for i in range(0,self.copies):
            cups.Connection().printFile(self.printer,"data/barcode.jpg",'Eigendom',{'copies': 1,'page-ranges':'1'})

    def foodprint(self):
        img=gd.image(self.SMALL)
        WHITE=img.colorAllocate(self.WHITE)
        BLACK=img.colorAllocate(self.BLACK)
        img.filledRectangle((0,0),(10,10),WHITE)
        LOGO=gd.image(self.LOGOFILE)
        LOGO.copyResizedTo(img,(0,0),(0,0),self.LOGOSMALLSIZE)
        img.string_ttf(self.FONT,40,0,(0,self.SMALL[1]-15),self.name,BLACK)
        img.string_ttf(self.FONT,50,0,(320,  120),time.strftime('%Y-%m-%d'),BLACK)
        img.writePng("data/foodout.png")
        os.system("convert -density 300 -units pixelsperinch data/foodout.png data/foodout.jpg")
        for i in range(0,self.copies):
            cups.Connection().printFile(self.printer,"data/foodout.jpg",title="Voedsel",options={'page-ranges':'1'})

    def eigendomprint(self):
        img=gd.image(self.SMALL)
        WHITE=img.colorAllocate(self.WHITE)
        BLACK=img.colorAllocate(self.BLACK)
        img.filledRectangle((0,0),(10,10),WHITE)
        LOGO=gd.image(self.LOGOFILE)
        LOGO.copyResizedTo(img,(0,0),(0,0),self.LOGOSMALLSIZE)
        img.string_ttf(self.FONT,40,0,(0,self.SMALL[1]-15),self.name,BLACK)
        img.string_ttf(self.FONT,20,0,(320,  23),"Don't                             Ask",BLACK)
        img.string_ttf(self.FONT,25,0,(320,  64),"☐          Look ",BLACK)
        img.string_ttf(self.FONT,25,0,(321,  65),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(320,  99),"☐          Hack ",BLACK)
        img.string_ttf(self.FONT,25,0,(321, 100),"☐",0)
        img.string_ttf(self.FONT,25,0,(320, 134),"☐          Repair ",BLACK)
        img.string_ttf(self.FONT,25,0,(321, 135),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(320, 169),"☐          Destroy ",BLACK)
        img.string_ttf(self.FONT,25,0,(321, 170),"☐",0)
        img.string_ttf(self.FONT,25,0,(320, 204),"☐          Steal  ",BLACK)
        img.string_ttf(self.FONT,25,0,(321, 205),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(650,  64),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(651,  65),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(650,  99),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(651, 100),"☐",0)
        img.string_ttf(self.FONT,25,0,(650, 134),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(651, 135),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(650, 169),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(651, 170),"☐",0)
        img.string_ttf(self.FONT,25,0,(650, 204),"☐",BLACK)
        img.string_ttf(self.FONT,25,0,(651, 205),"☐",BLACK)
        img.writePng("data/output.png")
        os.system("convert -density 300 -units pixelsperinch data/output.png data/output.jpg")
        for i in range(0,self.copies):
            cups.Connection().printFile(self.printer,"data/output.jpg",title="Eigendom",options={'page-ranges':'1'})

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

    def foodname(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        self.name=text
        return self.messageandbuttons('foodnum','numbers','How many do you want?')
        
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
        elif text=="barcode":
            return self.messageandbuttons('barcodecount','products','What product do you want a barcode for?')
        elif text=="stickers":
            custom=[]
            custom.append({'text': 'barcode','display': 'Barcode label'})
            custom.append({'text': 'eigendom','display': 'Property label'})
            self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
            self.master.send_message(True,'message','Please select a command')
            return True
        
    def startup(self):
        pass
