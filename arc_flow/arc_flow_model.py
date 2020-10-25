import gurobipy as gp
import data
from arc_flow.arc_generation import ArcGenerator
import arc_flow.set_generator as sg
import arc_flow.variable_generator as vg
import arc_flow.constraint_generator as cg
from pprint import pprint


class ArcFlowModel:

    def __init__(self, name):
        self.env = gp.Env(f'{name}.log')
        self.model = gp.Model(name=name, env=self.env)
        self.model.setParam('TimeLimit', 1 * 60 * 60)

        preparation_end_time = 16 * data.TIME_UNITS_PER_HOUR - 1
        self.ag = ArcGenerator(preparation_end_time)
        self.nodes = None
        self.arc_costs = None

        self.node_time_points = None
        self.from_orders = None
        self.to_orders = None
        self.departure_times = None
        self.arrival_times = None
        self.specific_departure_times = None
        self.specific_arrival_times = None

        self.x = {}
        self.u = {}
        self.l_D = {}
        self.l_P = {}

    def preprocess(self):
        self.ag.generate_arcs()
        self.nodes = self.ag.get_nodes()
        self.arc_costs = self.ag.get_arc_costs()

    def populate_sets(self):
        self.node_time_points = sg.generate_node_time_points(self.nodes)
        pprint(self.node_time_points, compact=True)
        self.from_orders = sg.generate_from_orders(self.arc_costs, self.node_time_points)
        self.to_orders = sg.generate_to_orders(self.arc_costs, self.node_time_points)
        self.departure_times = sg.generate_departure_times(self.arc_costs)
        self.arrival_times = sg.generate_arrival_times(self.arc_costs)
        pprint(self.arrival_times, compact=True)
        self.specific_departure_times = sg.generate_specific_departure_times(self.arc_costs, self.arrival_times)
        self.specific_arrival_times = sg.generate_specific_arrival_times(self.arc_costs, self.departure_times)

    def add_variables(self):
        self.x = vg.initialize_arc_variables(self.model, self.departure_times, self.specific_arrival_times)
        self.u = vg.initialize_order_served_variables(self.model)
        self.l_D = vg.initialize_delivery_load_variables(self.model)
        self.l_P = vg.initialize_pickup_load_variables(self.model)

    def add_constraints(self):
        cg.add_flow_conservation_constrs(self.model, self.x, self.to_orders, self.specific_departure_times,
                                         self.specific_arrival_times, self.node_time_points)

    def run(self):
        self.preprocess()
        self.populate_sets()


if __name__ == '__main__':
    afm = ArcFlowModel('test')
    afm.run()
