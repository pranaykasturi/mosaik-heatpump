import mosaik
import mosaik.util


# Sim config. and other parameters
SIM_CONFIG = {
    'HeatPumpSim': {
        'python': 'Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'cmd': 'mosaik-hdf5 %(addr)s'
    },
}

START = '2016-01-01 00:00:00'
END = 10 * 15 * 60  # 2.5 Hours or 150 mins
HEAT_LOAD_DATA = 'Heatload3.csv'
date_format = 'DD.MM.YYYY HH:mm'

# Create World
world = mosaik.World(SIM_CONFIG)

# Start simulators
heatpumpsim = world.start('HeatPumpSim', step_size=15*60)
csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA)
# csv = world.start('CSV', step_size=15*60)

params = {'heat_source': 'Water',
          'cons_T': 35,
          'heat_source_T': 5,
          'amb_T': 15
          }

# Instantiate models
heatpump = heatpumpsim.HeatPump(params=params)
heat_load = csv.HP()

# Connect entities
world.connect(heat_load, heatpump, 'cons_Q', 'amb_T')

# Initializing and instantiating a database component:
db = world.start('DB', step_size=15*60, duration=END)
hdf5 = db.Database(filename='heat_pump_newcsv.hdf5')

world.connect(heatpump, hdf5, 'cons_Q', 'amb_T', 'p_kw', 'COP')

# Run simulation
world.run(until=END)