import data
import arc_flow.preprocessing.helpers as hlp
from collections import defaultdict as dd
import multiprocessing
import time

# arcs[vessel][start_node][start_time][end_node][end_time] -> True/False
arcs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: False)))))
# arc_costs[vessel][start_node][start_time][end_node][end_time] -> arc_costs
arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))
# sep_arc_costs[vessel][start_node][start_time][end_node][end_time] -> (fuel_cost, charter_cost)
sep_arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))
# arc_arrival_times[vessel][start_node][start_time][end_node][end_time] -> arrival_time
arc_arrival_times = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))
# node_time_points[vessel][node] -> time
node_time_points = [[[] for _ in data.ALL_NODES] for _ in data.VESSELS]
# start_nodes[vessel][end_node][end_time] -> start_node
start_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]
# end_nodes[vessel][start_node][start_time] -> end_node
end_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]
# start_times[vessel][start_node][end_node] -> start_time
start_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]
# end_times[vessel][start_node][end_node] -> end_time
end_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]
# specific_start_times[vessel][start_node][end_node][end_times] -> start_time
specific_start_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                         for _ in data.ALL_NODES] for _ in data.VESSELS]
# specific_end_times[vessel][start_node][end_node][start_time] -> end_time
specific_end_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                       for _ in data.ALL_NODES] for _ in data.VESSELS]
verbose = True


def generate_arcs():
    visit_list = hlp.generate_visit_list()

    number_of_processes = multiprocessing.cpu_count()
    print(f'Number of processes: {number_of_processes}')
    pool = multiprocessing.Pool()

    for vessel in data.VESSELS:
        start_node = data.ALL_NODES[0]
        for not_visited_node in visit_list:
            new_visit_list = visit_list.copy()
            new_visit_list.remove(not_visited_node)
            start_time = data.PREPARATION_END_TIME

            pool.apply_async(visit_nodes,
                             args=(start_node, not_visited_node, new_visit_list, start_time, vessel,))

            # visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel)

    pool.close()
    pool.join()


def visit_nodes(start_node, end_node, visit_list, start_time, vessel):
    if hlp.is_illegal_arc(start_node, end_node):
        return

    # tabs = '\t' * (len(data.ALL_NODES) - 2 - len(visit_list))
    # print(f'{tabs} {start_node} ({start_time}) -> {end_node}', end=' ')

    inbound_et, idling = inbound_arc_calc(start_node, end_node, start_time, vessel)

    # print(inbound_et)

    if not visit_list:
        return
    if end_node.is_end_depot():
        return

    internal_nodes = hlp.get_internal_nodes(end_node)
    if len(internal_nodes) == 3:
        generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel)
        internal_et = internal_arc_calc(internal_nodes[:2], inbound_et, vessel)
        generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel)
        internal_et = internal_arc_calc([internal_nodes[0], internal_nodes[2]], inbound_et, vessel)
        generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel)
        internal_et = internal_arc_calc(internal_nodes, inbound_et, vessel)
        generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel)
    elif len(internal_nodes) == 2:
        generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel)
        internal_et = internal_arc_calc(internal_nodes, inbound_et, vessel)
        generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel)
    else:
        node = internal_nodes[0]
        generate_outbound_arcs(node, visit_list, inbound_et, vessel)


def generate_outbound_arcs(start_node, visit_list, start_times, vessel):
    for start_time in start_times:
        for not_visited_node in visit_list:
            new_visit_list = visit_list.copy()
            new_visit_list.remove(not_visited_node)
            visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel)


def inbound_arc_calc(start_node, end_node, start_time, vessel):
    distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
    early_arrival, late_arrival = hlp.get_arrival_time_span(distance, start_time)
    service_duration = hlp.calculate_service_time(end_node)
    checkpoints, idling = hlp.get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
    costs, end_times, arr_times = hlp.calculate_arc_data(start_time, checkpoints, distance, vessel)
    end_times = save_inbound_arcs(start_node, end_node, start_time, arr_times, end_times, costs, vessel, idling)
    return end_times, idling


def save_inbound_arcs(start_node, end_node, start_time, arr_times, end_times, costs, vessel, idling):
    if end_node.is_end_depot() or idling:
        end_time = add_best_arc(start_node, end_node, costs, start_time, arr_times, end_times, vessel)
        return [end_time]
    else:
        add_arcs(start_node, end_node, costs, start_time, arr_times, end_times, vessel)
        return end_times


