import gurobipy as gp
import data
from arc_generation import ArcGenerator
from pprint import pprint


class ArcFlowModel:

    def __init__(self, name):
        env = gp.Env(f'{name}.log')
        model = gp.Model(name=name, env=env)
        model.setParam('TimeLimit', 1 * 60 * 60)

        self.arc_generator = ArcGenerator()

    def preprocess(self):
        preparation_end_time = 16 * data.TIME_UNITS_PER_HOUR - 1
        self.arc_generator.generate_arcs(preparation_end_time)

    def generate_node_time_points(self):
        node_time_points = [[[] for _ in data.ORDERS] for _ in data.VESSELS]

        for vessel in data.VESSELS:
            for order in data.ORDERS:
                for time_point in data.TIME_POINTS_DISC:
                    if self.arc_generator.get_nodes()[vessel.get_index()][order.get_index()][time_point]:
                        node_time_points[vessel.get_index()][order.get_index()].append(time_point)

        pprint(node_time_points, compact=True)

        return node_time_points

    def generate_from_orders(self, node_time_points):
        from_orders = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.VESSELS]

        for v in range(len(data.VESSELS)):
            for j in range(len(data.ORDERS)):
                for t2 in node_time_points[v][j]:
                    for i in range(len(data.ORDERS)):
                        visited_order_i_from_j = False
                        for t1 in data.TIME_POINTS_DISC:
                            if self.arc_generator.arc_costs[v][i][t1][j][t2] != 0:
                                visited_order_i_from_j = True
                                break
                        if visited_order_i_from_j:
                            from_orders[v][j][t2].append(i)

        pprint(from_orders, compact=True)

        return from_orders

    def generate_to_orders(self, node_time_points):
        to_orders = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.VESSELS]

        for v in range(len(data.VESSELS)):
            for i in range(len(data.ORDERS)):
                for t1 in node_time_points[v][i]:
                    for j in range(len(data.ORDERS)):
                        visited_order_j_from_i = False
                        for t2 in data.TIME_POINTS_DISC:
                            if self.arc_generator.arc_costs[v][i][t1][j][t2] != 0:
                                visited_order_j_from_i = True
                                break
                        if visited_order_j_from_i:
                            to_orders[v][i][t1].append(j)

        return to_orders


if __name__ == '__main__':
    afm = ArcFlowModel('test')
    afm.preprocess()
    time_points = afm.generate_node_time_points()
    afm.generate_from_orders(time_points)

