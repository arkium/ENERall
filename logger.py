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


class LOGGER:
    """Classe d'enregistrement des données dans une base de données locale sqlite.

    Nom du fichier : enerall.db"""

    conn = None

    def __init__(self, time_period=300, name_db="enerall.db"):
        self.items = {}

        self.time_period = time_period #Période pour l'enregistrement des données.  Défaut: 5 minutes
        self.name_db = name_db #Nom du fichier de la base de données

        self.conn = sqlite3.connect(self.name_db)
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
            data (identifier text, time text, avg_value real, min_value real, max_value real)""")
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
            sum_value, min_value, max_value, count_value = self.items[identifier]
            sum_value = sum_value + value
            count_value += 1
            if value < min_value:
                min_value = round(value, 4)
            if value > max_value:
                max_value = round(value, 4)
            self.items[identifier] = (sum_value, min_value, max_value, count_value)
        except:
            self.items[identifier] = (value, value, value, 0)

    def upload(self):
        """Enregistrer les données dans la base de données toutes les x minutes."""

        while True:
            time.sleep(self.time_period)  # Upload data every 5min
            result = len(self.items)
            if result == 0:
                continue

            try:
                log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' sqlite3 connection: ' + self.name_db)
                self.conn = sqlite3.connect(self.name_db)
                for identifier, value in self.items.items():
                    avg_value = value[0] / value[3]
                    avg_value = round(avg_value, 4)
                    data = {"identifier": identifier,
                            "avg_value": avg_value, "min_value": value[1], "max_value": value[2]}
                    cursor = self.conn.cursor()
                    cursor.execute("""INSERT INTO data(identifier, time, avg_value, min_value, max_value)
                        VALUES(:identifier, datetime('now'), :avg_value, :min_value, :max_value)""", data)
                    self.conn.commit()
                    log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' Sauvegarde de:' + str(data))

            except Exception as err:
                log.error(time.strftime("%Y-%m-%d %H:%M:%S") + ' Error: ' + str(err) + ' // ' + str(data))
                self.conn.rollback()
            finally:
                self.conn.close()
                log.info(time.strftime("%Y-%m-%d %H:%M:%S") + ' sqlite3 close')

            self.items = {}

    def set_time_period(self, value):
        """Définir la période pour l'enregistrement des données.

        :param value: integer en seconde"""

        self.time_period = value

    def set_name_db(self, value):
        """Définir le nom du fichier de la base de données en sqlite.

        :param value: string"""

        self.name_db = value