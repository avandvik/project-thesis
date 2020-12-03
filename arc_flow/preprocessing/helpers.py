import data
import math
import numpy as np


def get_start_times(start_node, vessel):
    dist_from_dep = data.DEPOT.get_distance_to_installation(start_node.get_installation())
    earliest_start_time = data.PREPARATION_END_TIME + get_min_sailing_duration(dist_from_dep)

    if start_node.is_start_depot():
        return [earliest_start_time]

    latest_start_time = data.PERIOD_DISC
    while not is_return_possible(start_node, latest_start_time, vessel):
        latest_start_time -= 1

    opening_hours = start_node.get_installation().get_opening_hours_as_list()

    start_times = []
    disc_opening_hours = get_disc_time_interval(opening_hours[0], opening_hours[-1])
    for start_time in range(earliest_start_time, latest_start_time + 1):
        disc_daytime = disc_to_disc_daytime(start_time)
        if disc_daytime not in disc_opening_hours or data.WEATHER_FORECAST_DISC[start_time+1] == 3:
            continue
        start_times.append(start_time)
    return start_times


def is_illegal_arc(start_node, end_node):
    if start_node.is_start_depot() and end_node.is_end_depot():
        return False
    if start_node.get_index() == end_node.get_index():
        return True
    if start_node.get_installation() != end_node.get_installation():
        if end_node.get_installation().has_mandatory_order() and end_node.get_order().is_optional():
            return True
        elif end_node.get_installation().has_optional_delivery_order() and end_node.get_order().is_optional_pickup():
            return True
    else:
        if start_node.get_order().is_optional_delivery():
            if end_node.get_order().is_mandatory_delivery():
                return True
        elif start_node.get_order().is_optional_pickup():
            return True
    return False


def get_arc_data(start_node, end_node, start_time, vessel):
    if start_node.get_installation() != end_node.get_installation():
        arr_times_to_arc_data, idling = get_intermediate_arc_data(start_node, end_node, start_time, vessel)
    elif start_node.is_start_depot() and end_node.is_end_depot():
        return {start_time: [start_time, start_time, 0, 0, 0]}, False
    else:
        arr_times_to_arc_data, idling = get_internal_arc_data(end_node, start_time, vessel)

    if not arr_times_to_arc_data:
        return None, False

    return arr_times_to_arc_data, idling


def get_intermediate_arc_data(start_node, end_node, start_time, vessel):
    distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
    speeds = get_possible_speeds(distance, start_time)
    if not speeds:
        return None, False

    arr_times_to_speeds = get_arr_times_to_speeds(distance, start_time, speeds)
    service_duration = calculate_service_time(end_node)

    arr_times_to_arc_data, idling = get_arr_times_to_arc_data(start_time, arr_times_to_speeds, service_duration,
                                                              end_node, distance, vessel)
    return arr_times_to_arc_data, idling


def get_internal_arc_data(end_node, start_time, vessel):
    service_duration = calculate_service_time(end_node)
    end_time = start_time + service_duration
    if is_return_possible(end_node, end_time, vessel) and is_servicing_possible(start_time, service_duration, end_node):
        speed, arr_time, service_time, distance = 0, start_time, start_time, 0
        fuel_cost, charter_cost = calculate_arc_cost_v2(start_time, arr_time, service_time, end_time, speed,
                                                        distance, vessel)
        return {start_time: [start_time, end_time, speed, fuel_cost, charter_cost]}, False
    else:
        return None, False


def get_possible_speeds(distance, start_time):
    if not data.SPEED_OPTIMIZATION:
        return [data.DESIGN_SPEED]

    max_duration = math.ceil(hour_to_disc(distance / data.MIN_SPEED))  # ceil because we want upper limit
    if max_duration == 0:
        return None
    weather_states = data.WEATHER_FORECAST_DISC[start_time:start_time + max_duration]
    max_speeds = [data.MAX_SPEED - data.SPEED_IMPACTS[ws] for ws in weather_states]
    avg_max_speed = sum(max_speeds) / len(max_speeds)
    speeds = [float(speed) for speed in np.arange(data.MIN_SPEED, data.MAX_SPEED, 1) if speed < avg_max_speed]
    speeds.append(float(avg_max_speed))
    return speeds


def get_arr_times_to_speeds(distance, start_time, speeds):
    arr_times_to_speeds = {}
    speeds.reverse()
    for speed in speeds:
        arr_time = start_time + math.floor(hour_to_disc(distance / speed))
        if arr_time not in arr_times_to_speeds or speed < arr_times_to_speeds[arr_time]:
            arr_times_to_speeds.update({arr_time: speed})
    return arr_times_to_speeds


def get_min_sailing_duration(distance):
    return math.ceil(hour_to_disc(distance / data.MAX_SPEED))


