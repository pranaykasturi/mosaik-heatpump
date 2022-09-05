import mosaik
import inspect
import sys
sys.path.append("D:\\PPRE\\4th Sem\\Code\\pranaysthesis\\mosaik-heatpump")
import os
import numpy as np


SIM_CONFIG = {
    'HotWaterTankSim': {
        'python': 'mosaik_heatpump.hotwatertanksim.hotwatertank_mosaik:HotWaterTankSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'cmd': 'mosaik-hdf5 %(addr)s'
    },
}

START = '01.01.2016 00:01'
# END =  24 * 3600  # 1 day
END = 2*60
HEAT_LOAD_DATA = './data/data1.csv'
date_format = 'DD.MM.YYYY HH:mm'

params = {
    'height': 2100,
    'diameter': 1200,
    'T_env': 20.0,
    'htc_walls': 1.0,
    'htc_layers': 20,
    'n_layers': 3,
    'n_sensors': 3,
    'connections': {
        'cc_in': {'pos': 1500},
        'cc_out': {'pos': 10},
        }
    }

params_hwt = {
    'height': 1350,
    'volume': 1000,
    'T_env': 20.0,
    # 'htc_walls': 0,
    'htc_walls': 0.28,
    'htc_layers': 0.897,
    'n_layers': 6,
    'n_sensors': 6,
    'connections': {
        # 'sh_in': {'pos': 100, 'type': 'sh_in'},
        # 'sh_out': {'pos': 1200, 'type': 'sh_out'},
        'dhw_in': {'pos': 100, 'type': 'dhw_in', 'T_sp': -100},
        'dhw_out': {'pos': 1200, 'type': 'dhw_out'},
        # 'hp_in': {'pos': 1100, 'type': 'hp_in'},
        # 'hp_out': {'pos': 200, 'type': 'hp_out'},
        },
    # 'heating_rods': {
    #     'hr_1': {
    #         'pos': 100,
    #         'P_th_stages': [0, 50, 100, 200, 300],
    #         'T_max': 60,
    #         'eta': 0.98,
    #         }
    #      },
    }
init_vals_hwt = {
            # 'layers': {'T': [46.55]}
            'layers': {'T': [6.00338333940604, 6.0290619571119, 6.16434553392362, 24.5869170508085, 27.7542715962686, 27.7932842859967]}
            # 'layers': {'T': [25, 25, 25, 25, 25, 25]}
        }

hwt_volume = 4000

hwt_height = ((hwt_volume * 1e6) * (6**2) / np.pi) ** (1/3)  # H:D ratio of 3:1 was used to calculate height from volume

# params_hwt['heating_rods']['hr_1']['P_th_stages'] = np.linspace(0, (float(heater_p_mw)*1000), num=5)
params_hwt['volume'] = hwt_volume
params_hwt['height'] = round(hwt_height, 0)
params_hwt['connections']['dhw_in']['pos'] = round(0.01 * hwt_height, 0)
params_hwt['connections']['dhw_out']['pos'] = round(0.95 * hwt_height, 0)

world = mosaik.World(SIM_CONFIG)

# configure the simulators
hwtsim = world.start('HotWaterTankSim', step_size=60, config=params_hwt)

# heatpumpsim = world.start('HeatPumpSim', step_size=15*60)

csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA, date_format=date_format, delimiter=',')


init_vals = {
            'layers': {'T': [30, 50, 70]}
        }

# Instantiate models
hwt = hwtsim.HotWaterTank(params=params_hwt, init_vals=init_vals_hwt)
csv_data = csv.HWT()

# Connect entities
# world.connect(csv_data, hwt, ('T_in', 'cc_in.T'), ('F_in', 'cc_in.F'), ('T_out',  'cc_out.T'), ('F_out', 'cc_out.F'))
world.connect(csv_data, hwt, ('T_in', 'dhw_in.T'), ('F_in', 'dhw_in.F'), ('F_out', 'dhw_out.F'), ('T_amb', 'T_env'))


# # storage
# db = world.start('DB', step_size=15*60, duration=END)
# hdf5 = db.Database(filename='hwt_trial_5.hdf5')
# world.connect(hwt, hdf5, 'cc_in.T', 'cc_in.F', 'cc_out.T', 'cc_out.F', 'sensor_00.T', 'sensor_01.T', 'sensor_02.T')

world.run(until=END)  # As fast as possilbe
