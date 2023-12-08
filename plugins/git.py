# -*- coding: utf-8 -*-
import os
import threading


class git:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def background(self):
        os.system("cd data && git commit -m " + str(self.master.transID) + " .")

    def hook_post_checkout(self, _text):
        threading.Thread(target=self.background)

    def input(self, text):
        pass

    def startup(self):
        pass