def calculate_service_time(node):
    if node.is_end_depot():
        return 0
    elif node.get_order().is_optional_pickup():
        return 1
    else:
        return math.ceil(node.get_order().get_size() * data.UNIT_SERVICE_TIME_DISC)


def get_arr_times_to_arc_data(start_time, arr_times_to_speeds, service_duration, end_node, distance, vessel):
    if end_node.is_end_depot():
        arr_times_to_arc_data = get_return_to_depot_arcs(start_time, arr_times_to_speeds, distance, vessel)
        return arr_times_to_arc_data, False

    arr_times_to_arc_data = get_no_idling_arcs(start_time, arr_times_to_speeds, service_duration, end_node, distance,
                                               vessel)
    """
    limit = 4
    if len(arr_times_to_arc_data.keys()) > limit:
        number_to_remove = len(arr_times_to_arc_data.keys()) - limit
        while number_to_remove > 0:
            remove_idx = math.floor(len(arr_times_to_arc_data.keys()) / 2)
            remove_key = list(arr_times_to_arc_data.keys())[remove_idx]
            del arr_times_to_arc_data[remove_key]
            number_to_remove -= 1
    """

    if arr_times_to_arc_data.keys():
        return arr_times_to_arc_data, False

    arr_times_to_arc_data = get_idling_arcs(start_time, arr_times_to_speeds, service_duration, end_node, distance,
                                            vessel)
    if arr_times_to_arc_data.keys():
        return arr_times_to_arc_data, True

    return None, None


def get_return_to_depot_arcs(start_time, arr_times_to_speeds, distance, vessel):
    arr_times_to_arc_data = {}
    return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR - 1
    for arr_time, speed in arr_times_to_speeds.items():
        if arr_time <= return_time:
            fuel_cost, charter_cost = calculate_arc_cost_v2(start_time, arr_time, arr_time, arr_time, speed,
                                                            distance, vessel)
            arr_times_to_arc_data.update({arr_time: [arr_time, arr_time, speed, fuel_cost, charter_cost]})
    return arr_times_to_arc_data


def get_no_idling_arcs(start_time, arr_times_to_speeds, service_duration, end_node, distance, vessel):
    arr_times_to_arc_data = {}
    for arr_time, speed in arr_times_to_speeds.items():
        if not is_return_possible(end_node, arr_time + service_duration, vessel):
            break
        if is_servicing_possible(arr_time, service_duration, end_node):
            service_time = arr_time
            end_time = service_time + service_duration
            fuel_cost, charter_cost = calculate_arc_cost_v2(start_time, arr_time, service_time, end_time, speed,
                                                            distance, vessel)
            arr_times_to_arc_data.update({arr_time: [service_time, end_time, speed, fuel_cost, charter_cost]})
    return arr_times_to_arc_data


def get_idling_arcs(start_time, arr_times_to_speeds, service_duration, end_node, distance, vessel):
    arr_times_to_arc_data = {}
    for arr_time, speed in arr_times_to_speeds.items():
        service_time = arr_time
        while service_time < vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR - service_duration and \
                not is_servicing_possible(service_time, service_duration, end_node):
            service_time += 1
        if not is_return_possible(end_node, service_time + service_duration, vessel):
            break
        end_time = service_time + service_duration
        fuel_cost, charter_cost = calculate_arc_cost_v2(start_time, arr_time, service_time, end_time, speed, distance,
                                                        vessel)
        arr_times_to_arc_data.update({arr_time: [service_time, end_time, speed, fuel_cost, charter_cost]})
    return arr_times_to_arc_data


def is_servicing_possible(service_start_time, service_duration, end_node):
    worst_weather = max(data.WEATHER_FORECAST_DISC[service_start_time:service_start_time + service_duration])
    opening_hours = end_node.get_installation().get_opening_hours_as_list()
    disc_opening_time = max(0, hour_to_disc(opening_hours[0]) - 1)
    disc_closing_time = hour_to_disc(opening_hours[-1]) - 1
    installation_open = True
    if disc_opening_time != 0 and disc_closing_time != data.TIME_UNITS_24:
        start_daytime = disc_to_disc_daytime(service_start_time)
        end_daytime = disc_to_disc_daytime(service_start_time + service_duration)
        if start_daytime > disc_closing_time or start_daytime < disc_opening_time or \
                end_daytime > disc_closing_time or end_daytime < disc_opening_time:
            installation_open = False
    return installation_open and worst_weather < data.WORST_WEATHER_STATE


def is_return_possible(node, arc_end_time, vessel):
    distance = node.get_installation().get_distance_to_installation(data.DEPOT)
    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[arc_end_time:]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]
    if len(adjusted_max_speeds) == 0:
        return False
    avg_max_speed = sum(adjusted_max_speeds) / len(adjusted_max_speeds)
    earliest_arr_time = arc_end_time + hour_to_disc(distance / avg_max_speed)
    return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR - 1
    return earliest_arr_time <= return_time


