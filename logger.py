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

"""Module pour l'enregistrement des données dans une base de données sqlite."""

import logging as log
import sqlite3
import threading
import time
import statistics as stat

class LOGGER:
    """Classe d'enregistrement des données dans une base de données locale sqlite.

    Nom du fichier : enerall.db"""

    conn = None
    debug = False #Pour le debugage du logger
    timectrl = 0.2 #Temps pour la période du contrôleur
    ecarttype = [] #Tableau des valeurs puissances pour le calcul de l'écart type

    def __init__(self, time_period=300, name_db="enerall.db"):
        self.items = {}
        self.items_tosave = {}
        self.ecarttype.clear()

        self.time_period = time_period #Période pour l'enregistrement des données.  Défaut: 5 minutes
        self.name_db = name_db #Nom du fichier de la base de données

        self.conn = sqlite3.connect(self.name_db)
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
            data (identifier text, time text, avg_value real, min_value real, max_value real, population real, energy real, ecarttype real)""")
        self.conn.commit()

        log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Start logger')
        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        """Acquisition des données.

        :param identifier: Clé de la donnée

        :param value: Valeur de la donnée"""

        try:
            sum_value, min_value, max_value, count_value, energy = self.items[identifier]
            value = round(value, 4)
            sum_value = sum_value + value
            count_value += 1
            if identifier == "Power":
                energy = energy + (value * self.timectrl)
                self.ecarttype.append(value)
            else:
                energy = 0
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (sum_value, min_value, max_value, count_value, energy)
        except:
            self.items[identifier] = (value, value, value, 0, 0)

    def upload(self):
        """Enregistrer les données dans la base de données toutes les x minutes."""

        while True:
            time.sleep(self.time_period)  # Upload data every 5min
            result = len(self.items)
            if result == 0:
                continue

            try:
                if self.debug:
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' sqlite3 connection: ' + self.name_db)
                self.conn = sqlite3.connect(self.name_db)
                self.items_tosave = self.items
                self.items = {}
                for identifier, value in self.items_tosave.items():
                    avg_value = value[0] / value[3]
                    avg_value = round(avg_value, 4)
                    if identifier == "Power":
                        ecarttype = stat.pvariance(self.ecarttype, avg_value)
                        self.ecarttype.clear()
                    else:
                        ecarttype = 0

                    data = {"identifier": identifier,
                            "avg_value": avg_value,
                            "min_value": value[1],
                            "max_value": value[2],
                            "population": value[3],
                            "energy": value[4],
                            "ecarttype": ecarttype}
                    cursor = self.conn.cursor()
                    cursor.execute("""INSERT INTO data(identifier, time, avg_value, min_value, max_value, population, energy, ecarttype)
                        VALUES(:identifier, datetime('now'), :avg_value, :min_value, :max_value, :population, :energy, :ecarttype)""", data)
                    self.conn.commit()
                    if self.debug:
                        log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Sauvegarde de:' + str(data))

            except Exception as err:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Error: ' + str(err) + ' // ' + str(data))
                self.conn.rollback()
            finally:
                self.conn.close()
                if self.debug:
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' sqlite3 close')

            self.items_tosave = {}

    def set_time_period(self, value):
        """Définir la période pour l'enregistrement des données.

        :param value: integer en seconde"""

        self.time_period = value

    def set_name_db(self, value):
        """Définir le nom du fichier de la base de données en sqlite.

        :param value: string"""

        self.name_db = value