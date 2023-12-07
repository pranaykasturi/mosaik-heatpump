import mosaik.util
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

SIM_CONFIG = {
    'HeatPumpSim': {
        'python': 'mosaik_heatpump.heatpump.Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'python': 'mosaik_hdf5:MosaikHdf5'
    },
}

# Create World
world = mosaik.World(SIM_CONFIG)

START = '01.01.2016 00:00'
END = 10 * 15 * 60  # 2.5 Hours or 150 mins

# Heat pump
params = {'calc_mode': 'fast',
          'hp_model': 'Air_8kW',
          'heat_source': 'air',
          }
# configure the simulator
heatpumpsim = world.start('HeatPumpSim', step_size=15*60)
# Instantiate model
heatpump = heatpumpsim.HeatPump(params=params)

# Input data csv
HEAT_LOAD_DATA = './data/heatpump_data.csv'
# configure the simulator
csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA)
# Instantiate model
heat_load = csv.HP()

# Output data storage
# configure the simulator
db = world.start('DB', step_size=15*60, duration=END)
# Instantiate model
hdf5 = db.Database(filename='hp_trial_1.hdf5')

# Connect entities
world.connect(heat_load, heatpump, ('Q_Demand','Q_Demand'), ('heat_source_T','heat_source_T'),
              ('heat_source_T','T_amb'), ('cond_in_T','cond_in_T'))
world.connect(heatpump, hdf5, 'Q_Demand', 'Q_Supplied', 'heat_source_T', 'P_Required', 'COP')

# Run simulation
world.run(until=END)