def calculate_arc_cost_v2(start_time, arr_time, service_time, end_time, speed, distance, vessel):
    return calculate_total_fuel_cost_v2(start_time, arr_time, service_time, end_time, speed, distance), \
           calculate_charter_cost(vessel, start_time, end_time)


def calculate_total_fuel_cost_v2(start_time, arr_time, service_time, end_time, speed, distance):
    sail_cost = calculate_fuel_cost_sailing_v2(start_time, arr_time, speed, distance)
    idle_cost = calculate_fuel_cost_idling(arr_time, service_time)
    service_cost = calculate_fuel_cost_servicing(service_time, end_time)
    total_cost = sail_cost + idle_cost + service_cost
    return total_cost


def calculate_fuel_cost_sailing_v2(start_time, arr_time, speed, distance):
    if distance == 0 or start_time == arr_time:
        return 0
    time_in_each_ws = get_time_in_each_weather_state(start_time, arr_time)
    distance_in_each_ws = [speed * time_in_each_ws[ws] for ws in range(4)]
    consumption = get_fuel_consumption(distance_in_each_ws[0] + distance_in_each_ws[1], speed, 0) \
                  + get_fuel_consumption(distance_in_each_ws[2], speed, 2) \
                  + get_fuel_consumption(distance_in_each_ws[3], speed, 3)
    return consumption * data.FUEL_PRICE


def calculate_fuel_cost_idling(idling_start_time, idling_end_time):
    time_in_each_ws = get_time_in_each_weather_state(idling_start_time, idling_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_IDLING * data.FUEL_PRICE
    return cost


def calculate_fuel_cost_servicing(servicing_start_time, servicing_end_time):
    time_in_each_ws = get_time_in_each_weather_state(servicing_start_time, servicing_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] \
                * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_SERVICING * data.FUEL_PRICE
    return cost


def calculate_charter_cost(vessel, start_time, end_time):
    return data.SPOT_RATE * disc_to_exact_hours(end_time - start_time) if vessel.is_spot_vessel() else 0.0


def get_fuel_consumption(distance, speed, weather):
    return (distance / (speed - data.SPEED_IMPACTS[weather])) \
           * data.FUEL_CONSUMPTION_DESIGN_SPEED * math.pow((speed / data.DESIGN_SPEED), 3)


def print_arc_info(start_node, end_node, distance, start_time, early, late, service, checkpoints, verbose):
    if verbose:
        print(f'Legal arc: {start_node} -> {end_node} {end_node.get_installation().get_opening_and_closing_hours()} | '
              f'Distance: {distance} | Departure: {start_time} | '
              f'Arrival span: {early} -> {late} | Service duration: {service} | '
              f'Checkpoints (A, I, S): {checkpoints}')


def disc_to_current_hour(disc_time):
    return math.floor(disc_time / data.TIME_UNITS_PER_HOUR)


def disc_to_exact_hours(disc_time):
    return disc_time / data.TIME_UNITS_PER_HOUR


def disc_to_daytime(disc_time):
    return hour_to_daytime(disc_to_current_hour(disc_time))


def disc_to_disc_daytime(disc_time):
    return disc_time % (24 * data.TIME_UNITS_PER_HOUR)


def hour_to_disc(hourly_time):
    return hourly_time * data.TIME_UNITS_PER_HOUR


def hour_to_daytime(hourly_time):
    return hourly_time % 24


def get_disc_time_interval(start_hour, end_hour):
    start_time_disc = hour_to_disc(start_hour) - 1
    end_time_disc = hour_to_disc(end_hour) - 1
    return [disc_time for disc_time in range(start_time_disc, end_time_disc + 1)]


def get_time_in_each_weather_state(start_time, end_time):
    return [get_time_in_weather_state(start_time, end_time, ws) for ws in range(data.WORST_WEATHER_STATE + 1)]


def get_time_in_weather_state(start_time, end_time, weather_state):
    curr_time = start_time
    time_spent_in_weather_state = 0
    while curr_time < end_time:
        if weather_state == data.WEATHER_FORECAST_DISC[curr_time]:
            time_spent_in_weather_state += 1
        curr_time += 1
    return disc_to_exact_hours(time_spent_in_weather_state)


""" -------------------------- OLD -------------------------- """


def calculate_fuel_cost_sailing(start_time, arrival_time, distance):
    if distance == 0 or start_time == arrival_time:
        return 0
    time_in_each_ws = get_time_in_each_weather_state(start_time, arrival_time)
    speed = distance / disc_to_exact_hours(arrival_time - start_time)
    distance_in_each_ws = [speed * time_in_each_ws[ws] for ws in range(4)]
    max_speed_ws2, max_speed_ws3 = data.MAX_SPEED - data.SPEED_IMPACTS[-2], data.MAX_SPEED - data.SPEED_IMPACTS[-1]
    penalty_speed = 0
    if speed > max_speed_ws2:
        penalty_speed += (time_in_each_ws[-2] * (speed - max_speed_ws2)) / sum(time_in_each_ws[:-2])
    if speed > max_speed_ws3:
        penalty_speed += (time_in_each_ws[-1] * (speed - max_speed_ws3)) / sum(time_in_each_ws[:-1])
    consumption = get_fuel_consumption(distance_in_each_ws[0] + distance_in_each_ws[1], speed + penalty_speed, 0) \
                  + get_fuel_consumption(distance_in_each_ws[2], min(speed, max_speed_ws2), 2) \
                  + get_fuel_consumption(distance_in_each_ws[3], min(speed, max_speed_ws3), 3)
    return consumption * data.FUEL_PRICE


def calculate_total_fuel_cost(start_time, checkpoints, distance):
    sail_cost = calculate_fuel_cost_sailing(start_time, checkpoints[0], distance)
    idle_cost = calculate_fuel_cost_idling(checkpoints[0], checkpoints[1])
    service_cost = calculate_fuel_cost_servicing(checkpoints[1], checkpoints[2])
    total_cost = sail_cost + idle_cost + service_cost
    return total_cost


def calculate_arc_cost(start_time, end_time, checkpoints, distance, vessel):
    return calculate_total_fuel_cost(start_time, checkpoints, distance), \
           calculate_charter_cost(vessel, start_time, end_time)


def calculate_arc_data(start_time, checkpoints, distance, vessel):
    arc_costs, arc_end_times, arc_arr_times = [], [], []
    for checkpoint in checkpoints:
        fuel_cost, charter_cost = calculate_arc_cost(start_time, checkpoint[-1], checkpoint, distance, vessel)
        arc_costs.append((fuel_cost, charter_cost, fuel_cost + charter_cost + 0.00000002))
        arc_end_times.append(checkpoint[-1])
        arc_arr_times.append(checkpoint[0])
    return arc_end_times, arc_costs, arc_arr_times


def get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel):
    if end_node.is_end_depot():
        return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR - 1
        return [(at, at, at) for at in range(early_arrival, late_arrival + 1) if at <= return_time], False
    else:
        checkpoints = get_no_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
        if checkpoints:
            return checkpoints, False
        checkpoints = get_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
        if checkpoints:
            return checkpoints, True
        return None, None


