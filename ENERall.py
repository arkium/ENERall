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

"""Module de régulation du projet ENERall.

Version 0.1"""

import logging as log
import socket
import threading
import time

from tinkerforge.bricklet_accelerometer import Accelerometer
from tinkerforge.bricklet_industrial_analog_out import IndustrialAnalogOut
from tinkerforge.bricklet_industrial_digital_in_4 import IndustrialDigitalIn4
from tinkerforge.bricklet_industrial_dual_analog_in import IndustrialDualAnalogIn
from tinkerforge.bricklet_real_time_clock import RealTimeClock
from tinkerforge.bricklet_sound_intensity import SoundIntensity
from tinkerforge.bricklet_temperature import Temperature
from tinkerforge.ip_connection import Error, IPConnection

import CONTROLEUR as PID

import logger as loggerData

log.basicConfig(level=log.INFO)


class DataENERall:
    """Classe de régulation du projet ENERall"""

    HOST = "localhost" #192.168.42.1 ou localhost
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
    ain = None

    time_calcul = 1 # en seconde

    compteur_turbine = 0 # Compteur de la turbine

    aout_connected = False
    din_connected = False
    ain_connected = False

    pin_girouette = 1
    pin_anenometre = 0

    debug = False

    def __init__(self):
        self.ctrl = PID.CONTROLEUR(0.01, 0.5, 0.1)
        self.logger = loggerData.LOGGER() #Enregistrement tous les 5 minutes (300s)
        self.logger.timectrl = self.time_calcul
        self.ipcon = IPConnection()

        while True:
            try:
                self.ipcon.connect(self.HOST, self.PORT)
                log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' TCP/IP connection')
                break
            except Error as err:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Connection Error: ' + str(err.description))
                time.sleep(1)
            except socket.error as err:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Socket error: ' + str(err))
                time.sleep(1)

        self.ipcon.register_callback(
            IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
        self.ipcon.register_callback(
            IPConnection.CALLBACK_CONNECTED, self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Calling all Bricklets')
                break
            except Error as err:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Enumerate Error: ' + str(err.description))
                time.sleep(1)

        time.sleep(5) # Attendre 5 secondes avant de lancer le contrôleur
        self.ctrl_thread = threading.Thread(target=self.cb_controleur)
        self.ctrl_thread.daemon = True
        self.ctrl_thread.start()

    def cb_controleur(self):
        """Controleur callback"""

        log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Start controleur after 5 secondes')
        while True:
            # Calculer le couple toute les x secondes selon time_calcul
            time.sleep(self.time_calcul)
            if self.aout_connected and self.din_connected:
                # Récupérer valeur compteur pin 3 et mettre à zéro
                # Calculer la fréquence en fonction du time_calcul
                frequence = ((self.get_compteur(True)/23) / self.time_calcul) # 1 tr/s = 1Hz et 23 = Nombre de dents
                # Convertir fréquence en vitesse angulaire
                self.ctrl.to_angular_velocity(frequence)
                # Calculer le couple nécessaire
                self.ctrl.update(self.ctrl.angular_velocity)
                # Convertir Couple en Voltage
                self.ctrl.torque_to_voltage(self.ctrl.torque)
                # Envoyer le nouveau voltage
                self.aout.set_voltage(self.ctrl.torque_voltage)
                # Enregistrer les données
                self.logger.put('Torque', self.ctrl.torque)
                self.logger.put('Angular', self.ctrl.angular_velocity)
                self.logger.put('Power', self.ctrl.power)
                self.logger.put('Frequence', frequence)
                try:
                    self.logger.put('Temperature', self.temp.get_temperature() / 100.0)
                    self.logger.put('Intensity', self.sound.get_intensity())
                    x, y, z = self.accel.get_acceleration()
                    self.logger.put('AccelX', x / 1000.0)
                    self.logger.put('AccelY', y / 1000.0)
                    self.logger.put('AccelZ', z / 1000.0)
                    self.logger.put('wind_direction', self.cb_wind_direction(self.ain.get_voltage(self.pin_girouette)))
                    self.logger.put('wind_velocity', self.cb_wind_velocity(self.ain.get_voltage(self.pin_anenometre)))
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Bricklet failed: ' +
                        str(err.description))
                # Afficher pour le debug
                if self.debug:
                    text = 'Torque (Nm) %7.2f ' % self.ctrl.torque
                    text = text + 'Angular velocity (ms) %7.2f ' % self.ctrl.angular_velocity
                    text = text + 'Power (W) %7.2f ' % self.ctrl.power
                    text = text + 'Frequence (Hz) %7.2f ' % frequence
                    text = text + 'Voltage (mV) %7.0f ' % self.ctrl.torque_voltage
                    print(text)
            else:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Error in controleur: ' + str(self.aout_connected) + ' ' + str(self.din_connected))

    def cb_wind_direction(self, voltage):
        """Convertir le voltage 0-10V (en mV) en direction du vent (en degré)"""
        direction = ((voltage / 1000) / 10) * 360
        return direction

    def cb_wind_velocity(self, voltage):
        """Convertir le voltage 0-10V (en mV) en vitesse du vent (en m/s)"""
        vitesse = ((voltage / 1000) * 7.49033) 
        return vitesse

    def cb_compteur_turbine(self, interrupt_mask, value_mask):
        """Comptage du nombre de tours callback."""

        #log.info('Compteur Pin: ' + str(value_mask & 8) + ' ' + str(interrupt_mask & 8))
        if ((value_mask & 8) == 8) and ((interrupt_mask & 8) == 8): #pin3 = 8 sur front montant
            self.compteur_turbine += 1
        #log.info(str(self.compteur_turbine))

    def get_compteur(self, reset = False):
        """Renvoi le nombre de tours et remettre à zéro le compteur si nécessaire."""

        total = self.compteur_turbine
        if reset:
            self.compteur_turbine = 0
        return total

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """Recherche des brickets et configuration."""

        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == Temperature.DEVICE_IDENTIFIER:
                try:
                    self.temp = Temperature(uid, self.ipcon)
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Temperature initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Temperature init failed: ' +
                              str(err.description))
                    self.temp = None
            elif device_identifier == SoundIntensity.DEVICE_IDENTIFIER:
                try:
                    self.sound = SoundIntensity(uid, self.ipcon)
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Sound intensity initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Sound intensity init failed: ' +
                              str(err.description))
                    self.sound = None
            elif device_identifier == Accelerometer.DEVICE_IDENTIFIER:
                try:
                    self.accel = Accelerometer(uid, self.ipcon)
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Accelerometer initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Accelerometer init failed: ' +
                              str(err.description))
                    self.accel = None
            elif device_identifier == IndustrialAnalogOut.DEVICE_IDENTIFIER:
                try:
                    self.aout = IndustrialAnalogOut(uid, self.ipcon)
                    self.aout.set_configuration(self.aout.VOLTAGE_RANGE_0_TO_5V, self.aout.CURRENT_RANGE_0_TO_20MA)
                    self.aout.enable()
                    self.aout_connected = True
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialAnalogOut initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialAnalogOut init failed: ' +
                              str(err.description))
                    self.aout = None
            elif device_identifier == IndustrialDualAnalogIn.DEVICE_IDENTIFIER:
                try:
                    self.ain = IndustrialDualAnalogIn(uid, self.ipcon)
                    self.ain.set_sample_rate(6)
                    self.ain_connected = True
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialDualAnalogIn initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialDualAnalogIn init failed: ' +
                              str(err.description))
                    self.ain = None
            elif device_identifier == IndustrialDigitalIn4.DEVICE_IDENTIFIER:
                try:
                    self.din = IndustrialDigitalIn4(uid, self.ipcon)
                    self.din.set_interrupt(8)
                    self.din.set_debounce_period(0)
                    self.din.register_callback(self.din.CALLBACK_INTERRUPT, self.cb_compteur_turbine)
                    self.din_connected = True
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialDigitalIn4 initialized')
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' IndustrialDigitalIn4 init failed: ' +
                              str(err.description))
                    self.din = None

    def cb_connected(self, connected_reason):
        """Connection aux bricks."""

        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Auto Reconnect')

            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as err:
                    log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Enumerate Error: ' + str(err.description))
                    time.sleep(1)


if __name__ == "__main__":
    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' ENERall: Start')

    COM = DataENERall()

    input(time.strftime("%Y-%m-%d %H:%M:%S") + ' Press key to exit\n')

    if COM.ipcon != None:
        COM.ipcon.disconnect()

    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' ENERall: End')
