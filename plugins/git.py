# -*- coding: utf-8 -*-
import subprocess
import threading


class git:
    lock = threading.Lock()

    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def background(self):
        with self.lock:
            subprocess.run(
                ["git", "commit", "-m", str(self.master.transID), "."],
                cwd="data",
                check=False,
            )

    def hook_post_checkout(self, _text):
        threading.Thread(target=self.background).start()

    def input(self, text):
        pass

    def startup(self):
        pass
