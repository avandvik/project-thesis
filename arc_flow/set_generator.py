import data
from pprint import pprint


def generate_node_time_points(nodes):
    node_time_points = [[[] for _ in data.ORDERS] for _ in data.VESSELS]

    for vessel in data.VESSELS:
        for order in data.ORDERS:
            for time_point in data.TIME_POINTS_DISC:
                if nodes[vessel.get_index()][order.get_index()][time_point]:
                    node_time_points[vessel.get_index()][order.get_index()].append(time_point)

    return node_time_points


# TODO: Generalize all functions below
def generate_from_orders(arc_costs, node_time_points):
    from_orders = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for j in range(len(data.ORDERS)):
            for t2 in node_time_points[v][j]:
                for i in range(len(data.ORDERS)):
                    for t1 in data.TIME_POINTS_DISC:
                        if arc_costs[v][i][t1][j][t2] != 0:
                            from_orders[v][j][t2].append(i)
                            break

    return from_orders


def generate_to_orders(arc_costs, node_time_points):
    to_orders = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for t1 in node_time_points[v][i]:
                for j in range(len(data.ORDERS)):
                    for t2 in data.TIME_POINTS_DISC:
                        if arc_costs[v][i][t1][j][t2] != 0:
                            to_orders[v][i][t1].append(j)
                            break

    return to_orders


def generate_departure_times(arc_costs):
    departure_times = [[[[] for _ in data.ORDERS] for _ in data.ORDERS] for _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for j in range(len(data.ORDERS)):
                for t1 in data.TIME_POINTS_DISC:
                    for t2 in data.TIME_POINTS_DISC:
                        if arc_costs[v][i][t1][j][t2] != 0:
                            departure_times[v][i][j].append(t1)
                            break

    return departure_times


def generate_arrival_times(arc_costs):
    arrival_times = [[[[] for _ in data.ORDERS] for _ in data.ORDERS] for _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for j in range(len(data.ORDERS)):
                for t2 in data.TIME_POINTS_DISC:
                    for t1 in range(len(data.TIME_POINTS_DISC)):
                        if arc_costs[v][i][t1][j][t2] != 0:
                            arrival_times[v][i][j].append(t2)
                            break

    return arrival_times


def generate_specific_departure_times(arc_costs, arrival_times):
    specific_departure_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.ORDERS]
                                for _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for j in range(len(data.ORDERS)):
                for t2 in arrival_times[v][i][j]:
                    for t1 in data.TIME_POINTS_DISC:
                        if arc_costs[v][i][t1][j][t2] != 0:
                            specific_departure_times[v][i][j][t2].append(t1)

    return specific_departure_times


def generate_specific_arrival_times(arc_costs, departure_times):
    specific_arrival_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ORDERS] for _ in data.ORDERS] for
                              _ in data.VESSELS]

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for j in range(len(data.ORDERS)):
                for t1 in departure_times[v][i][j]:
                    for t2 in data.TIME_POINTS_DISC:
                        if arc_costs[v][i][t1][j][t2] != 0:
                            specific_arrival_times[v][i][j][t1].append(t2)

    return specific_arrival_times
