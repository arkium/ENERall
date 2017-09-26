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
import time

from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4
from tinkerforge.ip_connection import Error, IPConnection

log.basicConfig(level=log.INFO)

HOST = "localhost" #192.168.42.1
PORT = 4223
UID = "vX8"

IPCON = None
DIN = None

def cd_compte(interrupt_mask, value_mask):
    """Fonction d'appel"""
    print('Callback:')
    text2 = DIN.get_response_expected(DIN.FUNCTION_SET_EDGE_COUNT_CONFIG)
    log.info('FUNCTION_SET_EDGE_COUNT_CONFIG: ' + str(text2))
    text2 = DIN.get_edge_count_config(8)
    log.info('Valeur: ' + str(text2))


if __name__ == "__main__":
    try:
        print('Start')
        IPCON = IPConnection()
        log.info('Start Bricklet:')
        DIN = IndustrialDigitalIn4(UID, IPCON)
        log.info('Connect:')
        IPCON.connect(HOST, PORT)
        time.sleep(2)
        text1 = DIN.get_api_version()
        log.info('API: ' + str(text1))
        text2 = DIN.get_response_expected(DIN.FUNCTION_SET_EDGE_COUNT_CONFIG)
        log.info('FUNCTION_SET_EDGE_COUNT_CONFIG: ' + str(text2))
        text2 = DIN.get_response_expected(DIN.FUNCTION_GET_EDGE_COUNT)
        log.info('FUNCTION_GET_EDGE_COUNT: ' + str(text2))
        DIN.set_response_expected(DIN.FUNCTION_SET_EDGE_COUNT_CONFIG, True)
        text2 = DIN.get_response_expected(DIN.FUNCTION_SET_EDGE_COUNT_CONFIG)
        log.info('FUNCTION_SET_EDGE_COUNT_CONFIG: ' + str(text2))
        text2 = DIN.set_edge_count_config(1, 1, 50)
        log.info('set edge: ' + str(text2))
        text2 = DIN.get_edge_count_config(1)
        log.info('Valeur: ' + str(text2))

        DIN.register_callback(DIN.CALLBACK_INTERRUPT, cd_compte)
        DIN.set_interrupt(8)
        text2 = DIN.get_interrupt()
        log.info('Interrupt: ' + str(text2))

        while True:
            time.sleep(2)
            text1 = DIN.get_edge_count(8, False)
            text2 = DIN.get_edge_count_config(1)
            log.info('Valeur: ' + str(text1) + ' ' + str(text2))
            text2 = DIN.get_response_expected(DIN.FUNCTION_SET_EDGE_COUNT_CONFIG)
            log.info('FUNCTION_SET_EDGE_COUNT_CONFIG: ' + str(text2))

        input('Press')
    except Error as err:
        log.error('Connection Error: ' + str(err.description))
        time.sleep(1)
        
    IPCON.disconnect()
