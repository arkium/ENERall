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

compteur = 0

def cd_compte(interrupt_mask, value_mask):
    """Fonction d'appel"""
    if not value_mask & interrupt_mask == 8:
        compteur += 1

def get_compteur(reset=False):
    send = compteur
    if reset:
        compteur = 0
    return send

if __name__ == "__main__":
    try:
        print('Start')
        IPCON = IPConnection()
        DIN = IndustrialDigitalIn4(UID, IPCON)
        IPCON.connect(HOST, PORT)
        print('Init OK')
        time.sleep(2)

        DIN.set_interrupt(8)
        DIN.set_debounce_period(0)
        DIN.register_callback(DIN.CALLBACK_INTERRUPT, cd_compte)

        input('Press')

        print(get_compteur(False))

    except Error as err:
        log.error('Connection Error: ' + str(err.description))
        time.sleep(1)

    IPCON.disconnect()
