from mosaik_heatpump.hotwatertanksim.hotwatertank import HotWaterTank
import numpy as np
import jsonpickle
import pytest

@pytest.fixture
def hwt_init_vals():
    init_vals = {
        'layers':{
            'T': [30, 50, 70]
        },
        'hr': {
            'P_el': 0
        }
    }
    return init_vals

@pytest.fixture
def hwt_params():
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'T_init': [30, 50, 70],
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
            }
        }
    return hwt_params

def test_get_nested_attrs(hwt_params, hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    print(hwt.sensors['sensor_00'].T)
    print(hwt.get_nested_attr('sensor_00.T'))



#This test is currently not working, due to changes in the model
#def test_snapshot(hwt_params, hwt_init_vals):
#    hwt = HotWaterTank(hwt_params, hwt_init_vals)
#    copy = jsonpickle.decode(hwt.snapshot)
#    
#    hwt.connections['gcb_in'].F = 0.1
#    hwt.connections['gcb_out'].F = -0.1
#    hwt.connections['gcb_in'].T = 80
#    hwt.step(5*60)
#
#    copy.connections['gcb_in'].F = 0.1
#    copy.connections['gcb_out'].F = -0.1
#    copy.connections['gcb_in'].T = 80
#    copy.step(5*60)
#
#    assert hwt.sensors['sensor_02'].T == copy.sensors['sensor_02'].T

def test_step_flow_too_high():

    hwt_init_vals = {
        'layers': {
            'T': 60
        }
    }

    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 30,  # model more layers
        'T_init': 60,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
            }
        }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    for i in range(100):
        hwt.connections['gcb_in'].F = 0.6
        hwt.connections['gcb_out'].F = -0.6
        hwt.connections['gcb_in'].T = 80
        hwt.step(5*60)
    assert hwt.connections['gcb_out'].T == 79.81175198706227

def test_step_loading(hwt_init_vals):
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 0.0,
        'htc_layers': 0.0,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'gcb_in': {'pos': 2000},
            'gcb_out': {'pos': 100}
            }
        }

    step_size = 5 * 60
    c_w = 4180

    T_in = 80 
    f_in = 0.2  # l/s
    f_out = -0.2  # l/s

    V_ges = (np.pi * (hwt_params['diameter'] / 1e3 / 2)**2 
            * hwt_params['height'] / 1e3) * 1000  # l
    V_layer = V_ges / hwt_params['n_layers']

    # calculate temperature of uppermost layer after one step
    E_in = f_in * step_size * c_w * T_in
    E_out = f_out * step_size * c_w * hwt_init_vals['layers']['T'][2]
    T_layer_2_target = hwt_init_vals['layers']['T'][2] + (E_in + E_out) / (V_layer*c_w)

    # calculate temperature of undermost layer after one step
    E_in = f_in * step_size * c_w * hwt_init_vals['layers']['T'][1]
    E_out = f_out * step_size * c_w * hwt_init_vals['layers']['T'][0]
    T_layer_0_target = hwt_init_vals['layers']['T'][0] + (E_in + E_out) / (V_layer*c_w)

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    hwt.connections['gcb_in'].F = f_in
    hwt.connections['gcb_out'].F = f_out
    hwt.connections['gcb_in'].T = T_in
    hwt.step(step_size)

    assert abs(hwt.layers[2].T - T_layer_2_target) < 1e-5
    assert abs(hwt.layers[0].T - T_layer_0_target) < 1e-5


def test_step_if_input_connection_temperature_is_not_set(hwt_params,
        hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    # set flow 
    hwt.connections['cc_in'].F = 0.1
    hwt.connections['cc_out'].F = -0.1
    
    with pytest.raises(ValueError):
        hwt.step(60)


def test_step_if_input_and_outputs_flows_dont_equal_zero(hwt_params,
        hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    # check corresponding layer after flows and input temperatures are set
    hwt.connections['cc_in'].T = 50
    hwt.connections['cc_in'].F = 0.1
    hwt.connections['cc_out'].F = -0.5
    with pytest.raises(ValueError) as excinfo:
        hwt.step(60)

    assert "Sum of inputs and output flows" in str(excinfo.value)


def test_step_standing_losses():
    hwt_init_vals = {
        'layers': {
            'T': 60
            }
    }

    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
            }
        }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)

    step_size = 60*60 

    O_side = np.pi * hwt_params['diameter'] / 1e3 * hwt_params['height'] / 1e3
    O_top = np.pi * (hwt_params['diameter'] / 1e3 / 2)**2
    O_ges = O_side + 2 * O_top  # m2

    V_ges = (np.pi * (hwt_params['diameter'] / 1e3 / 2)**2 
            * hwt_params['height'] / 1e3) * 1000  # l
    
    E = O_ges * hwt_params['htc_walls'] * (hwt_init_vals['layers']['T']
            - hwt_params['T_env']) * step_size  # J
    
    c_w = 4180  # J/(kg/K)
    rho = 1  # kg/l

    delta_T_target = E / (V_ges * rho * c_w)  # K
    hwt.step(step_size)
    delta_T = hwt_init_vals['layers']['T'] - sum([layer.T for layer in hwt.layers]) / 3

    assert (delta_T - delta_T_target) < 1e-8


