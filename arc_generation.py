import data
import math
import helpers
from collections import defaultdict
from itertools import combinations


def generate_all_arcs(operation_start_time):
    nodes = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: False)))
    arc_costs = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))))

    # Add depot node for all vessels
    for vessel in data.VESSELS:
        nodes[vessel.index][operation_start_time][0] = True

    for vessel in data.VESSELS:
        print(f'Generating network of arcs for vessel {vessel}')
        for installation in data.INSTALLATIONS:
            for start_time in range(operation_start_time, vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR):
                if nodes[vessel.get_index()][start_time][installation.get_index()]:
                    print(f'    Generating arcs from node {installation}')
                    generate_arcs_from_node(vessel, start_time, installation, nodes, arc_costs)

                # Early return to only consider one network of arcs
                return


def generate_arcs_from_node(vessel, departure_time, dep_inst, nodes, arc_costs):
    for dest_inst in data.INSTALLATIONS:
        if dest_inst.get_index() == dep_inst.get_index() or not dest_inst.has_orders():
            continue

        print(f'        Considering node {dest_inst}')

        distance = dep_inst.get_distance_to_installation(dest_inst.get_index())
        print(f'        Distance {distance}')
        order_combinations = combine_orders([data.ORDERS[order_index] for order_index in dest_inst.get_orders()])

        for orders in order_combinations:
            early_end, late_end = calculate_end_time_span(departure_time, distance, orders)
            print(f'            End time span {early_end} -> {late_end}')
            service_end_time = early_end

            while service_end_time <= late_end:
                print(f'                Departure time (disc) {departure_time} | Service end time (disc) {service_end_time}')
                print(f'                Weather {data.WEATHER_FORECAST[departure_time:service_end_time]}')
                service_end_time, service_duration = calculate_servicing_times(service_end_time, orders, dest_inst)
                service_start_time = service_end_time - service_duration
                print(f'                    Service start time (disc) {service_start_time}')

                if is_arrival_possible(departure_time, distance, service_start_time):

                    sailing_end_time, idling_duration = calculate_idling_times(departure_time, distance,
                                                                               service_start_time)

                    print(f'                Sailing end time {sailing_end_time} | Idling duration {idling_duration} | Service start time {service_start_time} | Service end time {service_end_time}')

                    fuel_cost_sailing = calcuate_fuel_cost_sailing(departure_time, sailing_end_time, distance)
                    fuel_cost_idling = calculate_fuel_cost_idling(sailing_end_time, service_start_time)
                    fuel_cost_servicing = calculate_fuel_cost_servicing(service_start_time, service_end_time)
                    total_fuel_cost = fuel_cost_sailing + fuel_cost_idling + fuel_cost_servicing

                    add_arc(vessel, dep_inst, dest_inst, departure_time, service_end_time, total_fuel_cost, nodes,
                            arc_costs)

                print()

                service_end_time += 1


def combine_orders(orders):
    return [comb for sublist in list(combinations(orders, r) for r in range(1, len(orders) + 1)) for comb in sublist]


def calculate_end_time_span(departure_time, distance, order_combination):
    """Calculates the earliest time (discretized scale) service can be finished to the latest it can be finished"""
    min_service_time, max_service_time = 0, 0
    for order in order_combination:
        min_service_time += order.get_size() * data.HOURLY_SERVICE_TIME_PER_UNIT
        max_service_time += order.get_size() * data.HOURLY_SERVICE_TIME_PER_UNIT * data.SERVICE_IMPACTS[2]

    min_sailing_time = distance / data.MAX_SPEED
    max_sailing_time = distance / data.MIN_SPEED

    # TODO: What about potential idling time?

    # NB! Note that the discretization is handled here
    early_end = departure_time + math.ceil((min_sailing_time + min_service_time) * data.TIME_UNITS_PER_HOUR)
    late_end = departure_time + math.ceil((max_sailing_time + max_service_time) * data.TIME_UNITS_PER_HOUR)

    return early_end, late_end


