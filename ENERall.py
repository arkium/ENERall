#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time
import math
import logging as log
import requests
import json
import threading
import http.client
log.basicConfig(level=log.INFO)

from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.brick_master import Master

from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.bricklet_real_time_clock import RealTimeClock
from tinkerforge.bricklet_accelerometer import Accelerometer
from tinkerforge.bricklet_sound_intensity import SoundIntensity
from tinkerforge.bricklet_industrial_analog_out import IndustrialAnalogOut
from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4

#import http.client

class Logger:
    HOST = 'api.xively.com'
    AGENT = "Tinkerforge xively 1.0"
    FEED = '91249686-9fa2-4dfe-8d7c-495d5b1bb493'
    API_KEY = 'd34ec270-f524-4578-84ee-6fe1c5039606'

#    HOST = 'https://warp10.gra1.metrics.ovh.net'
    token_id = '5a227c6c-5336-4de2-9870-fff40644a4d7'
    token_key = 'TOXxSX1J7W.yYMSf6vAmK4J5hRNvhkr27Fzt_2k0RI8vgW9h12YZoeifPNmU3Vs_r4.WETWq83gTRquw_Tu2DcfaBPw7KKuT76WMkGMGD7.LY3cMQrgJEIWYHqJ2Bcme'

    def __init__(self):
        self.items = {}
        self.headers = {
            "Content-Type"  : "application/x-www-form-urlencoded",
            "X-ApiKey"      : self.API_KEY,
            "User-Agent"    : self.AGENT,
        }
        #"X-Warp10-Token"    : OvhMetrics.token_key,
        #"Content-Type"      : "text/plain"
        self.params = "http://api.xively.com/v2/feeds/" + str(self.FEED)
        #self.params = OvhMetrics.HOST+"/api/v0/update"
        #self.url = "/api/v0/update"
        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        t = int(time.time())
        try:
            _, min_value, max_value = self.items[identifier]
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (value, min_value, max_value, t)
        except:
            self.items[identifier] = (value, value, value, t)

    def upload(self):
        while True:
            time.sleep(1*10) # Upload data every 5min
            if len(self.items) == 0:
                continue

            stream_items = []
            for identifier, value in self.items.items():
                #stream_items.append(str(value[3]) + '// ' + identifier + '{devio=01} ' + str(value[0]))
                stream_items.append({'id': identifier,
                                     'current_value': value[0],
                                     'min_value': value[1],
                                     'max_value': value[2]})

            self.items = {}
            data = {'version': '1.0.0',
                    'datastreams': stream_items}
            body = json.dumps(data)
            #text = chr(13).join(stream_items)

            try:
                log.info('OvhMetrics')
                log.info(body)
                #com = http.client.HTTPSConnection(OvhMetrics.HOST)
                #com.connect()
                #com.request('PUT', self.url, text, self.headers)
                #response = com.getresponse()
                #com.close()
                #s = requests.Session()
                #s.mount('https://', MyAdapter())

                #response = s.post(self.params, data=text, headers=self.headers)
                #com = http.client.HTTPConnection(self.HOST)
                #com.request('PUT', self.params, body, self.headers)
                #response = com.getresponse()
                #com.close()
                response = requests.post(self.params, json=body, headers=self.headers)
                if response.status_code != 200:
                #if response.status != 200:
                    #log.error('Could not upload to OvhMetrics -> ' + str(response.status) + ': ' + response.msg)
                    log.error('Could not upload to OvhMetrics -> ' + str(response.status_code) + ': ' + response.text)
                    log.error(str(response.raw))
            except Exception as e:
                log.error('HTTP error: ' + str(e))

