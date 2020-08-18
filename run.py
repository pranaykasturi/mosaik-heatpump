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
}
END = 366 * 15 * 60  # 366 days

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

params1 = {'filename': 'HeatLoad.csv'}

# Instantiate models
heatpump = heatpumpsim.HeatPump(params=params)
csvfile = csv.CSVSchedule(params=params1)

# Connect entities
world.connect(csvfile, heatpump, 'cons_Q')

# Run simulation
world.run(until=END)