def calculate_servicing_times(service_end_time, orders, installation):
    """Calculates earliest feasible servicing end time and service time given weather and opening hours"""
    hourly_time = helpers.convert_discretized_time_to_hourly_time(service_end_time)
    print(f'                    Service end time (hourly) {hourly_time}')
    time_of_day = helpers.convert_hourly_time_to_time_of_day(hourly_time)
    print(f'                    Service end time (daytime) {time_of_day}')

    service_time, hours_passed = 0, 1

    for order in orders:
        cargo_left = order.get_size()
        while cargo_left:
            if not is_servicing_possible(hourly_time, time_of_day, installation):
                return calculate_servicing_times(service_end_time + 1, orders, installation)

            cargo_left -= 1
            service_time += data.HOURLY_SERVICE_TIME_PER_UNIT * helpers.get_weather_impact_on_service(hourly_time)

            if service_time > hours_passed:
                hourly_time -= 1
                time_of_day = helpers.convert_hourly_time_to_time_of_day(hourly_time)
                hours_passed += 1

    service_duration = helpers.convert_hourly_time_to_discretized_time(service_time)
    print(f'                    Service duration (disc) {service_duration}')
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
    """Calculate the minimal idling time, given that a vessel sails at the minimum speed"""
    max_sailing_duration = distance / data.MIN_SPEED

    idling_duration = max(0, service_start_time - (departure_time + max_sailing_duration))
    sailing_end_time = service_start_time - idling_duration

    print(f'                    Idling duration (disc) {idling_duration}')
    print(f'                    Sailing end time (disc) {sailing_end_time}')

    return sailing_end_time, idling_duration


def calcuate_fuel_cost_sailing(departure_time, sailing_end_time, distance):
    """Adjusts the speeds such that no max sailing speed limit in any weather state is broken"""
    speed = distance / (sailing_end_time - departure_time)
    speed_in_each_weather_state = [speed for _ in range(data.WORST_WEATHER_STATE + 1)]
    time_in_each_ws = helpers.get_time_in_each_weather_state(departure_time, sailing_end_time)

    illegal_distance = calculate_illegal_distance(time_in_each_ws, speed, speed_in_each_weather_state)
    distribute_illegal_distance(illegal_distance, time_in_each_ws, speed_in_each_weather_state)

    # Calculate the fuel cost given the speed in each weather state
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * get_consumption(speed_in_each_weather_state[ws] + data.SPEED_IMPACTS[ws])

    return cost


def calculate_illegal_distance(time_in_each_ws, speed, speed_in_each_weather_state):
    """Calculate the distance sailed due to a speed limit violation in a weather state"""
    illegal_distance = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        max_speed_in_ws = data.MAX_SPEED - data.SPEED_IMPACTS[ws]

        if speed > max_speed_in_ws:
            illegal_distance += time_in_each_ws[ws] * (speed - max_speed_in_ws)
            speed_in_each_weather_state[ws] = max_speed_in_ws

    return illegal_distance


def distribute_illegal_distance(illegal_distance, time_in_each_ws, speed_in_each_weather_state):
    """Distribute the illegally sailed distance on the better weather states"""
    ws = data.BEST_WEATHER_STATE
    while illegal_distance > 0:
        max_distance = (time_in_each_ws[ws] * speed_in_each_weather_state[ws]) + illegal_distance
        max_speed_in_ws = data.MAX_SPEED - data.SPEED_IMPACTS[ws]
        max_speed = max_distance / time_in_each_ws[ws]
        speed_in_each_weather_state[ws] = max_speed if max_speed <= max_speed_in_ws else max_speed_in_ws
        ws += 1


def calculate_fuel_cost_idling(idling_start_time, idling_end_time):
    time_in_each_ws = helpers.get_time_in_each_weather_state(idling_start_time, idling_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SPEED_IMPACTS[ws] * data.FUEL_CONSUMPTION_IDLING * data.FUEL_PRICE
    return cost


def calculate_fuel_cost_servicing(servicing_start_time, servicing_end_time):
    time_in_each_ws = helpers.get_time_in_each_weather_state(servicing_start_time, servicing_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_DEPOT * data.FUEL_PRICE
    return cost


def get_consumption(speed):
    return 11.111 * speed * speed - 177.78 * speed + 1011.1


def add_arc(vessel, dep_inst, dest_inst, start_time, end_time, fuel_cost, nodes, arc_costs):
    if end_time <= vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR:
        charter_cost = data.SPOT_HOUR_RATE * helpers.convert_discretized_time_to_hourly_time(
            end_time - start_time) if vessel.is_spot_vessel() else 0.0

        nodes[vessel.get_index()][end_time][dest_inst.get_index()] = True

        arc_cost = fuel_cost + charter_cost
        arc_costs[vessel.get_index()][dep_inst.get_index()][start_time][dest_inst.get_index()][end_time] = arc_cost


if __name__ == '__main__':
    generate_all_arcs(16 * data.TIME_UNITS_PER_HOUR)
