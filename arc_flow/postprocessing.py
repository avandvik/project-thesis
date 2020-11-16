import json
import data
from pprint import pprint


def print_nodes_and_orders():
    print('\n\n')
    for idx, node in enumerate(data.ALL_NODES):
        if node.is_order():
            print(f'{idx}: {node} {node.get_order().get_size()}')
        else:
            print(f'{idx}: {node}')
    print('\n')


def separate_objective(objective_value, variables, arc_costs, routes):
    objective_fuel_costs = 0
    objective_charter_costs = 0
    objective_arc_costs = 0
    objective_load_costs = 0
    for v in variables:
        split_var = v.varName.split('_')
        if v.x > 0.1 and split_var[0] == 'x':
            start_node, start_time, end_node, end_time, vessel = split_var[1:]
            start_node, start_time, end_node, end_time, vessel = int(start_node), int(start_time), int(
                end_node), int(end_time), int(vessel)
            objective_fuel_costs += routes[vessel][start_node][-1][0]
            objective_charter_costs += routes[vessel][start_node][-1][1]
            objective_arc_costs += arc_costs[vessel][start_node][start_time][end_node][end_time]
        elif v.x > 0.1 and split_var[0] == 'l':
            objective_load_costs += v.x

    true_objective = objective_value - objective_load_costs
    objective_penalty_costs = true_objective - objective_arc_costs

    return objective_fuel_costs, objective_charter_costs, objective_arc_costs, objective_penalty_costs


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

            if verbose:
                print(f'\t{start_node} ({start_time}) -> {end_node} ({end_time}) '
                      f'| l_D = {delivery_load} l_P = {pickup_load} | sailing speed = {arc_speed}')

            sequence.append((start_node, start_time, end_node, end_time, delivery_load, pickup_load, arc_speed))

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


def create_voyages_variable(variables, arc_arrival_times, sep_arc_costs):
    routes = {v: {} for v in range(len(data.VESSELS))}
    for v in variables:
        if v.x > 0.1:
            split_var = v.varName.split('_')
            var_name = split_var[0]
            if var_name == 'x':
                start_node, start_time, end_node, end_time, vessel = split_var[1:]
                start_node, start_time, end_node, end_time, vessel = int(start_node), int(start_time), int(
                    end_node), int(end_time), int(vessel)
                arrival_time = arc_arrival_times[vessel][start_node][start_time][end_node][end_time]
                fuel_cost, charter_cost = sep_arc_costs[vessel][start_node][start_time][end_node][end_time]
                routes[vessel].update(
                    {start_node: [end_node, (start_time, arrival_time, end_time), [0, 0], (fuel_cost, charter_cost)]})
            elif var_name == 'l':
                var_type = split_var[1]
                node, vessel = split_var[2:]
                node, vessel = int(node), int(vessel)
                for start_node in routes[vessel].keys():
                    if start_node == node:
                        routes[vessel][start_node][2][0 if var_type == 'D' else 1] = v.x
    return routes


def find_postponed_orders(voyages):
    all_orders = set()
    for order_node in data.ALL_NODE_INDICES[1:-1]:
        all_orders.add(order_node)

    serviced_orders = set()
    for vessel in voyages.keys():
        for start_node in voyages[vessel].keys():
            if data.ALL_NODES[start_node].is_order():
                serviced_orders.add(start_node)

    not_serviced_orders = all_orders.difference(serviced_orders)

    return not_serviced_orders, serviced_orders


def save_results_new(voyages, postponed_orders, serviced_orders, preprocess_runtime, model_runtime, fuel_costs,
                     charter_costs, penalty_costs, output_path):
    results = {}
    results.update({'instance_info': {}})
    results['instance_info'].update({'installation_ordering': data.INSTALLATION_ORDERING,
                                     'number_of_installations': data.NUMBER_OF_INSTALLATIONS_WITH_ORDERS,
                                     'weather_scenario': data.WEATHER_SCENARIO,
                                     'fleet_size': data.FLEET_SIZE,
                                     'order_composition': {}})
    for order_number, order_node in enumerate(data.ALL_NODES[1:-1]):
        results['instance_info']['order_composition'].update({order_number + 1: {}})
        results['instance_info']['order_composition'][order_number + 1].update(
            {'order': order_node.generate_representation(),
             'size': order_node.get_order().get_size(),
             'installation': order_node.get_installation().get_index()})
    results.update({'voyages': voyages})
    results.update({'order_fulfillment': {'postponed_orders': list(postponed_orders),
                                          'serviced_orders': list(serviced_orders)}})
    results.update({'objective': {'fuel_costs': fuel_costs,
                                  'charter_costs': charter_costs,
                                  'penalty_costs': penalty_costs}})
    results.update({'runtime': {'preprocess_runtime': preprocess_runtime,
                                'model_runtime': model_runtime}})
    with open(output_path, 'w') as ofp:
        json.dump(results, ofp)


def print_objective(objective, arc_costs, penalty_costs, verbose):
    if verbose:
        print(f'Objective: {objective}'
              f'\n\tArc costs: {arc_costs}'
              f'\n\tPenalty costs: {penalty_costs}')
