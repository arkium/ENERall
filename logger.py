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
Module pour l'enregistrement des données dans une base de données sqlite.
"""

import logging as log
import sqlite3
import threading
import time


class LOGGER:
    """
    Classe d'enregistrement des données dans une base de données locale sqlite.

    Nom du fichier : enerall.db
    """
    conn = None

    def __init__(self):
        self.items = {}

        self.conn = sqlite3.connect('enerall.db')
        cursor = self.conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS
            data (identifier text, time text, avg_value real, min_value real, max_value real)""")
        self.conn.commit()

        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        """
        Acquisition des données.

        :param identifier: Clé de la donnée

        :param value: Valeur de la donnée
        """
        try:
            _, min_value, max_value = self.items[identifier]
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (value, min_value, max_value)
        except:
            self.items[identifier] = (value, value, value)

    def upload(self):
        """
        Enregistrer les données dans la base de données toutes les x minutes.
        """
        while True:
            time.sleep(5 * 60)  # Upload data every 5min
            if len(self.items) == 0:
                continue

            try:
                log.info('sqlite3 connection')
                self.conn = sqlite3.connect('enerall.db')
                for identifier, value in self.items.items():
                    data = {"identifier": identifier,
                            "avg_value": value[0], "min_value": value[1], "max_value": value[2]}
                    cursor = self.conn.cursor()
                    cursor.execute(
                        """INSERT INTO data(identifier, time, avg_value, min_value, max_value)
                        VALUES(:name, datetime('now'), :avg_value, :min_value, :max_value)""", data)
                    self.conn.commit()

            except sqlite3.OperationalError:
                log.error('Erreur la table existe déjà')
            except Exception as err:
                log.error('Error: ' + str(err))
                self.conn.rollback()
            finally:
                self.conn.close()

            self.items = {}
