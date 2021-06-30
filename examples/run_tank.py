import mosaik
import inspect


import sys
import os


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

START = '01.01.2016 00:00'
# END =  24 * 3600  # 1 day
END = 7 * 15 * 60
HEAT_LOAD_DATA = 'data.csv'
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

world = mosaik.World(SIM_CONFIG)

# configure the simulators
hwtsim = world.start('HotWaterTankSim', step_size=15*60, config=params)

# heatpumpsim = world.start('HeatPumpSim', step_size=15*60)

csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA, date_format=date_format)


init_vals = {
            'layers': {'T': [30, 50, 70]}
        }

# Instantiate models
hwt = hwtsim.HotWaterTank(params=params, init_vals=init_vals)
csv_data = csv.HWT()

# Connect entities
# world.connect(csv_data, hwt, ('T_in', 'cc_in.T'), ('F_in', 'cc_in.F'), ('T_out',  'cc_out.T'), ('F_out', 'cc_out.F'))
world.connect(csv_data, hwt, ('T_in', 'cc_in.T'), ('F_in', 'cc_in.F'), ('F_out', 'cc_out.F'))


# storage
db = world.start('DB', step_size=15*60, duration=END)
hdf5 = db.Database(filename='hwt_trial_4.hdf5')
world.connect(hwt, hdf5, 'cc_in.T', 'cc_in.F', 'cc_out.T', 'cc_out.F', 'sensor_00.T', 'sensor_01.T', 'sensor_02.T')

world.run(until=END)  # As fast as possilbe
