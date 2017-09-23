#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2017  Paulo Ferreira <paulo.ferreira@arkium.eu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA.

import http.client
import json
import logging as log
import math
import socket
import sys
import threading
import time

class LOGGER:
    """Enregistrement"""
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
            "Content-Type": "application/x-www-form-urlencoded",
            "X-ApiKey": self.API_KEY,
            "User-Agent": self.AGENT,
        }
        #"X-Warp10-Token"    : OvhMetrics.token_key,
        #"Content-Type"      : "text/plain"
        self.params = "http://api.xively.com/v2/feeds/" + str(self.FEED)
        # self.params = OvhMetrics.HOST+"/api/v0/update"
        # self.url = "/api/v0/update"
        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        """Saisie des données"""
        temp = int(time.time())
        try:
            _, min_value, max_value = self.items[identifier]
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (value, min_value, max_value, temp)
        except ValueError as err:
            self.items[identifier] = (value, value, value, temp)

    def upload(self):
        """Enregistrer les données"""
        while True:
            time.sleep(1 * 10)  # Upload data every 5min
            if len(self.items) == 0:
                continue

            stream_items = []
            for identifier, value in self.items.items():
                # stream_items.append(str(value[3]) + '// ' + identifier + '{devio=01} ' + str(value[0]))
                stream_items.append({'id': identifier,
                                     'current_value': value[0],
                                     'min_value': value[1],
                                     'max_value': value[2]})

            self.items = {}
            data = {'version': '1.0.0',
                    'datastreams': stream_items}
            body = json.dumps(data)
            # text = chr(13).join(stream_items)

            try:
                log.info('OvhMetrics')
                log.info(body)
                # com = http.client.HTTPSConnection(OvhMetrics.HOST)
                # com.connect()
                # com.request('PUT', self.url, text, self.headers)
                # response = com.getresponse()
                # com.close()
                # s = requests.Session()
                # s.mount('https://', MyAdapter())

                # response = s.post(self.params, data=text, headers=self.headers)
                # com = http.client.HTTPConnection(self.HOST)
                # com.request('PUT', self.params, body, self.headers)
                # response = com.getresponse()
                # com.close()
                response = requests.post(
                    self.params, json=body, headers=self.headers)
                if response.status_code != 200:
                    # if response.status != 200:
                    # log.error('Could not upload to OvhMetrics -> ' + str(response.status) + ': ' + response.msg)
                    log.error('Could not upload to OvhMetrics -> ' +
                              str(response.status_code) + ': ' + response.text)
                    log.error(str(response.raw))
            except Exception as err:
                log.error('HTTP error: ' + str(err))
