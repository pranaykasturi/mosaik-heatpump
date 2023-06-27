import os
import sys
# sys.path.append("D:\\PPRE\\4th Sem\\Code\\pranaysthesis\\mosaik-heatpump")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# print(sys.path)
import mosaik
import time
#import visualizationResults
import numpy as np
import pandas as pd

# from postprocessing_mhp_hwt import do_postprocessing

sim_config = {
    'CSV': {
        'python': 'mosaik_csv:CSV',
    },
    'DB': {
        # 'cmd': 'mosaik-hdf5 %(addr)s'
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
#
END = 10 * 60 #+ 60 # one day in seconds
START = '01.01.2020 06:00'  # The date in the CSV is wrong! 18.03 is the data of the 19.03.!
STEP_SIZE = 60 * 1

#Parameters for mosaik-heatpump
# params_hp = {'hp_model': 'LW 300(L)',
params_hp = {'hp_model': 'Air_30kW_1stage',
             'heat_source': 'Air',
             'cons_T': 35,
             'Q_Demand': 35200,
             'cond_in_T': 30,
             'heat_source_T': 7,
             'calc_mode': 'fast',
             # 'calc_mode': 'hplib',
             }

params_hwt = {
    'height': 1350,
    'volume': 1000,
    'T_env': 20.0,
    # 'htc_walls': 0,
    'htc_walls': 0.28,
    'htc_layers': 0.897,
    'n_layers': 6,
    'n_sensors': 6,
    'connections': {
        'sh_in': {'pos': 100, 'type': 'sh_in'},
        'sh_out': {'pos': 1200, 'type': 'sh_out'},
        'dhw_in': {'pos': 100, 'type': 'dhw_in', 'T_sp': 0},
        'dhw_out': {'pos': 1200, 'type': 'dhw_out'},
        'hp_in': {'pos': 1100, 'type': 'hp_in'},
        'hp_out': {'pos': 200, 'type': 'hp_out'},
        },
    # 'heating_rods': {
    #     'hr_1': {
    #         'pos': 100,
    #         'P_th_stages': [0, 50, 100, 200, 300],
    #         'T_max': 60,
    #         'eta': 0.98,
    #         }
    #      },
    }
init_vals_hwt = {
            # 'layers': {'T': [46.55]}
            'layers': {'T': [40.0, 40.0, 40.0, 40.0, 40.0, 40.0]}
            # 'layers': {'T': [25, 25, 25, 25, 25, 25]}
        }

params_ctrl = {
    'T_hp_sp_h': 50,
    'T_hp_sp_l': 40,
    # 'T_hr_sp': 30,
    'T_hr_sp_dhw': 40,
    'T_hr_sp_sh': 35,
    'dhw_in_T': 10,
    'sh_dT': 7,
    'operation_mode': 'heating',
    'control_strategy': '1',
}

sf = 1 # scaling factor for results

# model_list = ['Air_30kW', 'Air_30kW_1stage', 'LW 300(L)']
model_list = ['Air_30kW']
# calc_mode_list = ['fast', 'fast', 'hplib']
calc_mode_list = ['fast']
# filename_list = ['tespy', 'tespy_1stage', 'hplib']
filename_list = ['fast']

for i in range(len(model_list)):

    time_at_start = time.time()

    HDF_File = 'Scenario_' + filename_list[i] + '_same_time_loop_test_5.hdf5'
    # HDF_File = './hdf_files/Scenario_' + filename_list[i] + '.hdf5'

    world = mosaik.World(sim_config, debug=True)

    # Initialize the simulators.

    heatpumpsim = world.start('HeatPumpSim', step_size=STEP_SIZE, same_time_loop=True)

    hwtsim = world.start('HotWaterTankSim', step_size=STEP_SIZE, config=params_hwt, same_time_loop=True)

    ctrlsim = world.start('ControllerSim', step_size=STEP_SIZE, same_time_loop=True)

    db = world.start('DB', step_size=STEP_SIZE, duration=END)
    hdf5 = db.Database(filename=HDF_File, buf_size=1440)
    # hdf5 = db.Database(filename=HDF_File)

    heat_load_file = './InputData_R2.csv'
    heat_load_sim = world.start('CSV', sim_start=START,
                                        datafile=heat_load_file,
                                        date_format='DD.MM.YYYY hh:mm',
                                        delimiter=',')
    heat_load = heat_load_sim.HEATLOAD.create(1)

    heater_p_mw = 5

    hwt_volume = 4000

    hwt_height = ((hwt_volume * 1e6) * (6**2) / np.pi) ** (1/3)  # H:D ratio of 3:1 was used to calculate height from volume

    params_hp['calc_mode'] = calc_mode_list[i]
    params_hp['hp_model'] = model_list[i]
    heatpumps = heatpumpsim.HeatPump.create(1, params=params_hp)

    # params_hwt['heating_rods']['hr_1']['P_th_stages'] = np.linspace(0, (float(heater_p_mw)*1000), num=5)
    params_hwt['volume'] = hwt_volume
    params_hwt['height'] = round(hwt_height, 0)
    params_hwt['connections']['hp_out']['pos'] = round(0.15 * hwt_height, 0)
    params_hwt['connections']['hp_in']['pos'] = round(0.01 * hwt_height, 0)
    params_hwt['connections']['sh_in']['pos'] = round(0.01 * hwt_height, 0)
    params_hwt['connections']['sh_out']['pos'] = round(0.6 * hwt_height, 0)
    params_hwt['connections']['dhw_in']['pos'] = round(0.01 * hwt_height, 0)
    params_hwt['connections']['dhw_out']['pos'] = round(0.95 * hwt_height, 0)


    hwts = hwtsim.HotWaterTank.create(1, params=params_hwt, init_vals=init_vals_hwt)

    ctrls = ctrlsim.Controller.create(1, params=params_ctrl)

    world.connect(heat_load[0], ctrls[0], ('T_amb', 'T_amb'), ('T_amb', 'heat_source_T'), ('SH Demand [kW]', 'sh_demand'),
                  ('DHW Demand [L]', 'dhw_demand'), ('dhw_in_T', 'dhw_in_T'))

    # world.connect(hwts[0], ctrls[0], ('snapshot', 'hwt_connections'), ('T_mean', 'T_mean'), ('mass', 'hwt_mass'),)
                  # weak=True,)
                  # initial_data= {'snapshot': None, 'T_mean': 20, 'mass': 4000})

    world.connect(hwts[0], ctrls[0], ('T_mean', 'T_mean'), ('mass', 'hwt_mass'),
                  ('sensor_00.T', 'bottom_layer_T'), ('sensor_04.T', 'top_layer_T'),
                  ('dhw_out.T', 'dhw_out_T'), ('sh_out.T', 'sh_out_T'),
                  ('hp_out.T', 'hp_out_T'))  # , ('snapshot', 'hwt_connections')

    world.connect(ctrls[0], hwts[0], ('sh_in_F', 'sh_in.F'), ('sh_in_T', 'sh_in.T'), ('sh_out_F', 'sh_out.F'),
                  ('dhw_in_F', 'dhw_in.F'), ('dhw_in_T', 'dhw_in.T'), ('dhw_out_F', 'dhw_out.F'), ('T_amb_hwt', 'T_env'),
                  ('hp_in_T', 'hp_in.T'), ('hp_in_F', 'hp_in.F'), ('hp_out_F', 'hp_out.F'),
                  # time_shifted=True,
                  weak=True,
                  #
                  # initial_data={'sh_in_F': 0, 'sh_in_T': 0, 'sh_out_F': 0,
                  #               'dhw_in_F': 0, 'dhw_in_T': 0, 'dhw_out_F': 0,
                  #               'T_amb': 0, 'hp_in_T': 0, 'hp_in_F': 0, 'hp_out_F': 0
                  #               # 'hwt_hr_P_th_set': 0,
                  #               },
                  )

    world.connect(heatpumps[0], ctrls[0], ('Q_Supplied', 'hp_supply'), ('on_fraction', 'hp_on_fraction'),
                  ('cond_m', 'hp_in_F'), ('cond_m_neg', 'hp_out_F'), ('cons_T', 'hp_in_T'),
                  ('step_executed', 'execute_step'), weak=True,)
                  # initial_data={'Q_Supplied': 0, 'on_fraction': 0, 'cond_m': 0, 'cons_T': 0})

    world.connect(ctrls[0], heatpumps[0], ('hp_demand', 'Q_Demand'), ('hp_out_T', 'cond_in_T'),
                  ('T_amb', 'T_amb'), ('heat_source_T', 'heat_source_T'))


    world.connect(heat_load[0], hdf5, 'T_amb', 'SH Demand [kW]', 'DHW Demand [L]')
    world.connect(heatpumps[0], hdf5, 'Q_Demand', 'Q_Supplied', 'T_amb', 'heat_source_T', 'heat_source',
                  'cons_T', 'P_Required', 'COP', 'cond_m', 'cond_in_T', 'on_fraction')

    world.connect(ctrls[0], hdf5, 'heat_demand', 'heat_supply', 'hp_demand', 'sh_supply', 'sh_demand', 'hp_supply',
                  'sh_in_F', 'sh_in_T', 'sh_out_F', 'sh_out_T','dhw_in_F', 'dhw_in_T', 'dhw_out_F', 'dhw_out_T',
                  # 'hp_in_F', 'hp_in_T', 'hp_out_F', 'hp_out_T',  'hwt_hr_P_th_set', 'dhw_demand', 'dhw_supply')
                  'hp_in_F', 'hp_in_T', 'hp_out_F', 'hp_out_T',  'P_hr_sh', 'P_hr_dhw', 'dhw_demand', 'dhw_supply')
    world.connect(hwts[0], hdf5, 'sensor_00.T', 'sensor_01.T', 'sensor_02.T','sensor_03.T', 'sensor_04.T', 'sensor_05.T',
                  'sh_out.T', 'sh_out.F', 'dhw_out.T', 'dhw_out.F', 'hp_in.T', 'hp_in.F', 'hp_out.T', 'hp_out.F',
                  'T_mean', 'sh_in.T', 'sh_in.F', 'dhw_in.T', 'dhw_in.F')
                  # 'hr_1.P_th_set', 'hr_1.P_el', 'hr_1.P_th', 'T_mean', 'sh_in.T', 'sh_in.F', 'dhw_in.T', 'dhw_in.F')

    # world.connect(bus[0], hdf5, 'vm_pu')

    # To start hwts as first simulator
    world.set_initial_event(hwts[0].sid)

    #Run
    world.run(until=END)

    # eg = world.execution_graph
    # import execution_graph_tools
    # execution_graph_tools.plot_execution_graph(world)
    # execution_graph_tools.plot_execution_graph_new(world)
    # execution_graph_tools.plot_execution_time(world)
    # execution_graph_tools.plot_df_graph(world)

    time_at_end = time.time()

    print('The simulation took %s seconds' % (time_at_end - time_at_start))

    time_at_start = time.time()
    #
    # do_postprocessing(HDF_File, step_size=(STEP_SIZE/60))
    #
    # time_at_end = time.time()
    #
    # print('The post-processing took %s seconds' % (time_at_end - time_at_start))
    #
    # time_at_start = time.time()
    #
    # csv_filename_base = HDF_File.split('.')[1].split('/')[2]
    # # csv_filename_base = 'Scenario_' + filename_list[i] + '_R3'
    # csv_filename = './postprocessing_csv/' + csv_filename_base + '.csv'
    #
    # usecols = ['time', 'Tamb', 'Pel,HP', 'P_HR_sh', 'P_HR_dhw', 'T_mean', 'Temp_layer_0', 'Temp_layer_1',
    #            'Temp_layer_2', 'Temp_layer_3', 'Temp_layer_4', 'Temp_layer_5',
    #            'heat_supply', 'hp_supply', 'hp_demand', 'sh_supply', 'dhw_supply']
    #
    # df = pd.read_csv(csv_filename, index_col=['time'], usecols=usecols)
    #
    # df.index = pd.date_range(start="2020-01-01 00:00:00", periods=len(df.index), freq="1Min")
    # df.index.name = 'Time'
    #
    # # func_dict = {'T_mean': 'last', 'Temp_layer_0': 'last', 'Temp_layer_1': 'last', 'Temp_layer_2': 'last',
    # #              'Temp_layer_3': 'last', 'Temp_layer_4': 'last', 'Temp_layer_5': 'last', 'hp_supply': 'mean',
    # #              'hp_demand': 'mean', 'sh_supply': 'mean', 'dhw_supply': 'mean', 'heat_supply': 'mean', }
    #
    # # df = df.resample('1D', label='left').agg(func_dict)
    # replace_cols = ['Pel,HP', 'heat_supply', 'hp_demand', 'sh_supply', 'dhw_supply', 'hp_supply']
    # replace_dict = {}
    # for col_name in replace_cols:
    #     replace_dict[col_name] = {0: np.nan}
    # df.replace(replace_dict, inplace=True)
    # df = df.resample('1D', label='left').mean()
    #
    # csv_filename = './Results/' + csv_filename_base + '_1Day.csv'
    #
    # df.to_csv(csv_filename)
    #
    # time_at_end = time.time()
    #
    # print('The step size conversion took %s seconds' % (time_at_end - time_at_start))
