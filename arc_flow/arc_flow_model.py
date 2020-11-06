import gurobipy as gp
import data
from arc_flow.arc_generation import ArcGenerator
import arc_flow.set_generator as sg
import arc_flow.variable_generator as vg
import arc_flow.constraint_generator as cg
from pprint import pprint


class ArcFlowModel:

    def __init__(self, name, verbose):
        self.env = gp.Env(f'{name}.log')
        self.model = gp.Model(name=name, env=self.env)
        self.model.setParam('TimeLimit', 1 * 60 * 60)

        preparation_end_time = 16 * data.TIME_UNITS_PER_HOUR - 1
        self.verbose = verbose
        self.ag = ArcGenerator(preparation_end_time, self.verbose)
        self.nodes = None
        self.arc_costs = None

        self.node_time_points = None
        self.from_nodes = None
        self.to_nodes = None
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
        if self.verbose:
            print('Generating sets...', end=' ')
        self.node_time_points = sg.generate_node_time_points(self.nodes)
        self.from_nodes = sg.generate_from_orders(self.arc_costs, self.node_time_points)
        self.to_nodes = sg.generate_to_orders(self.arc_costs, self.node_time_points)
        self.departure_times = sg.generate_departure_times(self.arc_costs)
        self.arrival_times = sg.generate_arrival_times(self.arc_costs)
        self.specific_departure_times = sg.generate_specific_departure_times(self.arc_costs, self.arrival_times)
        self.specific_arrival_times = sg.generate_specific_arrival_times(self.arc_costs, self.departure_times)
        if self.verbose:
            print('Done!')

    def add_variables(self):
        self.x = vg.initialize_arc_variables(self.model, self.departure_times, self.specific_arrival_times)
        self.u = vg.initialize_order_served_variables(self.model)
        self.l_D = vg.initialize_delivery_load_variables(self.model)
        self.l_P = vg.initialize_pickup_load_variables(self.model)
        self.model.update()

    def add_constraints(self):
        cg.add_flow_conservation_constrs(self.model, self.x, self.from_nodes, self.to_nodes,
                                         self.specific_departure_times, self.specific_arrival_times,
                                         self.node_time_points)
        cg.add_start_and_end_flow_constrs(self.model, self.x, self.departure_times, self.specific_arrival_times)
        cg.add_visit_limit_constrs(self.model, self.x, self.u, self.departure_times, self.specific_arrival_times)
        cg.add_initial_delivery_load_constrs(self.model, self.l_D, self.l_P, self.u)
        cg.add_load_capacity_constrs(self.model, self.l_D, self.l_P, self.u)
        cg.add_load_continuity_constrs_1(self.model, self.x, self.l_D, self.l_P, self.u, self.departure_times,
                                         self.specific_arrival_times)
        cg.add_load_continuity_constrs_2(self.model, self.x, self.l_D, self.l_P, self.departure_times,
                                         self.specific_arrival_times)
        cg.add_final_pickup_load_constrs(self.model, self.l_P, self.u)
        self.model.update()

    def set_objective(self):
        self.model.setObjective(gp.quicksum(self.arc_costs[v][i][t1][j][t2] * self.x[v, i, t1, j, t2]
                                            for v in range(len(data.VESSELS))
                                            for i in range(len(data.ALL_NODES))
                                            for j in range(len(data.ALL_NODES)) if i != j
                                            for t1 in self.departure_times[v][i][j]
                                            for t2 in self.specific_arrival_times[v][i][j][t1])

                                +

                                gp.quicksum(data.POSTPONE_PENALTIES[i] * (1 - self.u[v, i])
                                            for v in range(len(data.VESSELS))
                                            for i in data.OPTIONAL_NODE_INDICES)

                                , gp.GRB.MINIMIZE)

        self.model.update()

    def run(self):
        self.preprocess()
        self.populate_sets()
        self.add_variables()
        self.add_constraints()
        self.set_objective()

        self.model.printStats()
        self.model.optimize()

        for idx, node in enumerate(data.ALL_NODES):
            print(f'{idx}: {node}')

        self.model.printAttr('x')


if __name__ == '__main__':
    afm = ArcFlowModel('test', True)
    afm.run()
