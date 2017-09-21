"""Contrôleur cherchant à obtenir la puissance max"""
import time
import math

class CONTROLEUR:
    """Contrôleur cherchant à obtenir la puissance max"""

    def __init__(self, GPT = 0.0, GPU = 0.0, GPD = 0.0):
        self.gap_power_to_test = GPT
        self.gain_power_up = GPU 
        self.gain_power_down = GPD

        self.current_time = time.time() # en seconde
        self.last_time = self.current_time

        self.clear() # Effacer les variables

    def clear(self):
        """Efface les variables du contrôlleur"""
        self.power_current = 0.0
        self.power_tested = 0.0
        self.power_last = 0.0

        self.sample_time = 0.00 # en ms

        self.torque_setpoint = 0.0 # en Nm

        self.torque_voltage = 0.0
        self.angular_velocity = 0.0

    def update(self, value):
        """Calcul le nouveau couple (Nm) nécessaire en fonction de la vitesse angulaire (rad/s)
        """
        self.current_time = time.time()
        delta_time = self.current_time - self.last_time

        if (delta_time >= self.sample_time):
            # Calculer la puissance actuelle 
            self.power_current = self.torque_setpoint * value
            # Calculer la puissance réelle (équation caractérisant la turbine)
            power_real = 1.2 * math.exp(0.45 * value) * value
            # Déterminer la différence
            power_gap = power_real - self.power_current
            # Tester si la puissance actuelle augmentée est plus grande que la puissance précédente
            if self.power_current + self.gap_power_to_test >= self.power_last: 
                # Calculer la puissance augmentée à tester avec un gain_up
                self.power_tested = self.power_current + (power_gap * self.gain_power_up)
            else:
                # Calculer la puissance diminuée à tester avec un gain_down
                self.power_tested = self.power_current + (power_gap * self.gain_power_down)
            # Limiter la puissance à zéro si vitesse angulaire inférieure à
            if value < 0.7:
                self.power_tested = 0
            # Limiter la puissance à tester à 0 si elle est négative
            if self.power_tested < 0: 
                self.power_tested = 0
            # Limiter le couple à zéro si vitesse angulaire est nul ou négative
            if value <= 0: 
                self.torque_setpoint = 0
            else:
                # Calculer le couple à tester
                self.torque_setpoint = self.power_tested / value
            # Mémoriser la puissance pour le prochain calcul
            self.power_last = self.power_current

    def set_gap_power_to_test(self, value):
        """Définir la valeur à augmenter la puissance actuelle
        """
        self.gap_power_to_test = value

    def set_gain_power_up(self, value):
        """Définir le gain pour augmenter la puissance
        """
        self.gain_power_up = value

    def set_gain_power_down(self, value):
        """Définir le gain pour diminuer la puissance
        """
        self.gain_power_down = value

    def setSampleTime(self, sample_time):
        """Définir la période de calcul: sample_time en milliseconde (ms)
        """
        self.sample_time = sample_time

    def to_angular_velocity(self, value):
        """Transforme le nombre d'impulsion en une vitesse angulaire (rad/s).
        Résultat : angular_velocity
        Faire la calibration pour la conversion.
        """
        result = value
        self.angular_velocity = result

    def torque_to_voltage(self, value):
        """Transforme le couple en une tension.
        Résultat : torque_voltage
        Faire la calibration pour la conversion.
        """
        result = value
        self.torque_voltage = result


