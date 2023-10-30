import os
import sys
import mosaik
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

sim_config = {
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        'python': 'mosaik_hdf5:MosaikHdf5'
    },
    'HeatPumpSim': {
        'python': 'mosaik_heatpump.heatpump.Heat_Pump_mosaik:HeatPumpSimulator',
    },
    'HotWaterTankSim': {
        'python': 'mosaik_heatpump.hotwatertanksim.hotwatertank_mosaik:HotWaterTankSimulator',
    },
    'ControllerSim': {
        'python': 'mosaik_heatpump.controller.controller_mosaik:ControllerSimulator',
    },
}

# The start date, duration, and step size for the simulation
END = 3 * 60 * 60
START = '01.01.2020 00:00'
STEP_SIZE = 60 * 1

#Parameters for mosaik-heatpump
params_hp = {'hp_model': 'Air_30kW_1stage',
             'heat_source': 'Air',
             'cons_T': 35,
             'Q_Demand': 19780,
             'cond_in_T': 30,
             'heat_source_T': 7,
             }
#Parameters for hot water tank model
params_hwt = {
    'height': 3600,
    'volume': 4000,
    'T_env': 20.0,
    'htc_walls': 0.28,
    'htc_layers': 0.897,
    'n_layers': 6,
    'n_sensors': 6,
    'connections': {
        'sh_in': {'pos': 10, 'type': 'sh_in'},
        'sh_out': {'pos': 2150, 'type': 'sh_out'},
        'dhw_in': {'pos': 10, 'type': 'dhw_in', 'T_sp': -100},
        'dhw_out': {'pos': 3400, 'type': 'dhw_out'},
        'hp_in': {'pos': 10, 'type': 'hp_in'},
        'hp_out': {'pos': 500, 'type': 'hp_out'},
        },
    }
init_vals_hwt = {
            'layers': {'T': [40, 40, 40, 40, 40, 40]}
        }
#Parameters for controller model
params_ctrl = {
    'T_hp_sp_h': 50,
    'T_hp_sp_l': 40,
    'T_hr_sp_dhw': 40,
    'T_hr_sp_sh': 35,
    'dhw_in_T': 10,
    'sh_dT': 7,
    'operation_mode': 'heating',
    'control_strategy': '1'
}

# The different types of heat pumps and calculation modes that are simulated
model_list = ['Air_30kW_1stage', 'Air_30kW_1stage', 'LW 300(L)', None]
calc_mode_list = ['detailed', 'fast', 'hplib', 'fixed']
filename_list = ['detailed', 'fast', 'hplib', 'fixed']

