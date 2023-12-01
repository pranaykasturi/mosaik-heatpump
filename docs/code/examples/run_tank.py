import mosaik
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

SIM_CONFIG = {
    'HotWaterTankSim': {
        'python': 'mosaik_heatpump.hotwatertanksim.hotwatertank_mosaik:HotWaterTankSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'python': 'mosaik_hdf5:MosaikHdf5'
    },
}

world = mosaik.World(SIM_CONFIG)

START = '01.01.2016 00:00'
END = 7 * 15 * 60

# Hot water tank
params = {
    'height': 2100,
    'diameter': 1200,
    'T_env': 20.0,
    'htc_walls': 0.28,
    'htc_layers': 0.897,
    'n_layers': 3,
    'n_sensors': 3,
    'connections': {
        'cc_in': {'pos': 1500},
        'cc_out': {'pos': 10},
        }
    }
init_vals = {
            'layers': {'T': [30, 50, 70]}
        }
# configure the simulator
hwtsim = world.start('HotWaterTankSim', step_size=15*60, config=params)
# Instantiate model
hwt = hwtsim.HotWaterTank(params=params, init_vals=init_vals)

# Input data csv
HWT_FLOW_DATA = './data/tank_data.csv'
# configure the simulator
csv = world.start('CSV', sim_start=START, datafile=HWT_FLOW_DATA)
# Instantiate model
csv_data = csv.HWT()

# Output data storage
# configure the simulator
db = world.start('DB', step_size=15*60, duration=END)
# Instantiate model
hdf5 = db.Database(filename='hwt_trial_1.hdf5')

# Connect entities
world.connect(csv_data, hwt, ('T_in', 'cc_in.T'), ('F_in', 'cc_in.F'), ('F_out', 'cc_out.F'))
world.connect(hwt, hdf5, 'cc_in.T', 'cc_in.F', 'cc_out.T', 'cc_out.F', 'sensor_00.T', 'sensor_01.T', 'sensor_02.T')

# Run the simulation
world.run(until=END)  # As fast as possilbe
