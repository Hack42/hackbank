#!/usr/bin/python3
# -*- coding: utf-8 -*-
import glob
import time
import json
import sys
import traceback
import paho.mqtt.client as mqtt

sessions = {}


class log:  # pylint: disable=too-few-public-methods
    pass


class Session:
    SID = ""
    plugins = {}
    counter = 0
    nextcall = {}
    prompt = ""
    help = {}
    cache = {}
    iets = 0
    buttons = {}
    stock = None
    POS = None
    log = None
    receipt = None
    accounts = None
    products = None

    def import_from(self, module, name):
        module = __import__(module, fromlist=[name])
        return getattr(module, name)

    def __init__(self, SID, client):
        self.SID = SID
        self.client = client
        self.plugins = {}

    def startup(self):
        print("Startup", self.SID)
        for fname in glob.glob("plugins/*.py"):
            plugname = fname.split("/")[1].rstrip(".py")
            if plugname != "__init__" and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
        print(self.plugins)
        for fname in glob.glob("plugins/*.py"):
            plugname = fname.split("/")[1].rstrip(".py")
            print(plugname)
            if plugname != "__init__" and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
                self.plugins[plugname] = self.import_from(
                    "plugins." + plugname, plugname
                )(self.SID, self)
                print(plugname, self.import_from("plugins." + plugname, plugname))
                self.send_message(True, "message", "loaded plugin " + plugname)
                try:
                    self.help.update(self.plugins[plugname].help())
                except:
                    print(traceback.format_exc())
        print(self.plugins)
        self.receipt = self.plugins["receipt"]
        self.accounts = self.plugins["accounts"]
        self.products = self.plugins["products"]
        self.stock = self.plugins["stock"]
        self.log = self.plugins["log"]
        self.POS = self.plugins["POS"]
        self.counter += 1
        self.send_message(False, "message", "Please wait while loading...")
        for _plug, plugin in self.plugins.items():
            try:
                plugin.startup()
            except:
                print(traceback.format_exc())
        self.send_message(True, "commands", json.dumps(self.help))
        self.send_message(True, "message", "Enter product, command or username")
        print(self.plugins)

    def realcallhook(self, hook, arg):
        for _plug, plugin in self.plugins.items():
            try:
                getattr(plugin, "hook_" + hook)
                try:
                    getattr(plugin, "hook_" + hook)(arg)
                except:
                    print(traceback.format_exc())
            except AttributeError:
                pass

    def callhook(self, hook, arg):
        self.realcallhook("pre_" + hook, arg)
        self.realcallhook(hook, arg)
        self.realcallhook("post_" + hook, arg)
        return True

    def donext(self, plug, function):
        self.nextcall = {"plug": plug, "function": function}

    def input(self, text):  # pylint: disable=too-many-branches, too-many-statements
        if text == "":
            self.send_message(True, "message", "Enter product, command or username")
            self.send_message(True, "buttons", json.dumps({}))
            return True
        if self.iets == 0 and text != "abort":
            self.iets == 1  # pylint: disable = pointless-statement
        self.buttons = {}
        done = 0
        for plug, plugin in self.plugins.items():
            try:
                plugin.pre_input(text)
            except AttributeError:
                pass
            except:
                print(traceback.format_exc())

        self.prompt = ""
        if self.nextcall:
            try:
                print(text)
                print(self.nextcall)
                plug = self.nextcall["plug"]
                func = self.nextcall["function"]
                self.nextcall = {}
                print(getattr(plug, func))
                if getattr(plug, func)(text):
                    done = 1
            except:
                print(traceback.format_exc())
        if done == 1:
            print("Call done with self.nextcall")
        else:  # pylint: disable = too-many-nested-blocks
            for part in text.split():
                if part != "":
                    done = 0
                    print("Running part", part, self.nextcall)
                    self.prompt = ""
                    if self.nextcall:
                        try:
                            plug = self.nextcall["plug"]
                            func = self.nextcall["function"]
                            self.nextcall = {}
                            if getattr(plug, func)(part):
                                done = 1
                        except:
                            print(traceback.format_exc())
                    if done == 0:
                        for plug, plugin in self.plugins.items():
                            try:
                                if plugin.input(part):
                                    done = 1
                                    break
                            except AttributeError:
                                print(traceback.format_exc())
                            except:
                                print(traceback.format_exc())
                    if done == 0:
                        if self.plugins["withdraw"].withdraw(part):
                            done = 1
                        if self.plugins["accounts"].newuser(part):
                            done = 1
        if done == 1 and self.prompt == "":
            self.send_message(True, "message", "Enter product, command or username")
        elif self.prompt == "":
            self.send_message(True, "message", "Unknown product, command or username")
            self.callhook("wrong", ())
        if not self.nextcall and not self.buttons:
            self.send_message(True, "buttons", json.dumps({}))
        return None

    def send_message(self, retain, topic, message):
        if (
            not "hack42bar/output/session/" + self.SID + "/" + topic in self.cache
            or self.cache["hack42bar/output/session/" + self.SID + "/" + topic]
            != message
            or len(topic) < 8
        ):
            print(
                retain,
                "hack42bar/output/session/" + self.SID + "/" + topic,
                ":",
                message,
            )
            self.cache["hack42bar/output/session/" + self.SID + "/" + topic] = message
            if topic == "message":
                self.prompt = message
            if topic == "buttons":
                self.buttons = message
            self.client.publish(
                "hack42bar/output/session/" + self.SID + "/" + topic, message, 1, retain
            )


def get_session(SID, client):
    global sessions  # pylint: disable=global-variable-not-assigned
    if not SID in sessions:
        print("Starting new session", SID)
        sessions[SID] = Session(SID, client)
        sessions[SID].startup()
        client.publish("hack42bar/output/sessions", json.dumps(list(sessions.keys())))
    return sessions[SID]


def run_session(client, SID, action, data):
    if action == "input":
        session = get_session(SID, client)
        session.input(data.decode())
    else:
        print("unhandled", action)


def on_connect(client, _userdata, _flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("hack42bar/input/#")


def on_message(client, _userdata, msg):
    # print(msg.topic+" "+str(msg.payload))
    elms = msg.topic.split("/")
    msg = msg.payload
    if len(elms) < 3:
        return
    # try:
    run_session(client, elms[3], elms[4], msg)


def run():
    while 1:
        try:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message

            client.connect("localhost", 1883, 60)
            client.loop_start()
            while True:
                time.sleep(1)
            # client.loop_forever()
        except:
            time.sleep(5)


if __name__ == "__main__":
    run()
