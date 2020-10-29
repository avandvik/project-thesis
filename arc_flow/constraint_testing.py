import data
from arc_flow.arc_generation import ArcGenerator
import arc_flow.set_generator as sg
from pprint import pprint

ag = ArcGenerator(16 * data.TIME_UNITS_PER_HOUR - 1)
ag.generate_arcs()
nodes = ag.get_nodes()
arc_costs = ag.get_arc_costs()

node_time_points = sg.generate_node_time_points(nodes)
from_nodes = sg.generate_from_orders(arc_costs, node_time_points)
to_nodes = sg.generate_to_orders(arc_costs, node_time_points)
departure_times = sg.generate_departure_times(arc_costs)
arrival_times = sg.generate_arrival_times(arc_costs)
specific_departure_times = sg.generate_specific_departure_times(arc_costs, arrival_times)
specific_arrival_times = sg.generate_specific_arrival_times(arc_costs, departure_times)

arc_costs_li = []
for v in range(len(data.VESSELS)):
    for i in data.ALL_NODE_INDICES[:-1]:
        for j in data.DELIVERY_NODE_INDICES:
            for t1 in departure_times[v][i][j]:
                for t2 in specific_arrival_times[v][i][j][t1]:
                    arc_costs_li.append(arc_costs[v][i][t1][j][t2])

print(arc_costs[0][0][63][2][106])
print(arc_costs[0][1][130][3][149])
print(arc_costs[0][2][106][1][130])
print(arc_costs[1][0][63][3][63])

print(arc_costs_li)

"""

x = {}
for v in range(len(data.VESSELS)):
    for i in range(len(data.ALL_NODES)):
        for j in range(len(data.ALL_NODES)):
            if i == j:
                continue
            for t1 in departure_times[v][i][j]:
                for t2 in specific_arrival_times[v][i][j][t1]:
                    x[v, i, t1, j, t2] = 0

u = {}
for v in range(len(data.VESSELS)):
    for i in range(len(data.ALL_NODES)):
        u[v, i] = 0

l_D = {}
for v in range(len(data.VESSELS)):
    for i in range(len(data.ALL_NODES)):
        l_D[v, i] = 0

l_P = {}
for v in range(len(data.VESSELS)):
    for i in range(len(data.ALL_NODES)):
        l_P[v, i] = 0

x[0, 0, 63, 2, 106] = 1
x[0, 1, 130, 3, 149] = 1
x[0, 2, 106, 1, 130] = 1
x[1, 0, 63, 3, 63] = 1

u[0, 0] = 1
u[0, 1] = 1
u[0, 2] = 1
u[0, 3] = 1
u[1, 0] = 1
u[1, 3] = 1

l_D[0, 0] = 25

for v in range(len(data.VESSELS)):
    for i in data.ALL_NODE_INDICES[:-1]:
        for j in data.DELIVERY_NODE_INDICES:
            if i == j:
                continue
            influx_matrix = [[x[v, i, t1, j, t2] for t2 in specific_arrival_times[v][i][j][t1]] for t1 in
                             departure_times[v][i][j]]
            influx = sum([val for sublist in influx_matrix for val in sublist])

            big_M = data.VESSELS[v].get_total_capacity() * (1 - influx)
            if big_M == 0:
                l_D[v, j] = l_D[v, i] - data.ALL_NODES[j].get_order().get_size() * u[v, j]

            print(f'Node {i} -> {j}')
            print(f'\tl_D_{v}_{j}: {l_D[v, j]}')
            print(f'\tl_D_{v}_{i}: {l_D[v, i]}')
            print(f'\tSize of order at node {j}: {data.ALL_NODES[j].get_order().get_size()}')
            print(f'\tOrder at node {j} served by vessel {v}: {u[v, j]}')
            print(f'\tValue of big M: {data.VESSELS[v].get_total_capacity() * (1 - influx)}')
            print(f'\tLHS: {l_D[v, j]}')
            print(f'\tRHS: {l_D[v, i] - data.ALL_NODES[j].get_order().get_size() * u[v, j] - data.VESSELS[v].get_total_capacity() * (1 - influx)}')

pprint(l_D)
"""

