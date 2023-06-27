import mosaik_api
from mosaik_heatpump.controller.controller import Controller

META = {
    'type': 'time-based',
    'models': {
        'Controller': {
            'public': True,
            'params': ['params'],
            'attrs': ['_', 'T_amb', 'T_amb_hwt', 'heat_source_T', 'hp_demand', 'heat_supply', 'heat_demand', 'sh_demand', 'sh_supply',
                      'dhw_demand', 'dhw_supply', 'sh_in_F', 'sh_in_T', 'sh_out_F', 'dhw_in_F', 'dhw_in_T', 'dhw_out_F',
                      'hp_in_F', 'hp_in_T', 'hp_out_F', 'hp_out_T', 'hp_supply', 'hwt_connections', 'T_mean', 'hwt_mass',
                      'hwt_hr_P_th_set', 'hp_on_fraction', 'hp_cond_m', 'sh_out_T', 'dhw_out_T', 'P_hr_sh', 'P_hr_dhw',
                      'T_room', 'bottom_layer_T', 'top_layer_T', 'execute_step', 'PVT_T_in', 'PVT_T_out'],
        },
    },
}

hp_attrs = ['hp_demand', 'hp_out_T', 'T_amb', 'heat_source_T']
hwt_attrs = ['sh_in_F', 'sh_in_T', 'sh_out_F', 'dhw_in_F', 'dhw_in_T', 'dhw_out_F', 'T_amb_hwt', 'hp_in_T', 'hp_in_F',
             'hp_out_F']

class ControllerSimulator(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)

        self.models = dict()  # contains the model instances
        self.sid = None
        self.eid_prefix = 'Controller_'
        self.step_size = None
        self.async_requests = dict()
        self.time = None
        self.step_executed = False
        self.first_iteration = None
        self.final_iteration = False

    def init(self, sid, time_resolution, step_size, same_time_loop=False):
        self.time_resolution = float(time_resolution)
        if self.time_resolution != 1.0:
            print('WARNING: %s got a time_resolution other than 1.0, which \
                can not be handled by this simulator.', sid)
        self.sid = sid # simulator id
        self.step_size = step_size
        if same_time_loop:
            self.meta['type'] = 'event-based'
        return self.meta

    def create(self, num, model, params=None):
        entities = []

        next_eid = len(self.models)
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            if params is not None:
                self.models[eid] = Controller(params)
            else:
                self.models[eid] = Controller()
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs, max_advance):
        if self.meta['type'] == 'event-based':
            if self.time != time:
                self.first_iteration = True
                self.final_iteration = False
                self.step_executed = False
            elif self.step_executed:
                if not self.final_iteration:
                    self.first_iteration = False
                    self.final_iteration = True
                else:
                    self.final_iteration = False
        for eid, attrs in inputs.items():
            if self.meta['type'] == 'event-based':
                if time != self.time:
                    self.time = time
                    setattr(self.models[eid], 'execute_step', True)
            for attr, src_ids in attrs.items():
                if len(src_ids) > 1:
                    raise ValueError('Two many inputs for attribute %s' % attr)
                for val in src_ids.values():
                    setattr(self.models[eid], attr, val)
            if self.meta['type'] == 'event-based':
                if not self.step_executed:
                    self.models[eid].step_size = self.step_size
                    self.models[eid].step()
                    self.step_executed = True
            else:
                self.models[eid].step_size = self.step_size
                self.models[eid].step()

        if self.meta['type'] == 'event-based':
            return None
        else:
            return time + self.step_size

    def get_data(self, outputs):
        data = {}
        data['time'] = self.time
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Controller'][
                        'attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                if self.meta['type'] =='event-based':
                    if self.first_iteration and attr in hp_attrs:
                        data[eid][attr] = getattr(self.models[eid], attr)
                    elif self.final_iteration and attr in hwt_attrs:
                        if attr == 'T_amb_hwt':
                            data[eid][attr] = getattr(self.models[eid], 'T_amb')
                        else:
                            data[eid][attr] = getattr(self.models[eid], attr)
                else:
                    data[eid][attr] = getattr(self.models[eid], attr)
        return data

def main():
    return mosaik_api.start_simulation(ControllerSimulator())

if __name__ == '__main__':
    main()
