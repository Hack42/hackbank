# -*- coding: utf-8 -*-
import gd
import os
import cups
import json

class eigendom:
    SMALL=(690,271)
    LOGOSMALLSIZE=(309,200)
    WHITE=(255, 255, 255)
    BLACK=(0,0,0)
    LOGOFILE="images/hack42.png"
    FONT="images/arialbd.ttf"
    printer='QL-710W'

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"eigendom": "Property label"}

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
        cups.Connection().printFile(self.printer,"data/output.jpg",title="Eigendom",options={'copies': self.copies > 0 and str(self.copies) or '1','page-ranges':'1'})

        #os.system("convert -density 300 -units pixelsperinch data/output.png data/output.jpg ; lpr -o page-ranges=1 -P QL-710W -#"+str(aantal)+" data/output.jpg");
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
        
    def input(self,text):
        if text=="eigendom":
            self.master.donext(self,'eigendomcount')
            self.master.send_message(True,'message','Who are you?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True
        
    def startup(self):
        pass

