import json

class products:

    products={}
    aliases={}
    groups={}
    times=1

    def help(self):
        return {"aliasproduct": "Add alias to product"}

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

    def savealias(self,text):
        self.readproducts()
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        prod=self.lookupprod(text)
        if prod:
            self.master.donext(self,'addalias')
            self.master.send_message(True,'message','Already known alias '+text+' for '+prod+'! Try again.')
            self.master.send_message(True,'buttons',json.dumps({'special':'keyboard'}))
            return True
        else:
            self.products[self.aliasprod]['aliases'].append(text)
            self.writeproducts()
            return True

    def addalias(self,text):
        if text=="abort":
            self.master.callhook('abort',None)
            return True
        prod=self.lookupprod(text)
        if prod:
            self.aliasprod=prod
            self.master.donext(self,'savealias')
            self.master.send_message(True,'message','What alias to add for '+prod+'?')
            self.master.send_message(True,'buttons',json.dumps({'special':'keyboard'}))
            return True
        else:
            self.master.donext(self,'addalias')
            self.master.send_message(True,'message','Unknown product;What product do you want to alias?')
            self.master.send_message(True,'buttons',json.dumps({'special':'products'}))
            return True
        
    def input(self,text):
        prod=self.lookupprod(text)
        if prod:
            self.master.receipt.add(True,self.products[prod]['price'],self.products[prod]['description'],self.times,None,prod)
            self.times=1
            return True
        elif text=="aliasproduct":
            self.master.donext(self,'addalias')
            self.master.send_message(True,'message','What product do you want to alias?')
            self.master.send_message(True,'buttons',json.dumps({'special':'products'}))
            return True
        elif text=="addproduct":
            self.master.donext(self,'addproduct')
            self.master.send_message(True,'message','What is the name of the product you want to alias?')
            self.master.send_message(True,'buttons',json.dumps({'special':'keyboard'}))
            return True
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
        for prod in self.products:
            self.master.send_message(True,'products/'+prod,json.dumps(self.products[prod]))
        self.times=1
