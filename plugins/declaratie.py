# -*- coding: utf-8 -*-
import json
import time

class declaratie:

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"declaratie": "Declaration", "afroom": "Remove cash money", "verkoop": "Report sales"}


    def who(self,text):
        if text in self.master.accounts.accounts:
            self.wie=text
            self.master.donext(self,'amount')
            if self.soort=="verkoop":
                self.master.send_message(True,'message','How much money did you get?')
            elif self.soort=="afroom":
                self.master.send_message(True,'message','How much money are you taking?')
            else:
                self.master.send_message(True,'message','How much money do you want back?')
            self.master.send_message(True,'buttons',json.dumps({'special':'numbers'}))
            return True
        elif text=="abort":
            self.master.callhook('abort',None)
            return True
        else:
            self.master.donext(self,'who')
            self.master.send_message(True,'message','Unknown User; Who are you?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True

    def amount(self,text):
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        try:
            value=float(text)
            if value>=0 and value<5000:
                self.value=value
                if self.soort=="verkoop":
                    self.master.send_message(True,'message','Why do you give us E %.2f?' % self.value)
                elif self.soort=="declaratie":
                    self.master.send_message(True,'message','Where did you spend E %.2f on?'  % self.value)
                elif self.soort=="afroom":
                    self.reden="Afroom"
                    self.ascash=-value
                    self.asbank=value
                    return self.final()
                self.master.send_message(True,'buttons',json.dumps({'special':'keyboard'}))
                self.master.donext(self,'reason')
            else:
                self.master.donext(self,'amount')
                self.master.send_message(True,'message','Enter an amount between 0.01 and 4999.99:')
                self.master.send_message(True,'buttons',json.dumps({'special':'numbers'}))
            return True
        except:
            import traceback
            traceback.print_exc()

            if text=="abort":
                self.master.callhook('abort',None)
                return True
            self.master.donext(self,'amount')
            if self.soort=="verkoop":
                self.master.send_message(True,'message','Not a valid number! How much money did you get?')
            else:
                self.master.send_message(True,'message','Not a valid number! How much money do you want back?')
            self.master.send_message(True,'buttons',json.dumps({'special':'numbers'}))
            return True

    def reason(self,text):
        self.reden=text
        self.askbar('');
        return True

    def askbar(self,error):
        self.master.donext(self,'runasbar')
        if self.soort=="declaratie":
            self.master.send_message(True,'message',error+'How much do you want on your bar account?')
        else:
            self.master.send_message(True,'message',error+'How much do you want from your bar account?')
        custom=[]
        custom.append({'text': '0','display': 'None'})
        custom.append({'text': str(self.value),'display': 'Everything (E %.2f)' % self.value})
        self.master.donext(self,'runasbar')
        self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom': custom }))
        return True

    def runasbar(self,text):
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        try:
            value=float(text)
            if value>=0 and value<5000:
                if value>self.value:
                    return self.askbar("E %.2f is larger than E %.2f ; " % (value,self.value))
                self.asbar=value
                if self.asbar==self.value:
                    return self.final()
                return self.askcash('')
            else:
                return self.askbar('Not between 0.01 and 4999.99; ');
        except:
            import traceback
            traceback.print_exc()
            self.askbar('');
            return True

    def askcash(self,error):
        self.master.donext(self,'runascash')
        if self.soort=="declaratie":
            self.master.send_message(True,'message',error+'How much do you want in cash?')
        else:
            self.master.send_message(True,'message',error+'How much do you give in cash?')
        custom=[]
        custom.append({'text': '0','display': 'None'})
        custom.append({'text': str(self.value-self.asbar),'display': 'Everything (E %.2f)' % (self.value-self.asbar)})
        self.master.donext(self,'runascash')
        self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom': custom }))
        return True

    def runascash(self,text):
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        try:
            value=float(text)
            if value>=0 and value<5000:
                if value > (self.value-self.asbar):
                    return self.askcash("E %.2f is larger than E %.2f ; " % (value,self.value-self.asbar))
                self.ascash=value
                if (self.ascash+self.asbar) == self.value:
                    return self.final()
                return self.askbank('')
            else:
                return self.askcash('Not between 0.01 and 4999.99; ');
        except:
            import traceback
            traceback.print_exc()
            return self.askcash('');

    def askbank(self,error):
        self.master.donext(self,'runasbank')
        if self.soort=="declaratie":
            self.master.send_message(True,'message',error+'How much do you want in your bankaccount?')
        else:
            self.master.send_message(True,'message',error+'How much do you send from your bankaccount?')
        custom=[]
        custom.append({'text': '0','display': 'None'})
        custom.append({'text': str(self.value-self.asbar-self.ascash),'display': 'Everything (E %.2f)' % (self.value-self.asbar-self.ascash)})
        self.master.donext(self,'runasbank')
        self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom': custom }))
        return True

    def runasbank(self,text):
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        try:
            value=float(text)
            if value>=0 and value<5000:
                if value > (self.value-self.asbar-self.ascash):
                    return self.askbank("E %.2f is larger than E %.2f ; " % (value,self.value-self.asbar-self.ascash))
                self.asbank=value
                if (self.ascash+self.asbar+self.asbank) == self.value:
                    return self.final()
                else:
                    return self.askbank('The numbers do not match; ')
            else:
                return self.askbank('Not between 0.01 and 4999.99; ');
        except:
            import traceback
            traceback.print_exc()
            return self.askbank('');

    def bon(self):
        self.master.POS.printdeclaratie((self.wie,self.soort,self.reden,self.asbar,self.ascash,self.asbank))

    def save(self):
        with open("data/administratie.txt","a") as logfile:
            logfile.write("%s   %s %+10.2f   %+10.2f  # %s\n"  % ( time.strftime('%Y-%m-%d'),self.soort,self.asbank,self.ascash+self.asbar,self.wie+" / "+self.reden ) )
            logfile.close()

    def correct(self,text):
        if text=="yes":
            if self.asbar>0:
                self.master.receipt.add(False,self.asbar,'Declaratie',1,self.wie,'declaratie')
                self.master.callhook('checkout',self.wie)
                self.master.callhook('endsession',self.wie)
            if self.asbar<0:
                self.master.receipt.add(True,0-self.asbar,'Declaratie',1,self.wie,'declaratie')
                self.master.callhook('checkout',self.wie)
                self.master.callhook('endsession',self.wie)
            if self.ascash!=0:
                self.master.POS.drawer()
            self.save()
            return True
        elif text=="no":
            return True
        elif text=="abort":
            self.master.callhook('abort',None)
        else:
            self.master.send_message(True,'message','Invalid answer; Is the receipt correct?')
            custom=[{'text':"yes",'display':"Yes"},{'text':"no",'display':"No"}]
            self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
            self.master.donext(self,'correct')
            return True


    def final(self):
        self.bon()
        self.master.send_message(True,'message','Is the receipt correct?')
        custom=[{'text':"yes",'display':"Yes"},{'text':"no",'display':"No"}]
        self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
        self.master.donext(self,'correct')
        return True

    def input(self,text):
        if text=="declaratie" or text=="verkoop" or text=="afroom":
            self.ascash=0
            self.asbar=0
            self.asbank=0
            self.master.send_message(True,'message',"Who are you?")
            self.master.donext(self,'who')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            self.soort=text
            return True

    def startup(self):
        pass
