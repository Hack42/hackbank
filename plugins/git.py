# -*- coding: utf-8 -*-
import os
import thread
class git:

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID

    def background(self):
        os.system("cd data && git commit -m "+str(self.master.transID)+" .")
    def hook_post_checkout(self,text):
        thread.start_new_thread(self.background, ())

    def input(self,text):
        pass

    def startup(self):
        pass
