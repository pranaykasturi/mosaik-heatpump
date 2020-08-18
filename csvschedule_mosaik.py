"""This module contains a simulator for a csv schedule"""
import mosaik_api
import numpy as np
from datetime import datetime, timedelta
# from pysimmods.utils.constants import DT_FORMAT

META = {
    'models': {
        'CSVSchedule': {
            'public': True,
            'params': ['params', 'init_vals'],
            'attrs': ['cons_Q']
        }
    }
}


class CSVScheduleSimulator(mosaik_api.Simulator):
    """A simple simulator for a schedule in a csv file"""
    def __init__(self):
        super().__init__(META)
        self.sid = None
        self.models = dict()
        self.step_size = None
        # self.now_dt = None

    def init(self, sid, **sim_params):
        """Called exactly ones after the simulator has been started.

        :return: the meta dict (set by mosaik_api.Simulator)
        """
        self.sid = sid
        self.step_size = sim_params['step_size']
        # self.now_dt = datetime.strptime(
        #     sim_params['start_date'], DT_FORMAT)
        return self.meta

    def create(self, num, model, **model_params):
        """Initialize the simulation model instance (entity)

        :return: a list with information on the created entity
        """
        assert num == 1  # each schedule only once
        entities = list()
        next_eid = len(self.models)

        eid = '%s_%d' % (model, next_eid)
        self.models[eid] = CSVSchedule(model_params['params'])
        entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs):
        """Perform a simulation step"""
        for model in self.models.values():
            model.step_size = self.step_size
            model.step()

        return time + self.step_size

    def get_data(self, outputs):
        """Returns the requested outputs (if feasible)"""
        data = dict()
        for eid, attrs in outputs.items():
            data[eid] = dict()
            for attr in attrs:
                model = eid.split('_')[0]
                if attr not in self.meta['models'][model]['attrs']:
                    raise AttributeError('Unknown output attribute: %s' % attr)
                data[eid][attr] = getattr(self.models[eid], attr)
        return data


class CSVSchedule():
    """A VERY simple schedule model"""
    def __init__(self, params):

        self.schedule = np.genfromtxt(
            params['filename'], dtype=float, delimiter=',')

        self.cur_idx = 0
        self.cons_Q = None

    def step(self):
        """Perform a simulation step"""

        self.cons_Q = self.schedule[self.cur_idx]
        self.cur_idx = (self.cur_idx + 1) % len(self.schedule)
        # repeat
