import data
import arc_flow.preprocessing.helpers as hlp
from collections import defaultdict
import multiprocessing
from multiprocessing.managers import SyncManager
from multiprocessing.shared_memory import SharedMemory
import threading
import time
from pprint import pprint


def generate_arcs():
    visit_list = hlp.generate_visit_list()

    number_of_processes = multiprocessing.cpu_count()
    print(f'Number of processes: {number_of_processes}')
    pool = multiprocessing.Pool()
    manager = multiprocessing.Manager()

    processes = []

    # arcs[vessel][start_node][start_time][end_node][end_time] -> True/False
    arcs = manager.dict()

    for vessel in data.VESSELS:
        arcs.update({vessel.get_index(): {}})
        start_node = data.ALL_NODES[0]
        arcs[vessel.get_index()].update({start_node.get_index(): {}})
        for not_visited_node in visit_list:
            start_time = data.PREPARATION_END_TIME
            new_visit_list = visit_list.copy()
            new_visit_list.remove(not_visited_node)

            process = multiprocessing.Process(target=visit_nodes,
                                              args=(start_node, not_visited_node, new_visit_list, start_time, vessel, arcs))
            processes.append(process)
            process.start()

            # pool.apply_async(visit_nodes,
            #                  args=(start_node, not_visited_node, new_visit_list, start_time, vessel, arcs, ))

            # visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel, arcs)

    for process in processes:
        process.join()

    # pool.close()
    # pool.join()

    return arcs


def visit_nodes(start_node, end_node, visit_list, start_time, vessel, arcs):
    if hlp.is_illegal_arc(start_node, end_node):
        return

    # tabs = '\t' * (len(data.ALL_NODES) - 2 - len(visit_list))
    # print(f'{tabs} {start_node} ({start_time}) -> {end_node}', end=' ')

    inbound_et, idling = inbound_arc_calc(start_node, end_node, start_time, vessel, arcs)

    # print(inbound_et)

    if not visit_list:
        return
    if end_node.is_end_depot():
        return

    internal_nodes = hlp.get_internal_nodes(end_node)
    if len(internal_nodes) == 3:
        generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel, arcs)
        internal_et = internal_arc_calc(internal_nodes[:2], inbound_et, vessel, arcs)
        generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel, arcs)
        internal_et = internal_arc_calc([internal_nodes[0], internal_nodes[2]], inbound_et, vessel, arcs)
        generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel, arcs)
        internal_et = internal_arc_calc(internal_nodes, inbound_et, vessel, arcs)
        generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel, arcs)
    elif len(internal_nodes) == 2:
        generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel, arcs)
        internal_et = internal_arc_calc(internal_nodes, inbound_et, vessel, arcs)
        generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel, arcs)
    else:
        node = internal_nodes[0]
        generate_outbound_arcs(node, visit_list, inbound_et, vessel, arcs)


def generate_outbound_arcs(start_node, visit_list, start_times, vessel, arcs):
    for start_time in start_times:
        for not_visited_node in visit_list:
            new_visit_list = visit_list.copy()
            new_visit_list.remove(not_visited_node)
            visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel, arcs)


def inbound_arc_calc(start_node, end_node, start_time, vessel, arcs):
    distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
    early_arrival, late_arrival = hlp.get_arrival_time_span(distance, start_time)
    service_duration = hlp.calculate_service_time(end_node)
    checkpoints, idling = hlp.get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
    costs, end_times, arr_times = hlp.calculate_arc_data(start_time, checkpoints, distance, vessel)
    end_times = save_inbound_arcs(start_node, end_node, start_time, arr_times, end_times, costs, vessel, idling, arcs)
    return end_times, idling


def save_inbound_arcs(start_node, end_node, start_time, arr_times, end_times, costs, vessel, idling, arcs):
    if end_node.is_end_depot() or idling:
        end_time = add_best_arc(start_node, end_node, costs, start_time, arr_times, end_times, vessel, arcs)
        return [end_time]
    else:
        add_arcs(start_node, end_node, costs, start_time, arr_times, end_times, vessel, arcs)
        return end_times


