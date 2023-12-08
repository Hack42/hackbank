#!/usr/bin/python
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt


class door:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        print("Help")
        return {"dooropen": "Door open"}

    def input(self, text):
        if text == "dooropen":
            client = mqtt.Client()
            client.connect("mqtt.space.hack42.nl", 1883, 60)
            client.publish("hack42/brandhok/deuropen", "closed", 1, True)
            client.publish("hack42/brandhok/deuropen", "open", 1, True)
            client.disconnect()
            return True
        return None

    def startup(self):
        pass
