import mosaik
import mosaik.util


# Sim config. and other parameters
SIM_CONFIG = {
    'HeatPumpSim': {
        'python': 'Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'CSV': {
        'python': 'csvschedule_mosaik:CSVScheduleSimulator',
    },
    'DB': {
        'cmd': 'mosaik-hdf5 %(addr)s'
    },
}
END = 50 * 15 * 60  # 12.5 Hours or 750 mins

# Create World
world = mosaik.World(SIM_CONFIG)

# Start simulators
heatpumpsim = world.start('HeatPumpSim', step_size=15*60)
csv = world.start('CSV', step_size=15*60)

params = {'cd_cons_temp': 90,
          'cb_dhp_temp': 60,
          'amb_p_temp': 12,
          'amb_p_pres': 2,
          'ev_amb_out_temp': 9,
          'ev_amb_out_pres': 2,
          'cons_Q': 500000,
          'ic_out_temp': 30
          }

params1 = {'filename': 'HeatLoad1.csv'}

# Instantiate models
heatpump = heatpumpsim.HeatPump(params=params)
csvfile = csv.CSVSchedule(params=params1)

# Connect entities
world.connect(csvfile, heatpump, 'cons_Q')

# Initializing and instantiating a database component:
db = world.start('DB', step_size=15*60, duration=END)
hdf5 = db.Database(filename='heat_pump_trial.hdf5')

world.connect(heatpump, hdf5, 'cons_Q', 'amb_T', 'p_kw', 'COP')

# Run simulation
world.run(until=END)