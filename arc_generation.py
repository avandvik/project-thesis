import data
import math
import helpers
from collections import defaultdict
from itertools import combinations


def generate_all_arcs(operation_start_time):
    nodes = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: False)))
    arc_costs = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))))

    # Add depot node for all vessels
    for vessel in data.VESSELS:
        nodes[vessel.index][operation_start_time][0] = True

    for vessel in data.VESSELS:
        for installation in data.INSTALLATIONS:
            for start_time in range(operation_start_time, vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR):
                if nodes[vessel.index][start_time][installation.index]:
                    generate_arcs_from_node(vessel, start_time, installation, nodes, arc_costs)


def generate_arcs_from_node(vessel, departure_time, dep_inst, nodes, arc_costs):
    for dest_inst in data.INSTALLATIONS:
        if dest_inst.get_index() == dep_inst.get_index() or not dest_inst.has_orders():
            continue

        distance = dep_inst.get_distance_to_installation(dest_inst.index)
        order_combinations = combine_orders([data.ORDERS[order_index] for order_index in dest_inst.get_orders()])

        for orders in order_combinations:
            early_end, late_end = calculate_end_time_span(departure_time, distance, orders)
            service_end_time = early_end

            while service_end_time <= late_end:
                service_end_time, service_duration = calculate_servicing_times(service_end_time, orders, dest_inst)
                idling_end_time = service_end_time - service_duration

                if is_arrival_possible(departure_time, distance, idling_end_time):
                    sailing_end_time, idling_duration = calculate_idling_times(departure_time, distance,
                                                                               idling_end_time)

                    print('Arc generated!')

                # Calculate total fuel consumption

                # Calculate adjusted average speed

                service_end_time += 1


def combine_orders(orders):
    return [comb for sublist in list(combinations(orders, r) for r in range(1, len(orders) + 1)) for comb in sublist]


def calculate_end_time_span(departure_time, distance, order_combination):
    """Calculates the earliest time (discretized scale) service can be finished to the latest it can be finished"""
    min_service_time, max_service_time = 0, 0
    for order in order_combination:
        min_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT
        max_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT * data.SERVICE_IMPACTS[2]

    min_sailing_time = distance / data.MAX_SPEED
    max_sailing_time = distance / data.MIN_SPEED

    # TODO: What about potential idling time?

    # NB! Note that the discretization is handled here
    early_end = departure_time + math.ceil((min_sailing_time + min_service_time) * data.TIME_UNITS_PER_HOUR)
    late_end = departure_time + math.ceil((max_sailing_time + max_service_time) * data.TIME_UNITS_PER_HOUR)

    return early_end, late_end


def calculate_servicing_times(service_end_time, orders, installation):
    """Calculates earliest feasible servicing end time and service time given weather and opening hours"""
    time_of_day = helpers.convert_discretized_time_to_time_of_day(service_end_time)
    hourly_time = helpers.convert_discretized_time_to_hourly_time(service_end_time)
    service_time, hours_passed = 0, 1

    for order in orders:
        cargo_left = order.get_size()
        while cargo_left:
            if not is_servicing_possible(hourly_time, time_of_day, installation):
                return calculate_servicing_times(service_end_time + 1, orders, installation)

            cargo_left -= 1
            service_time += data.REAL_SERVICE_TIME_PER_UNIT * helpers.get_weather_impact_on_service(hourly_time)

            if service_time > hours_passed:
                hourly_time -= 1
                hours_passed += 1

    service_duration = helpers.convert_hourly_time_to_discretized_time(service_time)
    return service_end_time, service_duration


def is_servicing_possible(hourly_time, time_of_day, installation):
    """Returns whether an installation is open and the weather good enough to perform servicing"""
    if helpers.get_weather_state(hourly_time) == data.WORST_WEATHER_STATE or not installation.is_open(time_of_day):
        open_or_closed = 'open' if installation.is_open(time_of_day) else 'closed'
        weather = 'worst' if helpers.get_weather_state(hourly_time) == data.WORST_WEATHER_STATE else 'good enough'
        print(f'Servicing not possible. Weather is {weather}, installation is {open_or_closed}')

        return False

    return True


def is_arrival_possible(departure_time, distance, service_start_time):
    """Returns whether arrival is possible if a vessel sails at max speed in the given weather conditions"""
    hourly_departure_time = helpers.convert_discretized_time_to_hourly_time(departure_time)
    hourly_service_start_time = helpers.convert_discretized_time_to_hourly_time(service_start_time)

    time_in_each_weather_state = helpers.get_time_in_each_weather_state(hourly_departure_time,
                                                                        hourly_service_start_time)

    max_travel_distance = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        max_travel_distance += time_in_each_weather_state[ws] * (data.MAX_SPEED - data.SPEED_IMPACTS[ws])

    if max_travel_distance >= distance:
        return True

    return False


def calculate_idling_times(departure_time, distance, service_start_time):
    max_sailing_time = distance / data.MIN_SPEED

    if max_sailing_time >= service_start_time - departure_time:
        idling_duration = 0
        sailing_end_time = service_start_time
    else:
        idling_duration = service_start_time - max_sailing_time - departure_time
        sailing_end_time = service_start_time - idling_duration

    return sailing_end_time, idling_duration


def add_arc(vessel, dep_inst, dest_inst, start_time, end_time, consumptions, nodes, arc_costs):
    if end_time <= vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR:
        charter_cost = data.SPOT_HOUR_RATE * helpers.convert_discretized_time_to_hourly_time(
            end_time - start_time) if vessel.is_spot_vessel() else 0.0

        nodes[vessel.get_index()][end_time][dest_inst.get_index()] = True

        arc_cost = sum(consumptions) * data.FUEL_PRICE + charter_cost
        arc_costs[vessel.get_index()][dep_inst.get_index()][start_time][dest_inst.get_index()][end_time] = arc_cost


if __name__ == '__main__':
    operation_start_time = 16 * data.TIME_UNITS_PER_HOUR
    generate_all_arcs(operation_start_time)
