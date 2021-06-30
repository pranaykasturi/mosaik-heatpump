import mosaik_api
import multiprocessing as mp
import json
import os
from mosaik_heatpump.heatpump.Heat_Pump_Model import Heat_Pump

META = {
    'type': 'time-based',
    'models': {
        'HeatPump': {
            'public': True,
            'params': ['params'],
            'attrs': ['Q_Demand', 'Q_Supplied', 'heat_source_T', 'heat_source', 'cons_T', 'P_Required', 'COP',
                      'cond_m_in', 'cond_m_out', 'cond_in_T'],
        },
    },
}

JSON_COP_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), 'COP_m_data.json'))

class HeatPumpSimulator(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.time_resolution = None
        self.models = dict()  # contains the model instances
        self.sid = None
        self.eid_prefix = 'HeatPump_'
        self.step_size = None

        self.parallelization = False
        self.processes = 1
        # start time of simulation as UTC ISO 8601 time string

    def init(self, sid, time_resolution, step_size):
        self.time_resolution = float(time_resolution)
        if self.time_resolution != 1.0:
            print('WARNING: %s got a time_resolution other than 1.0, which \
                can not be handled by this simulator.', sid)
        self.sid = sid # simulator id
        self.step_size = step_size
        return self.meta

    def create(self, num, model, params):
        entities = []

        if 'processes' in params:
            self.parallelization = True
            self.processes = params['processes']
            if num < self.processes:
                self.processes = num

        COP_m_data = None
        if params['calc_mode'] == 'fast' or params['calc_mode'] == 'fixed':
            with open(JSON_COP_DATA, "r") as read_file_1:
                COP_m_data = json.load(read_file_1)

        next_eid = len(self.models)
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.models[eid] = Heat_Pump(params, COP_m_data)
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs, max_advance):
        # print('heatpump inputs: %s' % inputs)
        for eid, attrs in inputs.items():
            for attr, src_ids in attrs.items():
                if len(src_ids) > 1:
                    raise ValueError('Two many inputs for attribute %s' % attr)
                for val in src_ids.values():
                    setattr(self.models[eid].inputs, attr, val)

            self.models[eid].inputs.step_size = self.step_size

        if self.parallelization:
            pool = mp.Pool(processes=self.processes)
            for eid, model in self.models.items():
                pool.apply_async(model.step(), args=())
            pool.close()
            pool.join()
        else:
            for eid, model in self.models.items():
                model.step()

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['HeatPump'][
                        'attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                data[eid][attr] = float(getattr(self.models[eid].state, attr))
        return data

def main():
    return mosaik_api.start_simulation(HeatPumpSimulator())

if __name__ == '__main__':
    main()