class abort:

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def help(self):
        return {"abort": "Abort everything"}


    def input(self,text):
        if text=="abort": 
            self.master.callhook('abort',None)
            return True
        if text=="ok": 
            self.master.callhook('ok',None)
            return True

    def startup(self):
        pass

