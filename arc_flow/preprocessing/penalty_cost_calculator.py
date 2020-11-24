import data


def calculate_penalty_costs(arc_costs, preparation_end_time):

    nodes_to_visit = []
    for j in data.OPTIONAL_NODE_INDICES:
        optional_node = data.ALL_NODES[j]
        inst = optional_node.get_installation()
        if inst.has_mandatory_order():
            for idx in data.MANDATORY_NODE_INDICES:
                visit_node = data.ALL_NODES[idx]
                if visit_node.get_installation() == inst and visit_node.get_order().is_mandatory():
                    nodes_to_visit.append((optional_node, visit_node))
        elif optional_node.get_order().is_pickup() and inst.has_optional_delivery_order():
            for idx in data.OPTIONAL_NODE_INDICES:
                visit_node = data.ALL_NODES[idx]
                if visit_node.get_installation() == inst and visit_node.get_order().is_delivery():
                    nodes_to_visit.append((optional_node, visit_node))
        else:
            nodes_to_visit.append((optional_node, optional_node))

    penalty_costs = [0 for _ in data.ALL_NODE_INDICES]

    for node in data.ALL_NODES[1:-1]:
        for pair in nodes_to_visit:
            if node == pair[1]:
                service_from_depot_costs = []
                for t in data.TIME_POINTS_DISC:
                    if arc_costs[0][0][preparation_end_time][node.get_index()][t] != 0:
                        service_from_depot_costs.append(arc_costs[0][0][preparation_end_time][node.get_index()][t] * 2)
                worst_cost = max(service_from_depot_costs)
                idx = pair[0].get_index()
                penalty_costs[idx] = worst_cost

    return penalty_costs
