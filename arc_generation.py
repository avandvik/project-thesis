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
                min_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT
                max_service_time += order.get_size() * data.REAL_SERVICE_TIME_PER_UNIT * data.SERVICE_IMPACTS[2]

            min_sailing_time = distance / data.MAX_SPEED
            max_sailing_time = distance / data.MIN_SPEED

            early_end = start_time + math.ceil((min_sailing_time + min_service_time) * data.TIME_UNITS_PER_HOUR)
            late_end = start_time + math.ceil((max_sailing_time + max_service_time) * data.TIME_UNITS_PER_HOUR)

            end_time = early_end

            while end_time <= late_end:
                end_time = find_first_feasible_end_time()


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


def find_first_feasible_end_time():
    pass


def servicing_possible(time, orders, installation):
    hours = convert_discretized_time_to_hours(time)
    service_time = 0

    for order in orders:
        cargo_left = order.get_size()
        while cargo_left:
            service_time += data.REAL_SERVICE_TIME_PER_UNIT / get_weather_impact_on_service(hours)
            cargo_left -= 1

            if get_weather_state(hours) == data.WORST_WEATHER_STATE or installation.is_closed(hours):
                return False

            if service_time > 1:
                hours += 1
                service_time = 0

    return True


def convert_discretized_time_to_hours(time):
    return time / data.TIME_UNITS_PER_HOUR


def convert_hours_to_discretized_time(hours):
    return hours * data.TIME_UNITS_PER_HOUR


def get_weather_state(hours):
    return data.WEATHER_FORECAST[hours]


def get_weather_impact_on_service(hours):
    return data.SERVICE_IMPACTS[data.WEATHER_FORECAST[hours]]


def get_weather_impact_on_sailing(hours):
    return data.SPEED_IMPACTS[data.WEATHER_FORECAST[hours]]
