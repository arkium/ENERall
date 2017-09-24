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
Programme pour tester la régulation.
"""

import time
import matplotlib.pyplot as plt
import controleur as PID
import logger


def test_controleur(gpt=0.01, gpu=0.5, gpd=0.16, long=400):
    """Initialisation du controleur"""
    ctrl = PID.CONTROLEUR(gpt, gpu, gpd)

    log = logger.LOGGER(0.02) #Test de l'enregistrement tous les 20ms

    time_list = []
    rotation_list = []
    rotation_free_list = []
    torque_list = []
    power_list = []
    power_tested_list = []

    time_list.append(0)
    rotation_free_list.append(0)
    rotation_list.append(0)
    torque_list.append(ctrl.torque)
    power_list.append(ctrl.power_last)
    power_tested_list.append(ctrl.power)

    end = long
    rot_ini = 0
    rotation = 0
    for i in range(1, end):
        ctrl.update(rotation)
        if rotation > -1:
            rotation = rot_ini - (ctrl.torque * 0.3)
            if rotation < 0:
                rotation = 0
        if i > 0 and i < 80:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 2:
                rot_ini = 2
        if i > 80 and i < 150:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 6:
                rot_ini = 6
        if i > 150 and i < 225:
            rot_ini = rot_ini - (1 * 0.2)
            if rot_ini < 2:
                rot_ini = 2
        if i > 225 and i < 300:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 10:
                rot_ini = 10
        if i > 300 and i < 400:
            rot_ini = rot_ini - (1 * 0.2)
            if rot_ini < 2:
                rot_ini = 2
        time.sleep(0.02)

        time_list.append(i)
        rotation_list.append(rotation)
        rotation_free_list.append(rot_ini)
        torque_list.append(ctrl.torque)
        power_list.append(ctrl.power_last)
        power_tested_list.append(ctrl.power)

        log.put('rotation', rotation)
        log.put('torque_setpoint', ctrl.torque)
        log.put('power_current', ctrl.power_last)

    plt.plot(time_list, rotation_list, label='Rot Turbine (rad/s)')
    plt.plot(time_list, torque_list, label='Couple Turbine (Nm)')
    plt.plot(time_list, power_list, label='P actuelle (Watt)')
    plt.plot(time_list, power_tested_list, label='P à tester (Watt)')
    plt.plot(time_list, rotation_free_list, '--',
             label='Rot sans couple (rad/s)')
    plt.legend()
    plt.xlim((-2, long))
    plt.ylim((-5, 90))
    plt.xlabel('Cycle')
    plt.title('TEST CONTROLEUR')
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    test_controleur(0.01, 0.5, 0.1, long=400)
