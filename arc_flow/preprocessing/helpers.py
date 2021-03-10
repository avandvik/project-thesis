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
        fuel_cost, charter_cost = calculate_arc_cost(start_time, arr_time, service_time, end_time, speed,
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

    avg_max_speed = calculate_average_max_speed(start_time, distance)
    speeds = [float(speed) for speed in np.arange(data.MIN_SPEED, data.MAX_SPEED, 1) if speed < avg_max_speed]
    speeds.append(float(avg_max_speed))
    return speeds


def calculate_average_max_speed(start_time, distance):
    sailed_distance = 0
    current_time = start_time
    while sailed_distance < distance:
        ws = data.WEATHER_FORECAST_DISC[current_time]
        adjusted_max_speed = data.MAX_SPEED - data.SPEED_IMPACTS[ws]
        sailed_distance += adjusted_max_speed * data.TIME_UNIT_DISC
        current_time += 1
    overshoot_time = calculate_overshoot_time(sailed_distance - distance, current_time)
    return distance / disc_to_exact_hours(current_time - start_time) - overshoot_time


def calculate_overshoot_time(overshoot_distance, sailing_end_time):
    ws = data.WEATHER_FORECAST_DISC[sailing_end_time - 1]
    return overshoot_distance / (data.MAX_SPEED - data.SPEED_IMPACTS[ws])


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
            fuel_cost, charter_cost = calculate_arc_cost(start_time, arr_time, arr_time, arr_time, speed,
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
            fuel_cost, charter_cost = calculate_arc_cost(start_time, arr_time, service_time, end_time, speed,
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
        fuel_cost, charter_cost = calculate_arc_cost(start_time, arr_time, service_time, end_time, speed, distance,
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


def calculate_arc_cost(start_time, arr_time, service_time, end_time, speed, distance, vessel):
    return calculate_total_fuel_cost(start_time, arr_time, service_time, end_time, speed, distance), \
           calculate_charter_cost(vessel, start_time, end_time)


def calculate_total_fuel_cost(start_time, arr_time, service_time, end_time, speed, distance):
    sail_cost = calculate_fuel_cost_sailing(start_time, arr_time, speed, distance)
    idle_cost = calculate_fuel_cost_idling(arr_time, service_time)
    service_cost = calculate_fuel_cost_servicing(service_time, end_time)
    total_cost = sail_cost + idle_cost + service_cost
    return total_cost


def calculate_fuel_cost_sailing(start_time, arr_time, speed, distance):
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
    return [disc_to_exact_hours(get_time_in_weather_state(start_time, end_time, ws))
            for ws in range(data.WORST_WEATHER_STATE + 1)]


def get_time_in_weather_state(start_time, end_time, weather_state):
    curr_time = start_time
    time_spent_in_weather_state = 0
    while curr_time < end_time:
        if weather_state == data.WEATHER_FORECAST_DISC[curr_time]:
            time_spent_in_weather_state += 1
        curr_time += 1
    return disc_to_exact_hours(time_spent_in_weather_state)