for i in range(len(model_list)):

    time_at_start = time.time()

    HDF_File = 'Scenario_' + filename_list[i] + '_time_shifted.hdf5'

    world = mosaik.World(sim_config)

    # Initialize the simulators.

    heatpumpsim = world.start('HeatPumpSim', step_size=STEP_SIZE)

    hwtsim = world.start('HotWaterTankSim', step_size=STEP_SIZE, config=params_hwt)

    ctrlsim = world.start('ControllerSim', step_size=STEP_SIZE)

    db = world.start('DB', step_size=STEP_SIZE, duration=END)
    hdf5 = db.Database(filename=HDF_File, buf_size=1440)

    heat_load_file = './data/scenario_data.csv'
    heat_load_sim = world.start('CSV', sim_start=START,
                                        datafile=heat_load_file,
                                        date_format='DD.MM.YYYY hh:mm',
                                        delimiter=',')
    heat_load = heat_load_sim.HEATLOAD.create(1)

    params_hp['calc_mode'] = calc_mode_list[i]
    params_hp['hp_model'] = model_list[i]

    if 'hplib' in params_hp['calc_mode']:
        params_hp['equivalent_hp_model'] = 'Air_30kW_1stage'
    elif 'fixed' in params_hp['calc_mode']:
        params_hp['COP'] = 3.5
        params_hp['heating capacity'] = 15000
        params_hp['cond_m'] = 0.5

    heatpumps = heatpumpsim.HeatPump.create(1, params=params_hp)

    hwts = hwtsim.HotWaterTank.create(1, params=params_hwt, init_vals=init_vals_hwt)

    ctrls = ctrlsim.Controller.create(1, params=params_ctrl)

    # connections between the different models
    world.connect(heat_load[0], ctrls[0], ('T_amb', 'T_amb'), ('T_amb', 'heat_source_T'), ('SH Demand [kW]', 'sh_demand'),
                  ('DHW Demand [L]', 'dhw_demand'), ('dhw_in_T', 'dhw_in_T'))

    world.connect(hwts[0], ctrls[0], ('T_mean', 'T_mean_hwt'), ('mass', 'hwt_mass'),
                  ('sensor_00.T', 'bottom_layer_T'), ('sensor_04.T', 'top_layer_T'),
                  ('dhw_out.T', 'dhw_out_T'), ('sh_out.T', 'sh_out_T'), ('hp_out.T', 'hp_out_T'))

    world.connect(ctrls[0], hwts[0], ('sh_in_F', 'sh_in.F'), ('sh_in_T', 'sh_in.T'), ('sh_out_F', 'sh_out.F'),
                  ('dhw_in_F', 'dhw_in.F'), ('dhw_in_T', 'dhw_in.T'), ('dhw_out_F', 'dhw_out.F'), ('T_amb', 'T_env'),
                  time_shifted=True,
                  initial_data={'sh_in_F': 0, 'sh_in_T': 0, 'sh_out_F': 0,
                                'dhw_in_F': 0, 'dhw_in_T': 0, 'dhw_out_F': 0,
                                'T_amb': 0,
                                },
                  )

    world.connect(heatpumps[0], ctrls[0], ('Q_Supplied', 'hp_supply'), ('on_fraction', 'hp_on_fraction'),
                  ('cond_m', 'hp_cond_m'))

    world.connect(ctrls[0], heatpumps[0], ('hp_demand', 'Q_Demand'),
                  ('T_amb', 'T_amb'), ('heat_source_T', 'heat_source_T'), time_shifted=True,
                  initial_data={'hp_demand': 0, 'T_amb': 5, 'heat_source_T': 5})

    world.connect(hwts[0], heatpumps[0], ('hp_out.T', 'cond_in_T'))

    world.connect(heatpumps[0], hwts[0], ('cons_T', 'hp_in.T'), ('cond_m', 'hp_in.F'), ('cond_m_neg', 'hp_out.F'),
                  time_shifted=True, initial_data={'cons_T': 0, 'cond_m': 0, 'cond_m_neg': 0})

    world.connect(heat_load[0], hdf5, 'T_amb', 'SH Demand [kW]', 'DHW Demand [L]')
    world.connect(heatpumps[0], hdf5, 'Q_Demand', 'Q_Supplied', 'T_amb', 'heat_source_T', 'cons_T', 'P_Required',
                  'COP', 'cond_m', 'cond_in_T', 'on_fraction')

    world.connect(ctrls[0], hdf5, 'heat_demand', 'heat_supply', 'hp_demand', 'sh_supply', 'sh_demand', 'hp_supply',
                  'sh_in_F', 'sh_in_T', 'sh_out_F', 'sh_out_T','dhw_in_F', 'dhw_in_T', 'dhw_out_F', 'dhw_out_T',
                  'hp_in_F', 'hp_in_T', 'hp_out_F', 'hp_out_T',  'P_hr_sh', 'P_hr_dhw', 'dhw_demand', 'dhw_supply')
    world.connect(hwts[0], hdf5, 'sensor_00.T', 'sensor_01.T', 'sensor_02.T','sensor_03.T', 'sensor_04.T', 'sensor_05.T',
                  'sh_out.T', 'sh_out.F', 'dhw_out.T', 'dhw_out.F', 'hp_in.T', 'hp_in.F', 'hp_out.T', 'hp_out.F',
                  'T_mean', 'sh_in.T', 'sh_in.F', 'dhw_in.T', 'dhw_in.F')

    #Run
    world.run(until=END)

    time_at_end = time.time()

    print('The simulation took %s seconds' % (time_at_end - time_at_start))



