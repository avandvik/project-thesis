import data
import arc_flow.preprocessing.helpers as hlp
from collections import defaultdict as dd

# arcs[vessel][start_node][start_time][end_node][end_time] -> True/False
arcs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: False)))))


def run():
    visit_list = []
    installations = set()
    for node in data.ALL_NODES[1:]:
        if node.get_installation() in installations:
            continue
        if node.get_installation().has_multiple_orders():
            visit_list.append(data.ALL_NODES[node.get_installation().get_most_dominating_order().get_index() + 1])
        else:
            visit_list.append(node)
        installations.add(node.get_installation())

    for vessel in data.VESSELS:
        start_node = data.ALL_NODES[0]
        for not_visited_node in visit_list:
            new_visit_list = visit_list.copy()
            new_visit_list.remove(not_visited_node)
            start_time = data.PREPARATION_END_TIME
            unit(start_node, not_visited_node, new_visit_list, start_time, vessel)
            print('\n\n\n')
        break


def unit(start_node, end_node, visit_list, start_time, vessel):
    # Base cases
    check_base_cases(start_node, end_node, visit_list)

    # Inbound arcs
    print(f'Inbound: {start_node} -> {end_node} ({start_time})')

    # TODO: Perform inbound arc calculations
    inbound_end_times = inbound_arc_calculations(start_node, end_node, start_time, vessel)

    # If end_node is end_depot there will be no internal or outbound arcs
    if end_node.is_end_depot():
        return

    # Internal arcs
    internal_nodes, md_node, od_node, op_node = get_internal_nodes(end_node)
    if md_node and od_node and op_node:
        internal_end_times = internal_arc_calculations([md_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            print(f'Internal: {md_node} ({internal_end_time})')
            generate_outbound_arcs(md_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {md_node} -> {od_node}')
        internal_end_times = internal_arc_calculations([md_node, od_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(od_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {md_node} -> {op_node}')
        internal_end_times = internal_arc_calculations([md_node, op_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(op_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {od_node} -> {op_node}')
        internal_end_times = internal_arc_calculations([md_node, od_node, op_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(op_node, visit_list, internal_end_time, vessel)

    elif md_node and od_node:
        print(f'Internal: {md_node}')
        internal_end_times = internal_arc_calculations([md_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(md_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {md_node} -> {od_node}')
        internal_end_times = internal_arc_calculations([md_node, od_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(od_node, visit_list, internal_end_time, vessel)

    elif md_node and op_node:
        print(f'Internal: {md_node}')
        internal_end_times = internal_arc_calculations([md_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(md_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {md_node} -> {op_node}')
        internal_end_times = internal_arc_calculations([md_node, op_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(op_node, visit_list, internal_end_time, vessel)

    elif od_node and op_node:
        print(f'Internal: {od_node}')
        internal_end_times = internal_arc_calculations([od_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(od_node, visit_list, internal_end_time, vessel)

        print(f'Internal: {od_node} -> {op_node}')
        internal_end_times = internal_arc_calculations([od_node, op_node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(op_node, visit_list, internal_end_time, vessel)

    else:
        node = internal_nodes[0]  # TODO: Double check that there is only one element here
        internal_end_times = internal_arc_calculations([node], inbound_end_times, vessel)
        for internal_end_time in internal_end_times:
            generate_outbound_arcs(node, visit_list, internal_end_time, vessel)


def check_base_cases(start_node, end_node, visit_list):
    if hlp.is_illegal_arc(start_node, end_node):
        return
    if not visit_list:
        return


def get_internal_nodes(end_node):
    orders = end_node.get_installation().get_orders()
    internal_nodes = [data.ALL_NODES[o.get_index() + 1] for o in orders]
    md_node, od_node, op_node = None, None, None
    for internal_node in internal_nodes:
        if internal_node.get_order().is_mandatory_delivery():
            md_node = internal_node
        elif internal_node.get_order().is_optional_delivery():
            od_node = internal_node
        elif internal_node.get_order().is_optional_pickup():
            op_node = internal_node
    return internal_nodes, md_node, od_node, op_node


def inbound_arc_calculations(start_node, end_node, start_time, vessel):
    distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
    early_arrival, late_arrival = hlp.get_arrival_time_span(distance, start_time)
    service_duration = hlp.calculate_service_time(end_node)
    checkpoints, idling = hlp.get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
    arc_costs, arc_end_times, arc_arr_times = hlp.calculate_arc_data(start_time, checkpoints, distance, vessel)
    return arc_end_times


def internal_arc_calculations(internal_nodes, start_times, vessel):
    end_times = []
    for start_time in start_times:
        serv_dur = 0
        for internal_node in internal_nodes:
            if len(internal_nodes) > 1 and internal_node.get_order().is_pickup():
                continue
            serv_dur += hlp.calculate_service_time(internal_node)
        end_node = internal_nodes[-1]
        end_time = start_time + serv_dur
        if hlp.is_return_possible(end_node, end_time, vessel) and hlp.is_servicing_possible(start_time, serv_dur, end_node):
            end_times.append(end_time)
    return end_times


def generate_outbound_arcs(start_node, visit_list, start_time, vessel):
    for not_visited_node in visit_list:
        print(f'Outbound: {start_node} -> {not_visited_node}')
        new_visit_list = visit_list.copy()
        new_visit_list.remove(not_visited_node)
        unit(start_node, not_visited_node, new_visit_list, start_time, vessel)


def print_arcs():
    for start_node in data.ALL_NODES[:-1]:
        for end_node in data.ALL_NODES[1:]:
            for start_time in range(10):
                for end_time in range(10):
                    if arcs[0][start_node.get_index()][start_time][end_node.get_index()][end_time]:
                        print(f'{start_node} ({start_time}) -> {end_node} ({end_time})')


run()
print_arcs()
