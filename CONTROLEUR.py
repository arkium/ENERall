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
Module de régulation cherchant à obtenir la puissance max.

Version 0.1
"""

import math


class CONTROLEUR:
    """Controleur cherchant à obtenir la puissance max"""

    def __init__(self, gpt=0.0, gpu=0.0, gpd=0.0):
        self.gap_power_to_test = gpt
        self.gain_power_up = gpu
        self.gain_power_down = gpd

        self.power = 0.0 # Puissance en W (watt)
        self.power_last = 0.0

        self.torque = 0.0  # Couple en Nm
        self.torque_last = 0.0

        self.torque_voltage = 0.0 # Convertion du couple en voltage en mV
        self.angular_velocity = 0.0 # Vitesse angulaire en rad/S

    def update(self, value):
        """
        Calcul le nouveau couple (Nm) necessaire en fonction de la vitesse angulaire (rad/s)

        :param value: Vitesse angulaire (rad/s)

        :return: Couple (Nm)
        """

        # Mémoriser la puissance pour le prochain calcul
        self.torque_last = self.torque
        # Calculer la puissance actuelle
        self.power_last = self.torque_last * value
        # Calculer la puissance réelle (équation caractérisant la turbine)
        power_real = 1.2 * math.exp(0.45 * value) * value
        # Déterminer la différence
        power_gap = power_real - self.power_last
        # Tester si la puissance actuelle augmentée est plus grande que la puissance précédente
        if self.power_last + self.gap_power_to_test >= self.power_last:
            # Calculer la puissance augmentée à tester avec un gain_up
            self.power = self.power_last + \
                (power_gap * self.gain_power_up)
        else:
            # Calculer la puissance diminuée à tester avec un gain_down
            self.power = self.power_last + \
                (power_gap * self.gain_power_down)
        # Limiter la puissance à zéro si vitesse angulaire inférieure à
        if value < 0.7:
            self.power = 0
        # Limiter la puissance à tester à 0 si elle est négative
        if self.power < 0:
            self.power = 0
        # Limiter le couple à zéro si vitesse angulaire est nul ou négative
        if value <= 0:
            self.torque = 0
        else:
            # Calculer le couple à tester
            self.torque = self.power / value
        return self.torque

    def set_gap_power_to_test(self, value):
        """
        Définir la valeur à augmenter la puissance actuelle.

        :param value: floating
        """
        self.gap_power_to_test = value

    def set_gain_power_up(self, value):
        """
        Définir le gain pour augmenter la puissance.

        :param value: floating
        """
        self.gain_power_up = value

    def set_gain_power_down(self, value):
        """
        Définir le gain pour diminuer la puissance.

        :param value: floating
        """
        self.gain_power_down = value

    def to_angular_velocity(self, value):
        """
        Transforme le nombre d'impulsion en une vitesse angulaire (rad/s).

        :param value: Nombre d'impulsion (en Hz)

        :return: Vitesse angualire (en rad/s)

        Faire la calibration pour la conversion.
        """
        # Calculer la vitesse angulaire = 2 x PI x frequence
        result = 2 * math.pi * value
        self.angular_velocity = result
        return self.angular_velocity

    def torque_to_voltage(self, value):
        """
        Transforme le couple (Nm) en une tension (mV).

        :param value: Couple (en Nm)

        :return: Tension (en mV)

        Faire la calibration pour la conversion.
        """
        result = value
        self.torque_voltage = result
        return self.torque_voltage