def test_step_input_and_outputs_flows_dont_equal_zero(hwt_params,
        hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    # check corresponding layer after flows and input temperatures are set
    hwt.connections['cc_in'].T = 50
    hwt.connections['cc_in'].F = 0.1
    hwt.connections['cc_out'].F = -0.5
    with pytest.raises(ValueError) as excinfo:
        hwt.step(60)

    assert "Sum of inputs and output flows" in str(excinfo.value)


def test_init_corresponding_layers(hwt_params, hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert (hwt.connections['cc_in'].corresponding_layer ==
            hwt.layers[0])
    assert (hwt.connections['cc_out'].corresponding_layer ==
            hwt.layers[2])
    assert (hwt.connections['gcb_in'].corresponding_layer ==
            hwt.layers[2])
    assert (hwt.connections['gcb_out'].corresponding_layer ==
            hwt.layers[1])
    hwt.step(60)


def test_setting_connection_attributes_corresponding_layers(hwt_params,
        hwt_init_vals):
    hwt = HotWaterTank(hwt_params, hwt_init_vals)

    hwt.connections['cc_in'].T = 50
    hwt.connections['cc_in'].F = 0.2

    assert (hwt.connections['cc_in'].corresponding_layer ==
            hwt.layers[1])


def test_init_calculation_of_tank_volume(hwt_params, hwt_init_vals):

    hwt = HotWaterTank(hwt_params, hwt_init_vals)

    V_ges_target = (np.pi * (hwt_params['diameter'] / 1e3 / 2)**2 
            * hwt_params['height'] / 1e3) * 1000  # l

    V_ges = sum([layer.volume for layer in hwt.layers])
    assert abs(V_ges - V_ges_target) < 0.001


def test_init_calculation_of_outer_surface(hwt_params, hwt_init_vals):

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    O_side = np.pi * hwt_params['diameter'] / 1e3 * hwt_params['height'] / 1e3
    O_top = np.pi * (hwt_params['diameter'] / 1e3 / 2)**2
    O_ges_target = O_side + 2 * O_top

    O_ges = sum([layer.outer_surface for layer in hwt.layers])
    print(O_ges_target, O_ges)
    assert abs(O_ges - O_ges_target) < 0.0001


def test_init_temperature_vector(
        hwt_params, hwt_init_vals):

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert hwt.layers[0].T == 30
    assert hwt.layers[1].T == 50
    assert hwt.layers[2].T == 70


def test_init_specifying_layers_explicitly(hwt_init_vals):

    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'layers': [
            {'bottom': 0, 'top': 700},
            {'bottom': 700, 'top': 1400},
            {'bottom': 1400, 'top': 2100}
            ],
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 500}
            }
        }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert hwt.layers[0].T == 30
    assert hwt.layers[1].T == 50
    assert hwt.layers[2].T == 70


def test_init_specifying_sensors_explicitly(hwt_init_vals):
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'sensors': {
            'sensor_0': {'pos': 500},
            'sensor_1': {'pos': 2000}
            },
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 500}
            }
        }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert hwt.sensors['sensor_0'].T == 30
    assert hwt.sensors['sensor_1'].T == 70


def test_step_heating_rod(hwt_init_vals):
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 0,
        'htc_layers': 0,
        'n_layers': 3,
        'T_init': [30, 50, 70],
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
            },
        'heating_rods': {
            'hr_1': {
                'pos': 1800,
                'T_max': 90,
                'P_th_stages': [0, 500, 1000, 2000, 3000],
                'eta': 1
                }
            }
        }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    hwt.heating_rods['hr_1'].P_th_set = 3800
    for i in range(5):
        hwt.step(5*60)
        print('P_el: %s' % hwt.heating_rods['hr_1'].P_el)
    P = 3000
    T = 5 * 5 * 60
    C_W = 4180
    RHO = 1
    V = 21/3 * np.pi * 6**2
    delta_T = P * T / (C_W * RHO * V)
    print(V, delta_T)
    assert abs(hwt.layers[2].T - (70 + delta_T)) < 0.001


def test_max_temp_heating_rod(hwt_init_vals):
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 0,
        'htc_layers': 0,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
        },
        'heating_rods': {
            'hr_1': {
                'pos': 1800,
                'T_max': 90,
                'P_th_stages': [0, 500, 1000, 2000, 3000],
                'eta': 1
            }
        }
    }

    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    hwt.heating_rods['hr_1'].P_th_set = 5000
    hwt.step(5*60)
    assert hwt.heating_rods['hr_1'].P_th == 3000
    assert hwt.heating_rods['hr_1'].P_el == -3000


def test_init_temperature_range():
    hwt_init_vals = {
        'layers': {
            'T': [30, 70]
        }
    }
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
            }
        }
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert hwt.sensors['sensor_00'].T == 30
    assert hwt.sensors['sensor_01'].T == 50

def test_T_mean_attribute():
    hwt_init_vals = {
        'layers': {
            'T': [30, 70]
        }
    }
    hwt_params = {
        'height': 2100,
        'diameter': 1200,
        'T_env': 20.0,
        'htc_walls': 1.0,
        'htc_layers': 20,
        'n_layers': 3,
        'n_sensors': 3,
        'connections': {
            'cc_in': {'pos': 0},
            'cc_out': {'pos': 2099},
            'gcb_in': {'pos': 1700},
            'gcb_out': {'pos': 900}
        }
    }
    hwt = HotWaterTank(hwt_params, hwt_init_vals)
    assert hwt.T_mean == 50
