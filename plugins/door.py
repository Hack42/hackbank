#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

import paho.mqtt.client as mqtt
from config import config_get

logger = logging.getLogger(__name__)


class door:
    def __init__(self, SID, master):
        self.master = master
        self.SID = SID

    def help(self):
        logger.debug("door_help sid=%s", self.SID)
        return {"dooropen": "Door open"}

    def input(self, text):
        if text == "dooropen":
            mqtt_config = config_get("door", "mqtt", default={})
            client = mqtt.Client()
            topic = mqtt_config["topic"]
            client.connect(
                mqtt_config["host"],
                int(mqtt_config["port"]),
                int(mqtt_config["keepalive"]),
            )
            client.publish(topic, "closed", 1, True)
            client.publish(topic, "open", 1, True)
            client.disconnect()
            return True
        return None

    def startup(self):
        pass
