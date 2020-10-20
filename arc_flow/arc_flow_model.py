import gurobipy as gp
import data
from arc_flow.arc_generation import ArcGenerator


class ArcFlowModel:

    def __init__(self, name):
        env = gp.Env(f'{name}.log')
        model = gp.Model(name=name, env=env)
        model.setParam('TimeLimit', 1 * 60 * 60)

        preparation_end_time = 16 * data.TIME_UNITS_PER_HOUR - 1
        self.arc_generator = ArcGenerator(preparation_end_time)

    def preprocess(self):
        self.arc_generator.generate_arcs()


if __name__ == '__main__':
    afm = ArcFlowModel('test')
    afm.preprocess()

