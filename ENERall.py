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
Module de régulation du projet ENERall.

Version 0.1
"""

import logging as log
import socket
import sys
import threading
import time

from tinkerforge.bricklet_accelerometer import Accelerometer
from tinkerforge.bricklet_industrial_analog_out import IndustrialAnalogOut
from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4
from tinkerforge.bricklet_real_time_clock import RealTimeClock
from tinkerforge.bricklet_sound_intensity import SoundIntensity
from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.ip_connection import Error, IPConnection

import controleur as PID

import logger

log.basicConfig(level=log.INFO)


class DataENERall:
    """Classe de régulation du projet ENERall
    """
    HOST = "192.168.42.1" #192.168.42.1 ou localhost
    PORT = 4223
    ipcon = None

    ctrl = None
    logger = None

    temp = None
    sound = None
    accel = None
    clock = None
    aout = None
    din = None

    time_calcul = 1

    def __init__(self):
        self.ctrl = PID.CONTROLEUR(0.01, 0.5, 0.1)
        self.logger = logger.LOGGER()
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

        if self.aout.is_enabled and not self.din:
            log.info('Start controleur')
            self.ctrl_thread = threading.Thread(target=self.cb_controleur)
            self.ctrl_thread.daemon = True
            self.ctrl_thread.start()
        else:
            log.info('Error start controleur')

    def cb_controleur(self):
        """
        Controleur callback
        """
        # Calculer le couple toute les x secondes selon time_calcul
        time.sleep(self.time_calcul)

        # Récupérer valeur compteur pin 3 et mettre à zéro
        # Calculer la fréquence en fonction du time_calcul
        frequence = self.din.get_edge_count(8, True) / self.time_calcul
        # Convertir impulsion en vitesse angulaire
        self.ctrl.to_angular_velocity(frequence)
        # Calculer le couple nécessaire
        self.ctrl.update(self.ctrl.angular_velocity)
        # Convertir Couple en Voltage
        self.ctrl.torque_to_voltage(self.ctrl.torque_setpoint)
        # Envoyer le nouveau voltage
        self.aout.set_voltage(self.ctrl.torque_voltage)
        log.info('Controleur Couple: ' + str(self.ctrl.torque_setpoint))

    def cb_temperature(self, temperature):
        """
        Temperature callback
        """
        text = 'Temperature %7.2f ?C' % (temperature / 100.0)
        self.logger.put('Temperature', temperature / 100.0)
        log.info('Write to line 1: ' + text)

    def cb_sound(self, intensity):
        """
        Sound callback
        """
        text = 'Intensity %7.2f' % (intensity)
        self.logger.put('Intensity', intensity)
        log.info('Write to line 2: ' + text)

    def cb_accelerometer(self, xdata, ydata, zdata):
        """
        Accelerometer callback
        """
        text = "Acceleration[X]: " + str(xdata / 1000.0) + " g"
        self.logger.put('AccelX', xdata / 1000.0)
        log.info('Write to line 3: ' + text)
        text = "Acceleration[Y]: " + str(ydata / 1000.0) + " g"
        self.logger.put('AccelY', ydata / 1000.0)
        log.info('Write to line 4: ' + text)
        text = "Acceleration[Z]: " + str(zdata / 1000.0) + " g"
        self.logger.put('AccelZ', zdata / 1000.0)
        log.info('Write to line 5: ' + text)

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """
        Recherche des brickets et configuration.
        """
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == Temperature.DEVICE_IDENTIFIER:
                try:
                    self.temp = Temperature(uid, self.ipcon)
                    self.temp.set_temperature_callback_period(1000)
                    self.temp.register_callback(
                        self.temp.CALLBACK_TEMPERATURE, self.cb_temperature)
                    log.info('Temperature initialized')
                except Error as err:
                    log.error('Temperature init failed: ' +
                              str(err.description))
                    self.temp = None
            elif device_identifier == SoundIntensity.DEVICE_IDENTIFIER:
                try:
                    self.sound = SoundIntensity(uid, self.ipcon)
                    self.sound.set_intensity_callback_period(1000)
                    self.sound.register_callback(
                        self.sound.CALLBACK_INTENSITY, self.cb_sound)
                    log.info('Sound intensity initialized')
                except Error as err:
                    log.error('Sound intensity init failed: ' +
                              str(err.description))
                    self.sound = None
            elif device_identifier == Accelerometer.DEVICE_IDENTIFIER:
                try:
                    self.accel = Accelerometer(uid, self.ipcon)
                    self.accel.set_acceleration_callback_period(1000)
                    self.accel.register_callback(
                        self.accel.CALLBACK_ACCELERATION, self.cb_accelerometer)
                    log.info('Accelerometer initialized')
                except Error as err:
                    log.error('Accelerometer init failed: ' +
                              str(err.description))
                    self.accel = None
            elif device_identifier == RealTimeClock.DEVICE_IDENTIFIER:
                try:
                    self.clock = RealTimeClock(uid, self.ipcon)
                    log.info('RealTimeClock initialized')
                except Error as err:
                    log.error('RealTimeClock init failed: ' +
                              str(err.description))
                    self.clock = None
            elif device_identifier == IndustrialAnalogOut.DEVICE_IDENTIFIER:
                try:
                    self.aout = IndustrialAnalogOut(uid, self.ipcon)
                    self.aout.set_configuration(
                        self.aout.VOLTAGE_RANGE_0_TO_5V, self.aout.CURRENT_RANGE_0_TO_20MA)
                    self.aout.enable()
                    log.info('IndustrialAnalogOut initialized')
                except Error as err:
                    log.error('IndustrialAnalogOut init failed: ' +
                              str(err.description))
                    self.aout = None
            elif device_identifier == IndustrialDigitalIn4.DEVICE_IDENTIFIER:
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
    log.info('ENERall: Start')

    COM = DataENERall()

    if sys.version_info < (3, 0):
        INPUT = raw_input # Compatibility for Python 2.x
    INPUT('Press key to exit\n')

    if COM.ipcon != None:
        COM.ipcon.disconnect()

    log.info('ENERall: End')
