# ANT - Heart Rate Monitor Example
#
# Copyright (c) 2012, Gustav Tiger <gustav@tiger.name>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, print_function

from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message

import logging
import struct
import threading
import sys
import RPi.GPIO as GPIO
import time
import traceback



# define the heartrate levels ; 
# if heartrate is greater then first value in this list, the fan will be turned on 
#
myHeartrateLevel = [90,120,130,140]

# if your fan has 4 speeds 
pinList = [2, 3, 4, 17]
# if your fan has 3 speeds 
#pinList = [2, 3, 4]



logFileName = '/tmp/ant_logging.log'
#logging.basicConfig(filename=logFileName, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
logging.basicConfig(level=logging.INFO)

myGears = [0,1,2,3,4,5,6]

# time to sleep between operations in the main loop
SleepTimeL = 2

NETWORK_KEY= [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

# callback 
def on_data(data):
    heartrate = data[7]
    i = 0
    g = 0 
    while i < len(fan.pinlist):
       if heartrate >= myHeartrateLevel[i]:
          g = i + 1
       i += 1
    fan.gearOn(g) 
    string = "Heartrate: " + str(heartrate) + " [BPM] | Fan gear: " + str(fan.gear)
    logging.info(string)

# GPIO control for relais 
class Fan:
    def __init__(self, pinlist):
        self.gear=0 
        self.pinlist = pinlist
        i=0
        while i < len(self.pinlist):
           GPIO.setup(self.pinlist[i], GPIO.OUT)
           i += 1
    def gearOn(self,newgear):
        logging.debug('new Fan gear :' + str(newgear) )
        if newgear == self.gear or newgear < 0 :
           return
        if newgear > len(self.pinlist):
            string = "wrong gear number:" + str(newgear) + " Max gear is : " + str(len(self.pinlist)) 
            logging.error("string")
            raise Exception(string)
        self.gearOff()
        self.gear=newgear
        logging.info('Fan gear :' + str(self.gear) )
        if self.gear > 0:
            GPIO.output(self.pinlist[self.gear-1],GPIO.LOW)
            logging.debug('Fan Gear ON Pin: ' + str(self.pinlist[self.gear-1]) )
    def gearOff(self):
        i=0
        while i < len(self.pinlist):
           GPIO.output(self.pinlist[i] ,  GPIO.HIGH)
           i += 1
        self.gear=0 
        logging.debug('Fan off')

# 
#
def main():
    fan.gearOff()
    logging.info("Setting:")
    i = 0
    while i < len(fan.pinlist):
        info = "*  gear " + str(i+1) + " if heartrate greater " + str(myHeartrateLevel[i]) 
        i += 1
        logging.info(info)
    # ant device
    node = Node()
    node.set_network_key(0x00, NETWORK_KEY)
    channel = node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
    # define the callback
    channel.on_broadcast_data = on_data
    channel.on_burst_data = on_data
    #  
    channel.set_period(8070)
    channel.set_search_timeout(12)
    channel.set_rf_freq(57)
    channel.set_id(0, 120, 0)

    try:
        channel.open()
        node.start()
    finally:
        fan.gearOff()
        node.stop()
        GPIO.cleanup()


run=True
GPIO.setmode(GPIO.BCM)
fan = Fan(pinList)

while run:
    try:
        main()
    except KeyboardInterrupt:
       run=False
    except:
        logging.error(sys.exc_info()[0])
        #print("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)
        time.sleep(2)
    finally:
        fan.gearOff()