def internal_arc_calc(internal_nodes, start_times, vessel):
    end_times = []
    for start_time in start_times:
        service_durations = []
        for internal_node in internal_nodes[1:]:
            service_durations.append(hlp.calculate_service_time(internal_node))

        total_service_duration = sum(service_durations)
        end_node, end_time = internal_nodes[-1], start_time + total_service_duration
        end_times.append(end_time)

        checkpoints = []
        service_start_time = start_time
        for service_duration in service_durations:
            checkpoints.append((service_start_time, service_start_time, service_start_time + service_duration))
            service_start_time += service_duration

        if hlp.is_return_possible(end_node, end_time, vessel) \
                and hlp.is_servicing_possible(start_time, total_service_duration, end_node):
            costs, end_times, arr_times = hlp.calculate_arc_data(start_time, checkpoints, 0, vessel)

            save_internal_arcs(internal_nodes, checkpoints, arr_times, end_times, costs, vessel)
    return end_times


def save_internal_arcs(internal_nodes, checkpoints, arr_times, end_times, costs, vessel):
    for i in range(len(internal_nodes) - 1):
        start_node, end_node = internal_nodes[i], internal_nodes[i + 1]
        start_time = checkpoints[i][1]
        add_arcs(start_node, end_node, costs, start_time, arr_times, [end_times[i]], vessel)


def add_best_arc(start_node, end_node, costs, start_time, arr_times, end_times, vessel):
    arcs = [(ac[-1], ac[:-1], aet, aat) for ac, aet, aat in zip(costs, end_times, arr_times)]
    if not arcs:
        return
    best_return_arc = min(arcs)
    cost, sep_cost, end_time, arr_time = best_return_arc
    update_sets(start_node, end_node, cost, sep_cost, start_time, end_time, vessel, arr_time)
    return end_time


def add_arcs(start_node, end_node, costs, start_time, arr_times, end_times, vessel):
    for cost, end_time, arr_time in zip(costs, end_times, arr_times):
        update_sets(start_node, end_node, cost[-1], cost[:-1], start_time, end_time, vessel, arr_time)


def update_sets(sn, en, ac, sac, ast, aet, v, aat):
    if verbose:
        distance = sn.get_installation().get_distance_to_installation(en.get_installation())
        if aat - ast > 0:
            speed = distance / hlp.disc_to_exact_hours(aat - ast)
        else:
            speed = 0
        # print(f'Adding arc: {sn} ({ast}) -> {en} ({aet}) ({ac}) {speed}')

    arcs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = True
    arc_costs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = ac
    sep_arc_costs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = sac
    arc_arrival_times[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = aat

    if aet not in node_time_points[v.get_index()][en.get_index()]:
        node_time_points[v.get_index()][en.get_index()].append(aet)
    if sn.get_index() not in start_nodes[v.get_index()][en.get_index()][aet]:
        start_nodes[v.get_index()][en.get_index()][aet].append(sn.get_index())
    if en.get_index() not in end_nodes[v.get_index()][sn.get_index()][ast]:
        end_nodes[v.get_index()][sn.get_index()][ast].append(en.get_index())
    if ast not in start_times[v.get_index()][sn.get_index()][en.get_index()]:
        start_times[v.get_index()][sn.get_index()][en.get_index()].append(ast)
    if aet not in end_times[v.get_index()][sn.get_index()][en.get_index()]:
        end_times[v.get_index()][sn.get_index()][en.get_index()].append(aet)
    if ast not in specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet]:
        specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet].append(ast)
    if aet not in specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast]:
        specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast].append(aet)


def print_arcs():
    counter = 0
    for start_node in data.ALL_NODES[:-1]:
        for end_node in data.ALL_NODES[1:]:
            for start_time in range(data.PREPARATION_END_TIME, data.PERIOD_DISC):
                for end_time in range(data.PREPARATION_END_TIME, data.PERIOD_DISC):
                    if arcs[0][start_node.get_index()][start_time][end_node.get_index()][end_time]:
                        arc_cost = arc_costs[0][start_node.get_index()][start_time][end_node.get_index()][end_time]
                        print(f'{start_node} ({start_time}) -> {end_node} ({end_time}): {arc_cost}')
                        counter += 1
    print(counter)


def get_arc_costs(self):
    return self.arc_costs


def get_sep_arc_costs(self):
    return self.sep_arc_costs


def get_arc_arrival_times(self):
    return self.arc_arrival_times


def get_node_time_points(self):
    return self.node_time_points


def get_start_nodes(self):
    return self.start_nodes


def get_end_nodes(self):
    return self.end_nodes


def get_start_times(self):
    return self.start_times


def get_end_times(self):
    return self.end_times


def get_specific_start_times(self):
    return self.specific_start_times


def get_specific_end_times(self):
    return self.specific_end_times


if __name__ == '__main__':
    start = time.time()
    generate_arcs()
    print(f'Runtime: {time.time() - start}')
    print_arcs()