def internal_arc_calc(internal_nodes, start_times, vessel, arcs):
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

            save_internal_arcs(internal_nodes, checkpoints, arr_times, end_times, costs, vessel, arcs)
    return end_times


def save_internal_arcs(internal_nodes, checkpoints, arr_times, end_times, costs, vessel, arcs):
    for i in range(len(internal_nodes) - 1):
        start_node, end_node = internal_nodes[i], internal_nodes[i + 1]
        start_time = checkpoints[i][1]
        add_arcs(start_node, end_node, costs, start_time, arr_times, [end_times[i]], vessel, arcs)


def add_best_arc(start_node, end_node, costs, start_time, arr_times, end_times, vessel, arcs):
    arc_info = [(ac[-1], ac[:-1], aet, aat) for ac, aet, aat in zip(costs, end_times, arr_times)]
    if not arc_info:
        return
    best_return_arc = min(arc_info)
    cost, sep_cost, end_time, arr_time = best_return_arc
    update_sets(start_node, end_node, cost, sep_cost, start_time, end_time, vessel, arr_time, arcs)
    return end_time


def add_arcs(start_node, end_node, costs, start_time, arr_times, end_times, vessel, arcs):
    for cost, end_time, arr_time in zip(costs, end_times, arr_times):
        update_sets(start_node, end_node, cost[-1], cost[:-1], start_time, end_time, vessel, arr_time, arcs)


def update_sets(sn, en, ac, sac, ast, aet, v, aat, arcs):
    if sn.get_index() not in arcs[v.get_index()].keys():
        tmp = arcs[v.get_index()]
        tmp.update({sn.get_index(): {}})
        arcs[v.get_index()] = tmp
    if ast not in arcs[v.get_index()][sn.get_index()].keys():
        tmp = arcs[v.get_index()][sn.get_index()]
        tmp.update({ast: {}})
        tmp_2 = arcs[v.get_index()]
        tmp_2[sn.get_index()].update(tmp)
        arcs[v.get_index()] = tmp_2
    if en.get_index() not in arcs[v.get_index()][sn.get_index()][ast].keys():
        tmp = arcs[v.get_index()][sn.get_index()][ast]
        tmp.update({en.get_index(): {}})
        tmp_2 = arcs[v.get_index()][sn.get_index()]
        tmp_2[ast].update(tmp)
        tmp_3 = arcs[v.get_index()]
        tmp_3[sn.get_index()].update(tmp_2)
        arcs[v.get_index()] = tmp_3

    tmp = arcs[v.get_index()][sn.get_index()][ast][en.get_index()]
    tmp.update({aet: True})
    tmp_2 = arcs[v.get_index()][sn.get_index()][ast]
    tmp_2[en.get_index()].update(tmp)
    tmp_3 = arcs[v.get_index()][sn.get_index()]
    tmp_3[ast].update(tmp_2)
    tmp_4 = arcs[v.get_index()]
    tmp_4[sn.get_index()].update(tmp_3)
    arcs[v.get_index()] = tmp_4


def print_arcs(arcs):
    counter = 0
    vessel_idx = 0
    for start_node in data.ALL_NODES[:-1]:
        for start_time in arcs[vessel_idx][start_node.get_index()]:
            for end_node in arcs[vessel_idx][start_node.get_index()][start_time]:
                for end_time in arcs[vessel_idx][start_node.get_index()][start_time][end_node]:
                    if arcs[0][start_node.get_index()][start_time][end_node][end_time]:
                        # arc_cost = arc_costs[0][start_node.get_index()][start_time][end_node.get_index()][end_time]
                        # print(f'{start_node} ({start_time}) -> {end_node} ({end_time}): {arc_cost}')
                        print(f'{start_node} ({start_time}) -> {data.ALL_NODES[end_node]} ({end_time})')
                        counter += 1
    print(f'Number of arcs: {counter}')


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
    arc_network = generate_arcs()
    print(f'Runtime: {time.time() - start}')
    print(arc_network)
    print_arcs(arc_network)
