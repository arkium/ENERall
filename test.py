import CONTROLEUR as PID
import time
import matplotlib.pyplot as plt

def test_controleur(GPT = 0.01,  GPU = 0.5, GPD = 0.16, L=400):
    ctrl = PID.CONTROLEUR(GPT, GPU, GPD)
    ctrl.setSampleTime(0.0)

    time_list = []
    rotation_list = []
    rotation_free_list = []
    torque_list = []
    power_list = []
    power_tested_list = []

    time_list.append(0)
    rotation_free_list.append(0)
    rotation_list.append(0)
    torque_list.append(ctrl.torque_setpoint)
    power_list.append(ctrl.power_current)
    power_tested_list.append(ctrl.power_tested)

    END = L
    rot_ini = 0
    rotation = 0
    for i in range(1, END):
        ctrl.update(rotation)
        if rotation > -1:
            rotation = rot_ini - (ctrl.torque_setpoint * 0.3)
            if rotation < 0:
                rotation = 0
        if i>0 and i<80:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 2:
                rot_ini = 2
        if i>80 and i<150:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 6:
                rot_ini = 6
        if i>150 and i<225:
            rot_ini = rot_ini - (1 * 0.2)
            if rot_ini < 2:
                rot_ini = 2
        if i>225 and i<300:
            rot_ini = rot_ini + (1 * 0.2)
            if rot_ini > 10:
                rot_ini = 10
        if i>300 and i<400:
            rot_ini = rot_ini - (1 * 0.2)
            if rot_ini < 2:
                rot_ini = 2
        time.sleep(0.02)

        time_list.append(i)
        rotation_list.append(rotation)
        rotation_free_list.append(rot_ini)
        torque_list.append(ctrl.torque_setpoint)
        power_list.append(ctrl.power_current)
        power_tested_list.append(ctrl.power_tested)

    plt.plot(time_list, rotation_list, label='Rot Turbine (rad/s)')
    plt.plot(time_list, torque_list, label='Couple Turbine (Nm)')
    plt.plot(time_list, power_list, label='P actuelle (Watt)')
    plt.plot(time_list, power_tested_list, label='P à tester (Watt)')
    plt.plot(time_list, rotation_free_list, '--', label='Rot sans couple (rad/s)')
    plt.legend()
    plt.xlim((-2, L))
    plt.ylim((-5, 90))
    plt.xlabel('Cycle')
    plt.title('TEST CONTROLEUR')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    test_controleur(0.01, 0.5, 0.1, L = 400)