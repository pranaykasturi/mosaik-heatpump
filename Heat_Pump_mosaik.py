import mosaik_api
from Heat_Pump_Model import Heat_Pump

META = {
    'models': {
        'HeatPump': {
            'public': True,
            'params': ['params'],
            'attrs': ['cons_Q', 'heat_source_T', 'heat_source', 'cons_T', 'p_kw', 'COP', 'amb_T'],
        },
    },
}

class HeatPumpSimulator(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.models = dict()  # contains the model instances
        self.sid = None
        self.eid_prefix = 'HeatPump_'
        self.step_size = None
        # start time of simulation as UTC ISO 8601 time string

    def init(self, sid, step_size):
        self.sid = sid # simulator id
        self.step_size = step_size
        return self.meta

    def create(self, num, model, params):
        entities = []

        next_eid = len(self.models)
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.models[eid] = Heat_Pump(params)
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs):
        for eid, attrs in inputs.items():
            for attr, src_ids in attrs.items():
                if len(src_ids) > 1:
                    raise ValueError('Two many inputs for attribute %s' % attr)
                for val in src_ids.values():
                    setattr(self.models[eid].inputs, attr, val)

            self.models[eid].inputs.step_size = self.step_size
            self.models[eid].step()
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['HeatPump'][
                        'attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                data[eid][attr] = getattr(self.models[eid].state, attr)
        return data

# def main():
#     return mosaik_api.start_simulation(HeatPumpSimulator())
#
# if __name__ == '__main__':
#     main()