
# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
from cbpi.api.dataclasses import NotificationAction, NotificationType
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

@parameters([Property.Actor(label="Actor",  description="Select the actor that will be switched off depending on the GPIO state."),
            Property.Select(label="GPIO_Upper", options=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27], description="GPIO [BMC numbering] of upper Level Sensor"), 
            Property.Select(label="GPIO_Lower", options=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27], description="GPIO [BMC numbering] of lower Level Sensor"), 
            Property.Select(label="GPIOstate", options=["High", "Low"],description="High: Actor switches off when both GPIOstates are high; Low: Actor switches off when both GPIOstates are  low"),
            Property.Select(label="notification", options=["Yes", "No"], description="Will show notification when GPIO switches actor off")])

class GPIODependentActor(CBPiActor):

    async def wait_for_input(self):
        while True:
            input_signal_upper=GPIO.input(int(self.gpio_upper))
            input_signal_lower=GPIO.input(int(self.gpio_lower))
            logging.error("GPIODependentActor: wait_for_input: input_signal_upper: %s and input_signal_lower: %s", input_signal_upper, input_signal_lower)
            if (self.dependency_type == "High"):
                if (GPIO.input(int(self.gpio_upper))) and (GPIO.input(int(self.gpio_lower))):
                    logging.error("GPIODependentActor: Start on both high")
                    await self.on()
                    self.state = False
                    if self.notification == "Yes":
                        self.cbpi.notify("GPIO Dependent Actor", "Actor {} switched on as lower GPIO {} and upper GPIIO {} siwtchted to {}".format(self.name, self.gpio_lower, self.gpio_upper, self.dependency_type), NotificationType.error)
                elif (not GPIO.input(int(self.gpio_upper))) and not (GPIO.input(int(self.gpio_lower))):
                    logging.error("GPIODependentActor: Stop on both low")
                    await self.off()
                    self.state = False
                    if self.notification == "Yes":
                        self.cbpi.notify("GPIO Dependent Actor", "Actor {} switched on as lower GPIO {} and upper GPIIO {} siwtchted to {}".format(self.name, self.gpio_lower, self.gpio_upper, self.dependency_type), NotificationType.error)
                break
            elif (self.dependency_type == "Low") and not (GPIO.input(int(self.gpio_upper))) and not (GPIO.input(int(self.gpio_lower))):
                logging.error("GPIODependentActor: Break on Low")
                await self.off()
                self.state = False
                if self.notification == "Yes":
                    self.cbpi.notify("GPIO Dependent Actor", "Actor {} switched off as GPIO {} siwtchted to {}".format(self.name, self.gpio_upper, self.dependency_type), NotificationType.error)
                break
            if self.interrupt == True:
                break
            await asyncio.sleep(1)

    def on_start(self):
        self.state = False
        self.base = self.props.get("Actor", None)
        try:
            self.name = (self.cbpi.actor.find_by_id(self.base).name)
        except:
            self.name = ""
        self.gpio_upper = self.props.get("GPIO_Upper", None)
        self.gpio_lower = self.props.get("GPIO_Lower", None)
        self.dependency_type = self.props.get("GPIOstate", "High")
        self.notification = self.props.get("notification", "Yes")
        self.interrupt = False
        mode = GPIO.getmode()
        logging.error("GPIODependentActor: on_start GPIO mode: %s", mode)
        if (mode == None):
            GPIO.setmode(GPIO.BCM)
        if self.gpio_upper is not None:
            GPIO.setup(int(self.gpio_upper), GPIO.IN)
        if self.gpio_lower is not None:
            GPIO.setup(int(self.gpio_lower), GPIO.IN)
        else:
            pass

        pass

    async def on(self, power=0):
        logging.error("GPIODependentActor: on")
        self.interrupt = False
        await self.cbpi.actor.on(self.base)
        self._task = asyncio.create_task(self.wait_for_input())
        self.state = True

    async def off(self):
        logging.error("ACTOR %s OFF " % self.base)
        await self.cbpi.actor.off(self.base)
        self.interrupt = True
        self.state = False

    def get_state(self):
        logging.error("GPIODependentActor: get_state: %s", self.state)
        return self.state
    
    async def run(self):
        logging.error("GPIODependentActor: run")
        pass


def setup(cbpi):
    cbpi.plugin.register("GPIO Dependent Actor", GPIODependentActor)
    pass