class DataENERall:
    HOST = "localhost"
    PORT = 4223

    ipcon = None
    temp = None
    sound = None
    accel = None
    clock = None
    aout = None
    din = None

    def __init__(self):
        self.ovhmetrics = OvhMetrics()
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(self.HOST, self.PORT)
                log.info('TCP/IP connection')
                break
            except Error as e:
                log.error('Connection Error: ' + str(e.description))
                time.sleep(1)
            except socket.error as e:
                log.error('Socket error: ' + str(e))
                time.sleep(1)

        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED, self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                log.info('Calling all Bricklets')
                break
            except Error as e:
                log.error('Enumerate Error: ' + str(e.description))
                time.sleep(1)

    def cb_temperature(self, temperature):
        text = 'Temperature %7.2f ?C' % (temperature/100.0)
        self.ovhmetrics.put('Temperature', temperature/100.0)
        log.info('Write to line 1: ' + text)

    def cb_sound(self, intensity):
        text = 'Intensity %7.2f' % (intensity)
        self.ovhmetrics.put('Intensity', intensity)
        log.info('Write to line 2: ' + text)

    def cb_accelerometer(self, x, y, z):
        text = "Acceleration[X]: " + str(x/1000.0) + " g"
        self.ovhmetrics.put('AccelX', x/1000.0)
        log.info('Write to line 3: ' + text)
        text = "Acceleration[Y]: " + str(y/1000.0) + " g"
        self.ovhmetrics.put('AccelY', y/1000.0)
        log.info('Write to line 4: ' + text)
        text = "Acceleration[Z]: " + str(z/1000.0) + " g"
        self.ovhmetrics.put('AccelZ', z/1000.0)
        log.info('Write to line 5: ' + text)

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == Temperature.DEVICE_IDENTIFIER:
                try:
                    self.temp = Temperature(uid, self.ipcon)
                    self.temp.set_temperature_callback_period(1000)
                    self.temp.register_callback(self.temp.CALLBACK_TEMPERATURE, self.cb_temperature)
                    log.info('Temperature initialized')
                except Error as e:
                    log.error('Temperature init failed: ' + str(e.description))
                    self.temp = None
            elif device_identifier == SoundIntensity.DEVICE_IDENTIFIER:
                try:
                    self.sound = SoundIntensity(uid, self.ipcon)
                    self.sound.set_intensity_callback_period(1000)
                    self.sound.register_callback(self.sound.CALLBACK_INTENSITY, self.cb_sound)
                    log.info('Sound intensity initialized')
                except Error as e:
                    log.error('Sound intensity init failed: ' + str(e.description))
                    self.sound = None
            elif device_identifier == Accelerometer.DEVICE_IDENTIFIER:
                try:
                    self.accel = Accelerometer(uid, self.ipcon)
                    self.accel.set_acceleration_callback_period(1000)
                    self.accel.register_callback(self.accel.CALLBACK_ACCELERATION, self.cb_accelerometer)
                    log.info('Accelerometer initialized')
                except Error as e:
                    log.error('Accelerometer init failed: ' + str(e.description))
                    self.accel = None
            elif device_identifier == RealTimeClock.DEVICE_IDENTIFIER:
                try:
                    self.clock = RealTimeClock(uid, self.ipcon)
                    log.info('RealTimeClock initialized')
                except Error as e:
                    log.error('RealTimeClock init failed: ' + str(e.description))
                    self.clock = None
            elif device_identifier == IndustrialAnalogOut.DEVICE_IDENTIFIER:
                try:
                    self.aout = IndustrialAnalogOut(uid, self.ipcon)
                    log.info('IndustrialAnalogOut initialized')
                except Error as e:
                    log.error('IndustrialAnalogOut init failed: ' + str(e.description))
                    self.aout = None
            elif device_identifier == IndustrialDigitalIn4.DEVICE_IDENTIFIER:
                try:
                    self.din = IndustrialDigitalIn4(uid, self.ipcon)
                    log.info('IndustrialDigitalIn4 initialized')
                except Error as e:
                    log.error('IndustrialDigitalIn4 init failed: ' + str(e.description))
                    self.din = None

    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')

            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate Error: ' + str(e.description))
                    time.sleep(1)

if __name__ == "__main__":
    log.info('Data ENERall: Start')

    data_ENERall = DataENERall()

    if sys.version_info < (3, 0):
        input = raw_input # Compatibility for Python 2.x
    input('Press key to exit\n')

    if data_ENERall.ipcon != None:
        data_ENERall.ipcon.disconnect()

    log.info('Data ENERall: End')