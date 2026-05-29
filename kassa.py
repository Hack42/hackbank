#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Broad exception handling is intentional in this plugin host: plugin failures
# should be logged and isolated instead of stopping the active kassa session.
# pylint: disable=broad-exception-caught
import glob
import logging
import os
import time
import json
import sys
import paho.mqtt.client as mqtt
from config import config_get

logger = logging.getLogger(__name__)
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
        self.counter = 0
        self.nextcall = {}
        self.prompt = ""
        self.help = {}
        self.cache = {}
        self.iets = 0
        self.buttons = {}
        self.stock = None
        self.POS = None
        self.log = None
        self.receipt = None
        self.accounts = None
        self.products = None

    def startup(self):
        logger.info("session_startup sid=%s", self.SID)
        for fname in glob.glob("plugins/*.py"):
            plugname = os.path.splitext(os.path.basename(fname))[0]
            if plugname != "__init__" and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
        logger.debug(
            "session_plugins_before_load sid=%s plugins=%s", self.SID, self.plugins
        )
        for fname in glob.glob("plugins/*.py"):
            plugname = os.path.splitext(os.path.basename(fname))[0]
            logger.debug("plugin_discovered sid=%s plugin=%s", self.SID, plugname)
            if plugname != "__init__" and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
                self.plugins[plugname] = self.import_from(
                    "plugins." + plugname, plugname
                )(self.SID, self)
                logger.debug(
                    "plugin_loaded sid=%s plugin=%s class=%r",
                    self.SID,
                    plugname,
                    self.import_from("plugins." + plugname, plugname),
                )
                self.send_message(True, "message", "loaded plugin " + plugname)
                try:
                    self.help.update(self.plugins[plugname].help())
                except Exception:
                    logger.exception("Plugin %s help failed", plugname)
        logger.debug("session_plugins_loaded sid=%s plugins=%s", self.SID, self.plugins)
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
            except Exception:
                logger.exception("Plugin %s startup failed", _plug)
        self.send_message(True, "commands", json.dumps(self.help))
        self.send_message(True, "message", "Enter product, command or username")
        logger.info("session_ready sid=%s plugins=%s", self.SID, sorted(self.plugins))

    def realcallhook(self, hook, arg):
        for _plug, plugin in self.plugins.items():
            try:
                hook_func = getattr(plugin, "hook_" + hook)
            except AttributeError:
                continue
            try:
                hook_func(arg)
            except Exception:
                logger.exception("Plugin %s hook_%s failed", _plug, hook)

    def callhook(self, hook, arg):
        self.realcallhook("pre_" + hook, arg)
        self.realcallhook(hook, arg)
        self.realcallhook("post_" + hook, arg)
        return True

    def donext(self, plug, function):
        self.nextcall = {"plug": plug, "function": function}

    def pre_input(self, text):
        for _plug, plugin in self.plugins.items():
            try:
                pre_input = getattr(plugin, "pre_input")
            except AttributeError:
                continue
            try:
                pre_input(text)
            except Exception:
                logger.exception("Plugin %s pre_input failed", _plug)

    def handle_nextcall(self, text):
        if not self.nextcall:
            return False
        try:
            plug = self.nextcall["plug"]
            func = self.nextcall["function"]
            self.nextcall = {}
            logger.debug(
                "nextcall sid=%s plugin=%s function=%s input=%r",
                self.SID,
                plug.__class__.__name__,
                func,
                text,
            )
            return bool(getattr(plug, func)(text))
        except Exception:
            logger.exception("Nextcall failed")
            return False

    def input(self, text):
        if not text:
            self.send_message(True, "message", "Enter product, command or username")
            self.send_message(True, "buttons", json.dumps({}))
            return

        self.buttons = {}
        self.pre_input(text)

        self.prompt = ""

        done = self.handle_nextcall(text)
        if not done:
            parts = text.split()
            for part in parts:
                if part:
                    done = self.handle_part(part)  # Call handle_part for each part

        if done and not self.prompt:
            self.send_message(True, "message", "Enter product, command or username")
        elif not self.prompt:
            self.send_message(True, "message", "Unknown product, command or username")
            self.callhook("wrong", ())

        if not self.nextcall and not self.buttons:
            self.send_message(True, "buttons", json.dumps({}))

    def handle_part(self, part):
        done = self.handle_nextcall(part)

        if not done:
            for _plug, plugin in self.plugins.items():
                try:
                    plugin_input = getattr(plugin, "input")
                except AttributeError:
                    continue
                try:
                    if plugin_input(part):
                        done = 1
                        break
                except Exception:
                    logger.exception("Plugin %s input failed", _plug)

        if not done:
            if self.plugins.get("withdraw") and self.plugins["withdraw"].withdraw(part):
                done = 1
            if self.plugins.get("accounts") and self.plugins["accounts"].newuser(part):
                done = 1

        return done

    def send_message(self, retain, topic, message):
        if (
            not "hack42bar/output/session/" + self.SID + "/" + topic in self.cache
            or self.cache["hack42bar/output/session/" + self.SID + "/" + topic]
            != message
            or len(topic) < 8
        ):
            logger.debug(
                "send_message sid=%s retain=%s topic=%s message=%r",
                self.SID,
                retain,
                topic,
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
        logger.info("starting_new_session sid=%s", SID)
        sessions[SID] = Session(SID, client)
        sessions[SID].startup()
        client.publish("hack42bar/output/sessions", json.dumps(list(sessions.keys())))
    return sessions[SID]


def run_session(client, SID, action, data):
    if action == "input":
        session = get_session(SID, client)
        session.input(data.decode())
    else:
        logger.warning("unhandled_session_action sid=%s action=%s", SID, action)


def on_connect(client, _userdata, _flags, rc):
    logger.info("mqtt_connected rc=%s", rc)
    client.subscribe("hack42bar/input/#")


def on_message(client, _userdata, msg):
    elms = msg.topic.split("/")
    msg = msg.payload
    if len(elms) < 5:
        return
    # try:
    run_session(client, elms[3], elms[4], msg)


def run():
    logging_level = getattr(
        logging,
        str(config_get("logging", "level", default="INFO")).upper(),
        logging.INFO,
    )
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    while 1:
        try:
            mqtt_config = config_get("mqtt", default={})
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message

            client.connect(
                mqtt_config["host"],
                int(mqtt_config["port"]),
                int(mqtt_config["keepalive"]),
            )
            client.loop_start()
            while True:
                time.sleep(1)
            # client.loop_forever()
        except Exception:
            logger.exception("Kassa MQTT loop failed")
            time.sleep(5)


if __name__ == "__main__":
    run()
