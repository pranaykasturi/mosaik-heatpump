import mosaik_api
from mosaik_heatpump.coolingloadsim.coolingloadsim import CoolingLoadSim

META = {
    'type': 'time-based',
    'models': {
        'CoolingLoadSim': {
            'public': True,
            'params': ['params'],
            'attrs': ['_', 'T_amb', 'G', 'Q_evap', 'T_room'],
        },
    },
}


class CoolingLoadSimulator(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)

        self.models = dict()  # contains the model instances
        self.sid = None
        self.eid_prefix = 'CoolingLoadSim_'
        self.step_size = None

    def init(self, sid, time_resolution, step_size):
        self.time_resolution = float(time_resolution)
        if self.time_resolution != 1.0:
            print('WARNING: %s got a time_resolution other than 1.0, which \
                can not be handled by this simulator.', sid)
        self.sid = sid # simulator id
        self.step_size = step_size
        return self.meta

    def create(self, num, model, params=None):
        entities = []

        next_eid = len(self.models)
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            if params is not None:
                self.models[eid] = CoolingLoadSim(params)
            else:
                self.models[eid] = CoolingLoadSim()
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs, max_advance):
        # print('controller inputs: %s' % inputs)
        for eid, attrs in inputs.items():
            # print(eid, attrs)
            for attr, src_ids in attrs.items():
                if len(src_ids) > 1:
                    raise ValueError('Two many inputs for attribute %s' % attr)
                for val in src_ids.values():
                    setattr(self.models[eid], attr, val)

            self.models[eid].step_size = self.step_size
            self.models[eid].step()

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['CoolingLoadSim'][
                        'attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                data[eid][attr] = getattr(self.models[eid], attr)
        return data

def main():
    return mosaik_api.start_simulation(CoolingLoadSimulator())

if __name__ == '__main__':
    main()
