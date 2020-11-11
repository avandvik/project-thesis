import data


def separate_objective(objective_value, variables, arc_costs):
    objective_arc_costs = 0
    objective_load_costs = 0
    for v in variables:
        split_var = v.varName.split('_')
        if v.x > 0.1 and split_var[0] == 'x':
            start_node, start_time, end_node, end_time, vessel = split_var[1:]
            start_node, start_time, end_node, end_time, vessel = int(start_node), int(start_time), int(
                end_node), int(end_time), int(vessel)
            objective_arc_costs += arc_costs[vessel][start_node][start_time][end_node][end_time]
        elif v.x > 0.1 and split_var[0] == 'l':
            objective_load_costs += v.x

    true_objective = objective_value - objective_load_costs
    objective_penalty_costs = true_objective - objective_arc_costs

    return objective_arc_costs, objective_penalty_costs


def print_routes(variables):
    routes = create_routes_variable(variables)
    for vessel in routes.keys():
        print(f'VESSEL {vessel}')
        next_to_destination_node = max(list(routes[vessel].keys()))
        destination_node = routes[vessel][next_to_destination_node][0][1]
        start_node = 0
        end_node = routes[vessel][start_node][0][1]
        while end_node != destination_node:
            start_time, end_time = routes[vessel][start_node][0][0], routes[vessel][start_node][0][2]
            delivery_load, pickup_load = routes[vessel][start_node][1], routes[vessel][start_node][2]
            print(f'\t{start_node} ({start_time}) -> {end_node} ({end_time}) '
                  f'| l_D = {delivery_load} l_P = {pickup_load}')
            start_node = end_node
            end_node = routes[vessel][start_node][0][1]

        start_time, end_time = routes[vessel][start_node][0][0], routes[vessel][start_node][0][2]
        print(f'\t{start_node} ({start_time}) -> {end_node} ({end_time})')


def create_routes_variable(variables):
    routes = {v: {} for v in range(len(data.VESSELS))}
    for v in variables:
        if v.x > 0.1:
            split_var = v.varName.split('_')
            var_name = split_var[0]
            if var_name == 'x':
                start_node, start_time, end_node, end_time, vessel = split_var[1:]
                start_node, start_time, end_node, end_time, vessel = int(start_node), int(start_time), int(
                    end_node), int(end_time), int(vessel)
                routes[vessel].update(
                    {start_node: [(start_time, end_node, end_time), 0, 0]})
            elif var_name == 'l':
                var_type = split_var[1]
                node, vessel = split_var[2:]
                node, vessel = int(node), int(vessel)
                for start_node in routes[vessel].keys():
                    if start_node == node:
                        routes[vessel][start_node][1 if var_type == 'D' else 2] = round(v.x)

    return routes
