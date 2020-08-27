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

# Create World
world = mosaik.World(SIM_CONFIG)

# Start simulators
heatpumpsim = world.start('HeatPumpSim', step_size=15*60)
csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA)
# csv = world.start('CSV', step_size=15*60)

params = {'cd_cons_temp': 90,
          'cb_dhp_temp': 60,
          'amb_p_temp': 12,
          'amb_p_pres': 2,
          'ev_amb_out_temp': 9,
          'ev_amb_out_pres': 2,
          'cons_Q': 500000,
          'ic_out_temp': 30
          }

# Instantiate models
heatpump = heatpumpsim.HeatPump(params=params)
heat_load = csv.HP.create(1)[0]

# Connect entities
world.connect(heat_load, heatpump, 'cons_Q')

# Initializing and instantiating a database component:
db = world.start('DB', step_size=15*60, duration=END)
hdf5 = db.Database(filename='heat_pump_trial_mosaikcsv.hdf5')

world.connect(heatpump, hdf5, 'cons_Q', 'amb_T', 'p_kw', 'COP')

# Run simulation
world.run(until=END)