import json
import re

class products:

    products={}
    aliases={}
    groups={}
    times=1

    def help(self):
        return {"aliasproduct": "Add alias to product","addproduct": "Add new product","setprice": "Change the price of a product"}

    def readproducts(self):
        groupname=""
        with open('data/revbank.products','r') as f:
            lines=f.readlines()
        for line in lines:
            parts=' '.join(line.split()).split(" ",2)
            if line.startswith('#'):
                groupname=line.replace("#","").strip(" \t\n\r")
                self.groups[groupname]=[]
            elif len(parts)==3:
                aliases=parts[0].split(",")
                name=aliases.pop(0)
                self.groups[groupname].append(name)
                for alias in aliases:
                    self.aliases[alias]=name
                self.products[name]={'price': float(parts[1]),'description': parts[2], 'group': groupname, 'aliases': aliases}
        for prod in self.products:
            self.master.send_message(True,'products/'+prod,json.dumps(self.products[prod]))

    def writeproducts(self):
        with open('data/revbank.products','w') as f:
            for group in self.groups:
                f.write('# '+group+"\n");
                for prod in self.groups[group]:
                   names=self.products[prod]['aliases']
                   names.insert(0,prod)
                   f.write("%-58s %7.2f  %s\n" % (",".join(names),self.products[prod]['price'],self.products[prod]['description']))
                f.write("\n");
            f.close()

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def lookupprod(self,text):
        prod=None
        if text in self.products:
            prod=text
        if text in self.aliases:
            prod=self.aliases[text]
        return prod

    def messageandbuttons(self,donext,buttons,msg):
        self.master.donext(self,donext)
        self.master.send_message(True,'message',msg)
        self.master.send_message(True,'buttons',json.dumps({'special':buttons}))
        return True

    def savealias(self,text):
        self.readproducts()
        if text=="abort": return self.master.callhook('abort',None)
        prod=self.lookupprod(text)
        if prod:
            return self.messageandbuttons('savealias','keyboard','Already known alias '+text+' for '+prod+'! Try again.')
        elif len(text)<6 or not re.compile('^[A-z0-9]+$').match(text):
            return self.messageandbuttons('savealias','keyboard','only [A-z0-9] is allowed in any alias and it should be at least 4 chars long')
        else:
            self.products[self.aliasprod]['aliases'].append(text)
            self.writeproducts()
            self.readproducts()
            return True

    def addalias(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        prod=self.lookupprod(text)
        if prod:
            self.aliasprod=prod
            return self.messageandbuttons('savealias','keyboard','What alias to add for '+prod+'?')
        else:
            return self.messageandbuttons('addalias','products','Unknown product;What product do you want to alias?')

    def setprice(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        prod=self.lookupprod(text)
        if prod:
            self.priceprod=prod
            return self.messageandbuttons('saveprice','numbers','What is the new price for '+prod+'?')
        else:
            return self.messageandbuttons('setprice','products','Unknown product;What product do you want change price?')

    def saveprice(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            price=float(text)
            if price<0.01 or price>999.99:
                return self.messageandbuttons('saveprice','numbers','Price should be between 0.01 and 999.99')
            else:
                self.newprodprice=price
                self.products[self.priceprod]['price']=self.newprodprice
                self.writeproducts()
                self.readproducts()
                return True
        except:
            import traceback
            return self.messageandbuttons('saveprice','numbers','Not a valid number; What is the price for'+self.newprod+'?')

    def addproductgroup(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        if len(text)<4:
            self.master.donext(self,'addproductgroup')
            self.master.send_message(True,'message','Too short,what productgroup to add the product to?')
            self.master.send_message(True,'buttons',json.dumps({'special':'custom', 'custom':[ {'text':n,'display':n } for n in self.groups ]}))
            return True
        else:
            self.newprodgroup=text
            if not self.newprodgroup in self.groups:
                self.groups[self.newprodgroup]=[self.newprod]
                self.products[self.newprod]={'price': self.newprodprice,'description': self.newproddesc, 'group': self.newprodgroup, 'aliases': []}
                self.writeproducts()
                self.readproducts()
                return True
            else:
                self.groups[self.newprodgroup].append(self.newprod)
                self.products[self.newprod]={'price': self.newprodprice,'description': self.newproddesc, 'group': self.newprodgroup, 'aliases': []}
                self.writeproducts()
                self.readproducts()
                return True
           

    def addproductprice(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        try:
            price=float(text)
            if price<0.01 or price>999.99:
                return self.messageandbuttons('addproductprice','numbers','Price should be between 0.01 and 999.99')
            else:
                self.newprodprice=price
                self.master.donext(self,'addproductgroup')
                self.master.send_message(True,'message','what productgroup to add the product to?')
                self.master.send_message(True,'buttons',json.dumps({'special':'custom', 'custom':[ {'text':n,'display':n } for n in self.groups ]}))
                return True
        except:
            import traceback
            return self.messageandbuttons('addproductprice','numbers','Not a valid number; What is the price for'+self.newprod+'?')

    def addproductdesc(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        if len(text)<4:
            return self.messageandbuttons('addproductdesc','keyboard','Too short, What is the description for '+self.newprod+'?')
        else:
            self.newproddesc=text
            return self.messageandbuttons('addproductprice','numbers','What is the price for '+self.newprod+'?')
            
    def addproduct(self,text):
        if text=="abort": return self.master.callhook('abort',None)
        prod=self.lookupprod(text)
        if prod:
            return self.messageandbuttons('addproduct','keyboard','Product already exists? What product to add?')
        elif len(text)<4 or not re.compile('^[A-z0-9]+$').match(text):
            return self.messageandbuttons('addproduct','keyboard','only [A-z0-9] is allowed as product name, what name do you want to add?')
        else:
            self.newprod=text
            return self.messageandbuttons('addproductdesc','keyboard','What is the description for '+text+'?')

    def input(self,text):
        prod=self.lookupprod(text)
        if prod:
            self.master.receipt.add(True,self.products[prod]['price'],self.products[prod]['description'],self.times,None,prod)
            self.times=1
            return True
        elif text=="aliasproduct":
            return self.messageandbuttons('addalias','products','What product do you want to alias?')
        elif text=="addproduct":
            return self.messageandbuttons('addproduct','keyboard','What is the name of the product you want to add?')
        elif text=="setprice":
            return self.messageandbuttons('setprice','products','What product to change the price for?')
        elif text.endswith('*'):
            try:
                value=float(text[:-1])
                if value>0 and value<100:
                    self.times=value
                    self.master.send_message(True,'message',"What are you buying %d from?" % self.times)
                    self.master.send_message(True,'buttons',json.dumps({'special':'products'}))
                    return True
            except:
                pass

    def hook_abort(self,void):
        self.startup()

    def startup(self):
        self.readproducts()
        self.times=1
