"""
Mosaik interface for hot water tank

"""
import mosaik_api
import jsonpickle
from mosaik_heatpump.hotwatertanksim.hotwatertank import HotWaterTank

class HotWaterTankSimulator(mosaik_api.Simulator):
    def __init__(self):
        # dummy metadata, actual metadata is set in init()
        meta = {
                'type': 'time-based',
                'models': {},
                }
        super().__init__(meta)
        self.models = dict()
        self.sid = None
        self.eid_prefix = 'HotWaterTank_'
        self.step_size = None  # [sec]
        self.async_requests = dict()
        self.time = None
        self.first_iteration = None
        self.step_executed = False

    def init(self, sid, time_resolution, step_size, config, same_time_loop=False):
        self.time_resolution = float(time_resolution)
        if self.time_resolution != 1.0:
            print('WARNING: %s got a time_resolution other than 1.0, which \
                can not be handled by this simulator.', sid)
        self.sid = sid  # simulator id
        self.step_size = step_size
        attrs = ['_', 'snapshot', 'snapshot_connections', 'T_env', 'T_mean', 'mass', 'step_executed']
        if 'n_sensors' in config:
            for i in range(config['n_sensors']):
                attrs.append('sensor_%02d.T' % i)
        elif 'sensors' in config:
            for sensor in config['sensors']:
                attrs.append('%s.T' % sensor)

        if 'connections' in config:
            for connection in config['connections']:
                attrs.append('%s.T' % connection)
                attrs.append('%s.F' % connection)
        if 'heating_rods' in config:
            for heating_rod in config['heating_rods']:
                attrs.append('%s.P_th_set' % heating_rod)
                attrs.append('%s.P_el' % heating_rod)
                attrs.append('%s.P_th' % heating_rod)
                attrs.append('%s.P_th_min' % heating_rod)
                attrs.append('%s.P_th_max' % heating_rod)
        self.meta['models']['HotWaterTank'] = {
            'public': True,
            'params': ['params', 'init_vals', 'snapshot'],
            'attrs': attrs
        }

        if same_time_loop:
            self.meta['type'] = 'event-based'

        return self.meta
    
    def create(self, num, model, params=None, init_vals=None, snapshot=None):
        entities = []

        next_eid = len(self.models)
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            if params is not None:
                self.models[eid] = HotWaterTank(params, init_vals)
            else:
                self.models[eid] = jsonpickle.decode(snapshot)
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs, max_advance):

        if self.meta['type'] == 'event-based':
            if self.time != time:
                self.first_iteration = True
                self.step_executed = False
            else:
                self.first_iteration = False
            self.time = time
        for eid, attrs in inputs.items():
            for attr, src_ids in attrs.items():
                if attr == '_':
                    pass
                else:
                    for src_id, val in src_ids.items():
                        set_nested_attr(self.models[eid], attr, val)
        if self.meta['type'] == 'event-based':
            if not self.first_iteration and not self.step_executed:
                for eid, model in self.models.items():
                    model.step(self.step_size)
                    self.step_executed = True
        else:
            for eid, model in self.models.items():
                model.step(self.step_size)

        if self.meta['type'] == 'event-based':
            if self.step_executed and (time + self.step_size) <= self.mosaik.world.until:  #
                return (time + self.step_size)
        else:
            return (time + self.step_size)

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['HotWaterTank'][
                        'attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                if self.meta['type'] == 'event-based':
                    data['time'] = self.time
                data[eid][attr] = get_nested_attr(self.models[eid], attr)
        return data

def get_nested_attr(hwt, name):
    attr_parts = name.split('.')
    depth = len(attr_parts)
    if depth == 1:
        return getattr(hwt, name)
    if depth == 2:
        if attr_parts[0] in hwt.sensors:
            return getattr(hwt.sensors[attr_parts[0]],
                    attr_parts[1])
        elif attr_parts[0] in hwt.connections:
            return float(getattr(hwt.connections[attr_parts[0]],
                    attr_parts[1]))
        elif attr_parts[0] in hwt.heating_rods:
            return getattr(hwt.heating_rods[attr_parts[0]],
                    attr_parts[1])

def set_nested_attr(hwt, name, value):
    attr_parts = name.split('.')
    depth = len(attr_parts)
    if depth == 1:
        setattr(hwt, name, value)
    if depth == 2:
        if attr_parts[0] in hwt.sensors:
            setattr(hwt.sensors[attr_parts[0]],
                    attr_parts[1], value)
        elif attr_parts[0] in hwt.connections:
            setattr(hwt.connections[attr_parts[0]],
                    attr_parts[1], value)
        elif attr_parts[0] in hwt.heating_rods:
            setattr(hwt.heating_rods[attr_parts[0]],
                    attr_parts[1], value)

def main():
    return mosaik_api.start_simulation(HotWaterTankSimulator())

if __name__ == '__main__':
    main()
