import data
import math


def generate_all_arcs(earliest_end_time, latest_end_time):
    # Add depot node for all vessels
    nodes = {vessel: {0: {earliest_end_time: True}} for vessel in data.vessels}
    for installation in data.installations:
        for end_time in range(earliest_end_time, latest_end_time):
            for vessel in data.vessels:
                if nodes[installation.identifier][end_time][vessel.identifier]:
                    generate_arcs_from_node(installation, end_time, vessel)


def generate_arcs_from_node(dep_inst, start_time, vessel):
    for dest_inst in data.installations:

        if dest_inst.identifier == dep_inst.identifier or not dest_inst.has_orders():
            continue

        distance = dep_inst.get_distance_to_installation(dest_inst.identifier)

        # TODO: Add real start time if needed

        order_combinations = create_order_combinations(dest_inst.get_orders())

        for order_combination in order_combinations:

            min_service_time, max_service_time = 0, 0
            for order in order_combination:
                min_service_time += order.get_size() * data.SERVICE_TIME_PER_UNIT
                max_service_time += order.get_size() * data.SERVICE_TIME_PER_UNIT * 1.3  # TODO: Find out why 1.3 is used

            min_sailing_time = distance / data.MAX_SPEED
            max_sailing_time = distance / data.MIN_SPEED

            early_end = start_time + math.ceil((min_sailing_time + min_service_time) * data.TIME_UNITS_PER_HOUR)
            late_end = start_time + math.ceil((max_sailing_time + max_service_time) * data.TIME_UNITS_PER_HOUR)


def add_arc():
    pass


def create_order_combinations(orders):
    combinations = []
    for order_one in orders:
        for other_order in orders:
            if order_one.index == other_order.index:
                combinations.append({order_one})
                continue
            combinations.append({order_one, other_order})
    return combinations
