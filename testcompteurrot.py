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

"""
Module pour tester le compteur d'impulsion sur l'arbre du frein.
"""

import logging as log
import socket
import threading
import time

from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4
from tinkerforge.ip_connection import Error, IPConnection

log.basicConfig(level=log.INFO)


class DataENERall:
    """
    Classe de test pour compter le nombre d'impulsion.
    """
    HOST = "localhost" #192.168.42.1
    PORT = 4223

    ipcon = None
    din = None
    compte_thread = None

    compteur_turbine = 0

    def __init__(self):
        self.ipcon = IPConnection()
        #self.compte_thread = None
        while True:
            try:
                self.ipcon.connect(self.HOST, self.PORT)
                log.info('TCP/IP connection')
                break
            except Error as err:
                log.error('Connection Error: ' + str(err.description))
                time.sleep(1)
            except socket.error as err:
                log.error('Socket error: ' + str(err))
                time.sleep(1)

        self.ipcon.register_callback(
            IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
        self.ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED, self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                log.info('Calling all Bricklets')
                break
            except Error as err:
                log.error('Enumerate Error: ' + str(err.description))
                time.sleep(1)

        #log.info('Pile compteur')
        #self.compte_thread = threading.Thread(target=self.cb_compteur)
        #self.compte_thread.daemon = False
        #self.compte_thread.start()

    def cb_compteur_turbine(self, interrupt_mask, value_mask):
        """
        Comptage du nombre de tours callback
        """
        print(str(value_mask) + ' ' + str(interrupt_mask))
        if (value_mask == 1) and (interrupt_mask == 8):
            self.compteur_turbine += 1
        print(str(self.compteur_turbine))

    def get_compteur(self, reset = False):
        total = self.compteur_turbine
        if reset:
            self.compteur_turbine = 0
        return total

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """
        Recherche des brickets et configuration.
        """
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == IndustrialDigitalIn4.DEVICE_IDENTIFIER:
                try:
                    self.din = IndustrialDigitalIn4(uid, self.ipcon)
                    self.din.set_interrupt(8)
                    self.din.set_debounce_period(0)
                    self.din.register_callback(self.din.CALLBACK_INTERRUPT, self.cb_compteur_turbine)
                    log.info('IndustrialDigitalIn4 initialized')
                except Error as err:
                    log.error('IndustrialDigitalIn4 init failed: ' +
                              str(err.description))
                    self.din = None

    def cb_connected(self, connected_reason):
        """
        Connection aux bricks
        """
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')

            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as err:
                    log.error('Enumerate Error: ' + str(err.description))
                    time.sleep(1)


if __name__ == "__main__":
    log.info('Compteur rotation: Start')

    COM = DataENERall()

    time.sleep(5)
    print(str(COM.compteur_turbine))
    time.sleep(5)
    print(COM.get_compteur(True))
    time.sleep(5)
    print(COM.get_compteur(True))
    input('Press key to exit\n')

    if COM.ipcon != None:
        COM.ipcon.disconnect()

    log.info('Compteur rotation: End')
