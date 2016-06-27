import json
import time
import codecs

class accounts:

    accounts={}

    members=[]
    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    # Internal functions
    def readaccounts(self):
        with codecs.open('data/revbank.accounts','r','utf-8') as f:
            lines=f.readlines()
        for line in lines:
            parts=line.split()
            self.accounts[parts[0]]={'amount': float(parts[1]), 'lastupdate': parts[2]}

    def updateaccount(self,usr,value):
           print "Updating account",usr
           if usr=="cash": return
           had=self.accounts[usr]['amount']
           self.accounts[usr]['amount']+=value
           has=self.accounts[usr]['amount']
           self.accounts[usr]['lastupdate']=time.strftime("%Y-%m-%d_%H:%M:%S")
           self.master.callhook('balance',(usr,had,has,self.master.transID))

    def writeaccount(self):
        with open('data/revbank.accounts','w') as f:
            for usr in self.accounts:
               f.write("%-18s %+7.2f %s\n" % (usr,round(self.accounts[usr]['amount'],2),self.accounts[usr]['lastupdate']))

    # Hooks
    def hook_balance(self,(usr,had,has,transID)):
        self.master.send_message(False,'infobox/account/'+usr,json.dumps(self.accounts[usr]))
        self.master.send_message(True,'accounts/'+usr,json.dumps(self.accounts[usr]))

    def hook_endsession(self,text):
        self.writeaccount()
 
    def hook_abort(self,void):
        self.readaccounts()
        for name in self.accounts:
            self.master.send_message(True,'accounts/'+name,json.dumps(self.accounts[name]))

    def createnew(self,text):
        if text=="yes":
           self.accounts[self.newaccount]={'amount': 0, 'lastupdate': 0}
           return self.input(self.newaccount)
        elif text=="no":
           return True
        elif text=="abort":
           self.master.callhook('abort',None)
        else:
           self.master.send_message(True,'message','Invalid answer; Account '+self.newaccount+' does not exist do you want to create?')
           custom=[{'text':"yes",'display':"Yes"},{'text':"no",'display':"No"}]
           self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
           self.master.donext(self,'createnew')
           return True
    
    def startup(self):
        self.readaccounts()
        for name in self.accounts:
            self.master.send_message(True,'accounts/'+name,json.dumps(self.accounts[name]))
        with open('data/revbank.members') as f:
            self.members = f.readlines()
        self.members=[m.rstrip() for m in self.members]
        self.master.send_message(True,'members',json.dumps(self.members))

    def hook_pre_checkout(self,text):
        self.readaccounts()
        self.master.transID=int(time.time() - 1300000000)

    def hook_post_checkout(self,text):
        self.master.send_message(True,'buttons',json.dumps({'special':'infobox'}))
        for usr in self.master.receipt.totals:
            self.updateaccount(usr,self.master.receipt.totals[usr])

    # This handles the input
    def input(self,text):
        if self.master.receipt.is_empty() and text in self.accounts:
           self.master.send_message(False,'infobox/account',json.dumps(self.accounts[text]))
           self.master.send_message(True,'buttons',json.dumps({'special':'infobox'}))
           return True
        elif text in self.accounts:
           self.master.callhook('checkout',text)
           self.master.callhook('endsession',text)
           return True

    def newuser(self,text):
        for rid in self.master.receipt.receipt:
           if rid['value']>0 and rid['Lose']==False:
               self.master.send_message(True,'message','Account '+text+' does not exist do you want to create?')
               custom=[{'text':"yes",'display':"Yes"},{'text':"no",'display':"No"}]
               self.master.send_message(True,'buttons',json.dumps({'special':'custom','custom':custom}))
               self.master.donext(self,'createnew')
               self.newaccount=text
               return True

