import mosaik.util
import os

SIM_CONFIG = {
    'HeatPumpSim': {
        'python': 'mosaik_components.heatpump.Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'CSV_writer': {
        'python': 'mosaik_csv_writer:CSVWriter'
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
HEAT_LOAD_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'heatpump_data.csv')
# configure the simulator
csv = world.start('CSV', sim_start=START, datafile=HEAT_LOAD_DATA)
# Instantiate model
heat_load = csv.HP()

# Output data storage
# configure the simulator
csv_sim_writer = world.start('CSV_writer', start_date='01.01.2020 00:00', date_format='%d.%m.%Y %H:%M',
                             output_file='hp_trial.csv')
# Instantiate model
csv_writer = csv_sim_writer.CSVWriter(buff_size=60 * 60)

# Connect entities
world.connect(heat_load, heatpump, 'Q_Demand', 'heat_source_T', ('heat_source_T', 'T_amb'), 'cond_in_T')
world.connect(heatpump, csv_writer, 'Q_Demand', 'Q_Supplied', 'heat_source_T', 'P_Required', 'COP')

# Run simulation
world.run(until=END)
