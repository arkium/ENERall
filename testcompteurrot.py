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
import sys
import threading
import time

from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4
from tinkerforge.ip_connection import Error, IPConnection

log.basicConfig(level=log.INFO)


class DataENERall:
    """
    Classe de test pour compter le nombre d'impulsion.
    """
    HOST = "192.168.42.1"
    PORT = 4223

    ipcon = None
    din = None

    compteur = 0

    def __init__(self):
        self.ipcon = IPConnection()
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

        self.compte_thread = threading.Thread(target=self.cb_compteur)
        self.compte_thread.daemon = True
        self.compte_thread.start()

    def cb_compteur(self):
        """
        Compteur callback
        """
        time.sleep(10)  # Affiche le compteur toutes les 10 secondes
        # Récupérer valeur compteur pin 3 et mettre à zéro
        text = self.din.get_edge_count(8, True)
        log.info("Compteur:" + str(text))

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """
        Recherche des brickets et configuration.
        """
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == IndustrialDigitalIn4.DEVICE_IDENTIFIER:
                try:
                    self.din = IndustrialDigitalIn4(uid, self.ipcon)
                    # pin3, falling, 0ms debounce
                    self.din.set_edge_count_config(8, 1, 0)
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

    if sys.version_info < (3, 0):
        INPUT = raw_input  # Compatibility for Python 2.x
    INPUT('Press key to exit\n')

    if COM.ipcon != None:
        COM.ipcon.disconnect()

    log.info('Compteur rotation: End')
