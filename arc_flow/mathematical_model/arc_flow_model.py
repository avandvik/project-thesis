import gurobipy as gp

import data
import constants as cs
from arc_flow.preprocessing.arc_generator import ArcGenerator
from arc_flow.preprocessing.penalty_cost_calculator import calculate_penalty_costs
import arc_flow.mathematical_model.variable_generator as vg
import arc_flow.mathematical_model.constraint_generator as cg
import arc_flow.postprocessing as post


class ArcFlowModel:

    def __init__(self, name, verbose):
        self.env = gp.Env(f'{name}.log')
        self.model = gp.Model(name=name, env=self.env)
        self.model.setParam('TimeLimit', cs.TIME_LIMIT)

        self.preparation_end_time = 16 * data.TIME_UNITS_PER_HOUR - 1
        self.verbose = verbose
        self.ag = ArcGenerator(self.preparation_end_time, self.verbose)
        self.nodes = None
        self.arc_costs = None
        self.penalty_costs = None

        self.node_time_points = None
        self.start_nodes = None
        self.end_nodes = None
        self.start_times = None
        self.end_times = None
        self.specific_start_times = None
        self.specific_end_times = None

        self.x = {}
        self.u = {}
        self.l_D = {}
        self.l_P = {}

    def preprocess(self):
        self.ag.generate_arcs()
        self.nodes = self.ag.get_nodes()
        self.arc_costs = self.ag.get_arc_costs()
        self.penalty_costs = calculate_penalty_costs(self.arc_costs, self.preparation_end_time)

        self.node_time_points = self.ag.get_node_time_points()
        self.start_nodes = self.ag.get_start_nodes()
        self.end_nodes = self.ag.get_end_nodes()
        self.start_times = self.ag.get_start_times()
        self.end_times = self.ag.get_end_times()
        self.specific_start_times = self.ag.get_specific_start_times()
        self.specific_end_times = self.ag.get_specific_end_times()

    def add_variables(self):
        self.x = vg.initialize_arc_variables(self.model, self.start_times, self.specific_end_times)
        self.u = vg.initialize_order_served_variables(self.model)
        self.l_D = vg.initialize_delivery_load_variables(self.model)
        self.l_P = vg.initialize_pickup_load_variables(self.model)
        self.model.update()

    def add_constraints(self):
        cg.add_flow_conservation_constrs(self.model, self.x, self.start_nodes, self.end_nodes,
                                         self.specific_start_times, self.specific_end_times,
                                         self.node_time_points)
        cg.add_start_and_end_flow_constrs(self.model, self.x, self.start_times, self.specific_end_times)
        cg.add_visit_limit_constrs(self.model, self.x, self.u, self.start_times, self.specific_end_times)
        cg.add_initial_delivery_load_constrs(self.model, self.l_D, self.l_P, self.u)
        cg.add_load_capacity_constrs(self.model, self.l_D, self.l_P, self.u)
        cg.add_load_continuity_constrs_1(self.model, self.x, self.l_D, self.l_P, self.u, self.start_times,
                                         self.specific_end_times)
        cg.add_load_continuity_constrs_2(self.model, self.x, self.l_D, self.l_P, self.start_times,
                                         self.specific_end_times)
        cg.add_final_pickup_load_constrs(self.model, self.l_P, self.u)
        self.model.update()

    def set_objective(self):
        self.model.setObjective(gp.quicksum(self.arc_costs[v][i][t1][j][t2] * self.x[v, i, t1, j, t2]
                                            for v in range(len(data.VESSELS))
                                            for i in range(len(data.ALL_NODES))
                                            for j in range(len(data.ALL_NODES)) if i != j
                                            for t1 in self.start_times[v][i][j]
                                            for t2 in self.specific_end_times[v][i][j][t1])

                                +

                                gp.quicksum(self.penalty_costs[i] * (1 - gp.quicksum(self.u[v, i]
                                                                                     for v in range(len(data.VESSELS))))
                                            for i in data.OPTIONAL_NODE_INDICES)

                                +

                                gp.quicksum(self.l_D[v, i] + self.l_P[v, i]
                                            for v in range(len(data.VESSELS))
                                            for i in data.ALL_NODE_INDICES)

                                , gp.GRB.MINIMIZE)

        self.model.update()

    def run(self):
        self.preprocess()
        self.add_variables()
        self.add_constraints()
        self.set_objective()

        if self.verbose:
            self.model.printStats()

        self.model.optimize()

        print('\n\n')
        for idx, node in enumerate(data.ALL_NODES):
            if node.is_order():
                print(f'{idx}: {node} {node.get_order().get_size()}')
            else:
                print(f'{idx}: {node}')
        print('\n')

        if self.verbose:
            self.model.printAttr('x', filter='*')

        # Print routes in a nice format
        post.print_routes(self.model.getVars())

        print('\n')

        # Separate objective value
        arc_costs, penalty_costs = post.separate_objective(self.model.objVal, self.model.getVars(), self.arc_costs)
        print(f'Objective: {self.model.objVal}'
              f'\n\tArc costs: {arc_costs}'
              f'\n\tPenalty costs: {penalty_costs}')


if __name__ == '__main__':
    afm = ArcFlowModel(f'{cs.PROJECT_DIR_PATH}/output/{cs.FILE_NAME}', cs.VERBOSE)
    afm.run()
