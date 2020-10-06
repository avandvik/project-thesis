import data
import math
from collections import defaultdict
from itertools import combinations


def generate_all_arcs(operation_start_time):
    nodes = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: False)))

    # Add depot node for all vessels
    for vessel in data.vessels:
        nodes[vessel.identifier][operation_start_time][0] = True

    for vessel in data.vessels:
        print(vessel)
        for installation in data.installations:
            for start_time in range(operation_start_time, vessel.get_real_return_time()*data.TIME_UNITS_PER_HOUR):

                if nodes[vessel.identifier][start_time][installation.identifier]:
                    generate_arcs_from_node(vessel, start_time, installation)


def generate_arcs_from_node(vessel, start_time, dep_inst):
    for dest_inst in data.installations:

        if dest_inst.identifier == dep_inst.identifier or not dest_inst.has_orders():
            continue

        distance = dep_inst.get_distance_to_installation(dest_inst.identifier)

        # TODO: Add real start time if needed

        orders = [data.orders[order_index] for order_index in dest_inst.get_orders()]
        order_combinations = get_order_combinations(orders)

        for order_combination in order_combinations:

            min_service_time, max_service_time = 0, 0
            for order in order_combination:
                min_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT
                max_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT * data.SERVICE_IMPACTS[2]

            min_sailing_time = distance / data.MAX_SPEED
            max_sailing_time = distance / data.MIN_SPEED

            early_end = start_time + math.ceil((min_sailing_time + min_service_time) * data.TIME_UNITS_PER_HOUR)
            late_end = start_time + math.ceil((max_sailing_time + max_service_time) * data.TIME_UNITS_PER_HOUR)

            end_time = early_end

            break_counter = 0
            while end_time <= late_end:
                end_time = find_first_feasible_end_time(end_time, order_combination, dest_inst)



                break_counter += 1
                if break_counter == 10:
                    break


def add_arc():
    pass


def get_order_combinations(orders):
    return [comb for sublist in list(combinations(orders, r) for r in range(1, len(orders)+1)) for comb in sublist]


def find_first_feasible_end_time(end_time, orders, installation):
    first_feasible_end_time = end_time
    if not servicing_possible(first_feasible_end_time, orders, installation):
        first_feasible_end_time = find_first_feasible_end_time(first_feasible_end_time+1, orders, installation)
    return first_feasible_end_time


def servicing_possible(end_time, orders, installation):
    hours = convert_discretized_time_to_hours(end_time)
    service_time = 0

    for order in orders:
        cargo_left = order.get_size()
        while cargo_left:
            service_time += data.REAL_SERVICE_TIME_PER_UNIT / get_weather_impact_on_service(hours)
            cargo_left -= 1

            if get_weather_state(hours) == data.WORST_WEATHER_STATE or installation.is_closed(hours):
                return False

            if service_time > 1:
                hours -= 1
                service_time = 0

    return True


def convert_discretized_time_to_hours(time):
    return math.floor(time / data.TIME_UNITS_PER_HOUR)


def convert_hours_to_discretized_time(hours):
    return hours * data.TIME_UNITS_PER_HOUR


def get_weather_state(hours):
    return data.WEATHER_FORECAST[hours]


def get_weather_impact_on_service(hours):
    return data.SERVICE_IMPACTS[data.WEATHER_FORECAST[hours]]


def get_weather_impact_on_sailing(hours):
    return data.SPEED_IMPACTS[data.WEATHER_FORECAST[hours]]


if __name__ == '__main__':
    operation_start_time = 16 * data.TIME_UNITS_PER_HOUR
    generate_all_arcs(operation_start_time)
