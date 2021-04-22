import mosaik.util


# Sim config. and other parameters
SIM_CONFIG = {
    'HeatPumpSim': {
        'python': 'Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv_3:CSV',
    },
    'DB': {
        'cmd': 'mosaik-hdf5 %(addr)s'
    },
}

START = '01.01.2016 00:00'
END = 10 * 15 * 60  # 2.5 Hours or 150 mins
HEAT_LOAD_DATA = 'Heatload_R1.csv'
date_format = 'DD.MM.YYYY HH:mm'

# Create World
world = mosaik.World(SIM_CONFIG)

# Start simulators
heatpumpsim = world.start('HeatPumpSim', step_size=15*60)
csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA, date_format=date_format)
# csv = world.start('CSV', step_size=15*60)

params = {'heat_source': 'air',
          'cons_T': 35,
          'heat_source_T': 2,
          'calc_mode': 'detailed',
          }

# Instantiate models
heatpump = heatpumpsim.HeatPump(params=params)
heat_load = csv.HP()

# Connect entities
world.connect(heat_load, heatpump, 'Q_Demand', 'heat_source_T')

# Initializing and instantiating a database component:
db = world.start('DB', step_size=15*60, duration=END)
hdf5 = db.Database(filename='heat_pump_trial_4.hdf5')

world.connect(heatpump, hdf5, 'Q_Demand', 'Q_Supplied', 'heat_source_T', 'P_Required', 'COP')

# Run simulation
world.run(until=END)