def get_no_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel):
    checkpoints = []
    for arrival_time in range(early_arrival, late_arrival + 1):
        if not is_return_possible(end_node, arrival_time + service_duration, vessel):
            break
        if is_servicing_possible(arrival_time, service_duration, end_node):
            checkpoints.append((arrival_time, arrival_time, arrival_time + service_duration))
    return checkpoints


def get_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel):
    checkpoints = []
    for arrival_time in range(early_arrival, late_arrival + 1):
        service_start_time = arrival_time
        if service_start_time >= vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR:
            break
        while not is_servicing_possible(service_start_time, service_duration, end_node):
            service_start_time += 1
        if not is_return_possible(end_node, service_start_time + service_duration, vessel):
            break
        checkpoints.append((arrival_time, service_start_time, service_start_time + service_duration))
    return checkpoints


def get_intermediate_checkpoints(start_node, end_node, start_time, vessel):
    distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
    early_arrival, late_arrival = get_arrival_time_span(distance, start_time)
    service_duration = calculate_service_time(end_node)
    checkpoints, idling = get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
    return checkpoints, idling


def get_internal_checkpoints(end_node, start_time, vessel):
    service_duration = calculate_service_time(end_node)
    end_time = start_time + service_duration
    if is_return_possible(end_node, end_time, vessel) and is_servicing_possible(start_time, service_duration, end_node):
        return [(start_time, start_time, end_time)], False
    else:
        return None, False


def get_arrival_time_span(distance, departure_time):
    max_sailing_duration = hour_to_disc(distance / data.MIN_SPEED)
    min_sailing_duration = hour_to_disc(distance / data.MAX_SPEED)
    if math.floor(min_sailing_duration) == math.floor(max_sailing_duration):
        sailing_duration = math.floor(max_sailing_duration)
        max_distance = sailing_duration * data.MAX_DISTANCE_UNIT
        if max_distance < distance:
            return departure_time, departure_time
    min_sailing_duration = math.ceil(min_sailing_duration)
    max_sailing_duration = math.floor(max_sailing_duration)
    return departure_time + min_sailing_duration, departure_time + max_sailing_duration


def generate_visit_list():
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
    return visit_list


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
    ordered_internal_nodes = []
    for node in [md_node, od_node, op_node]:
        if node:
            ordered_internal_nodes.append(node)
    return ordered_internal_nodes
