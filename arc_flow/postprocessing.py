import json
import data


def print_nodes_and_orders():
    print('\n\n')
    for idx, node in enumerate(data.ALL_NODES):
        if node.is_order():
            print(f'{idx}: {node} {node.get_order().get_size()}')
        else:
            print(f'{idx}: {node}')
    print('\n')


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


def print_routes_and_get_sequence(variables, arc_speeds, verbose):
    routes = create_routes_variable(variables)
    sequences = {}
    for vessel in routes.keys():
        sequence = []

        if verbose:
            print(f'VESSEL {vessel}')

        next_to_destination_node = max(list(routes[vessel].keys()))
        destination_node = routes[vessel][next_to_destination_node][0][1]
        start_node = 0
        end_node = routes[vessel][start_node][0][1]
        while end_node != destination_node:
            start_time, end_time = routes[vessel][start_node][0][0], routes[vessel][start_node][0][2]
            delivery_load, pickup_load = routes[vessel][start_node][1], routes[vessel][start_node][2]
            arc_speed = arc_speeds[vessel][start_node][start_time][end_node][end_time]

            sequence.append((start_node, start_time, end_node, end_time, delivery_load, pickup_load, arc_speed))
            if verbose:
                print(f'\t{start_node} ({start_time}) -> {end_node} ({end_time}) '
                      f'| l_D = {delivery_load} l_P = {pickup_load} | sailing speed = {arc_speed}')

            start_node = end_node
            end_node = routes[vessel][start_node][0][1]

        start_time, end_time = routes[vessel][start_node][0][0], routes[vessel][start_node][0][2]
        delivery_load, pickup_load = routes[vessel][start_node][1], routes[vessel][start_node][2]
        arc_speed = arc_speeds[vessel][start_node][start_time][end_node][end_time]

        if verbose:
            print(f'\t{start_node} ({start_time}) -> {end_node} ({end_time}) | sailing speed = {arc_speed}')

        sequence.append((start_node, start_time, 0, end_time, delivery_load, pickup_load, arc_speed))

        sequences.update({vessel: sequence})

    return sequences


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
                        routes[vessel][start_node][1 if var_type == 'D' else 2] = v.x
    return routes


def print_objective(objective, arc_costs, penalty_costs, verbose):
    if verbose:
        print(f'Objective: {objective}'
              f'\n\tArc costs: {arc_costs}'
              f'\n\tPenalty costs: {penalty_costs}')


def save_results(vessel_sequences, arc_costs, penalty_costs, preprocess_runtime, model_runtime, output_path):
    results = {'vessel_sequences': {}}
    for vessel in vessel_sequences.keys():
        results['vessel_sequences'].update({vessel: vessel_sequences[vessel]})

    results.update({'objective_info': {}})
    results['objective_info'].update({'arc_costs': arc_costs,
                                      'penalty_costs': penalty_costs})

    results.update({'instance_info': {}})
    results['instance_info'].update({'installation_ordering': data.INSTALLATION_ORDERING,
                                     'number_of_installations_with_orders': data.NUMBER_OF_INSTALLATIONS_WITH_ORDERS,
                                     'weather_scenario': data.WEATHER_SCENARIO,
                                     'fleet_size': data.FLEET_SIZE,
                                     'order_composition': {}})

    for order_number, order_node in enumerate(data.ALL_NODES[1:-1]):
        results['instance_info']['order_composition'].update({str(order_number): {}})
        results['instance_info']['order_composition'][str(order_number)].update(
            {'order': order_node.generate_representation(),
             'size': order_node.get_order().get_size()})

    results.update({'runtime_info': {}})
    results['runtime_info'].update({'preprocess_runtime': preprocess_runtime,
                                    'model_runtime': model_runtime})

    with open(output_path, 'w') as ofp:
        json.dump(results, ofp)
