import data
import math


def is_illegal_arc(start_node, end_node):
    if start_node.is_start_depot():
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


def get_arrival_time_span(distance, departure_time):
    max_sailing_duration = math.floor(distance / data.MIN_SPEED_DISC)
    latest_arrival_time = departure_time + max_sailing_duration

    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[departure_time:latest_arrival_time + 1]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]

    sailed_distance, min_sailing_duration = 0, 0
    while sailed_distance < distance:
        sailed_distance += adjusted_max_speeds[min_sailing_duration] * data.TIME_UNIT_DISC
        min_sailing_duration += 1

    earliest_arrival_time = departure_time + min_sailing_duration

    return earliest_arrival_time, latest_arrival_time


def calculate_service_time(to_node):
    return 0 if to_node.is_end_depot() else math.ceil(to_node.get_order().get_size() * data.UNIT_SERVICE_TIME_DISC)


def get_checkpoints(early_arrival, late_arrival, service_duration, end_node):
    if end_node.is_end_depot():
        return [(at, at, at) for at in range(early_arrival, late_arrival + 1)], False
    else:
        checkpoints = get_no_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node)
        if checkpoints:
            return checkpoints, False
        checkpoints = get_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node)
        return checkpoints, True


def get_no_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node):
    checkpoints = []
    for arrival_time in range(early_arrival, late_arrival + 1):
        checkpoint = get_checkpoint(arrival_time, arrival_time, service_duration, end_node)
        if checkpoint:
            checkpoints.append(checkpoint)
    return checkpoints


def get_idling_checkpoints(early_arrival, late_arrival, service_duration, end_node):
    checkpoints = []
    for arrival_time in range(early_arrival, late_arrival + 1):
        service_start_time = arrival_time
        checkpoint = get_checkpoint(arrival_time, service_start_time, service_duration, end_node)
        while not checkpoint:
            service_start_time += 1
            checkpoint = get_checkpoint(arrival_time, service_start_time, service_duration, end_node)
        checkpoints.append(checkpoint)
    return checkpoints


def get_checkpoint(arrival_time, service_start_time, service_duration, end_node):
    worst_weather = max(data.WEATHER_FORECAST_DISC[service_start_time:service_start_time + service_duration])

    opening_hour, closing_hour = end_node.get_installation().get_opening_and_closing_hours()
    disc_opening_time, disc_closing_time = hour_to_disc(opening_hour), hour_to_disc(closing_hour)

    installation_open = True
    if disc_opening_time != 0 and disc_closing_time != data.TIME_UNITS_24:
        start_daytime = disc_to_disc_daytime(service_start_time)
        end_daytime = disc_to_disc_daytime(service_start_time + service_duration)
        if start_daytime > disc_closing_time or start_daytime < disc_opening_time or \
                end_daytime > disc_closing_time or end_daytime < disc_opening_time:
            installation_open = False

    if installation_open and worst_weather < data.WORST_WEATHER_STATE:
        return arrival_time, service_start_time, service_start_time + service_duration
    else:
        return None


def calculate_arc_data(start_time, checkpoints, distance, vessel):
    arc_costs, arc_end_times, arc_speeds = [], [], []
    for checkpoint in checkpoints:
        arc_cost = calculate_arc_cost(start_time, checkpoint[-1], checkpoint, distance, vessel)
        arc_costs.append(arc_cost)
        arc_end_times.append(checkpoint[-1])
        duration = disc_to_exact_hours(checkpoint[0] - start_time)
        arc_speeds.append(distance/duration if duration > 0 else 0)
    return arc_costs, arc_end_times, arc_speeds


def calculate_arc_cost(start_time, end_time, checkpoints, distance, vessel):
    return calculate_total_fuel_cost(start_time, checkpoints, distance) \
           + calculate_charter_cost(vessel, start_time, end_time) + 0.00001  # TODO: Find out effect of this


def calculate_total_fuel_cost(start_time, checkpoints, distance):
    sail_cost = calculate_fuel_cost_sailing(start_time, checkpoints[0], distance)
    idle_cost = calculate_fuel_cost_idling(checkpoints[0], checkpoints[1])
    service_cost = calculate_fuel_cost_servicing(checkpoints[1], checkpoints[2])
    total_cost = sail_cost + idle_cost + service_cost
    return total_cost


def calculate_fuel_cost_sailing(start_time, arrival_time, distance):
    if distance == 0:
        return 0
    time_in_each_ws = get_time_in_each_weather_state(start_time, arrival_time)
    speed = distance / disc_to_exact_hours(arrival_time - start_time)
    max_speed_ws2, max_speed_ws3 = data.MAX_SPEED - data.SPEED_IMPACTS[-2], data.MAX_SPEED - data.SPEED_IMPACTS[-1]

    penalty_speed = 0
    if speed > max_speed_ws2:
        penalty_speed += (time_in_each_ws[-2] * (speed - max_speed_ws2)) / sum(time_in_each_ws[:-2])
    if speed > max_speed_ws3:
        penalty_speed += (time_in_each_ws[-1] * (speed - max_speed_ws3)) / sum(time_in_each_ws[:-1])

    consumption = (time_in_each_ws[0] + time_in_each_ws[1]) * get_consumption(speed + penalty_speed) \
                  + time_in_each_ws[2] * get_consumption(min(speed + data.SPEED_IMPACTS[2], data.MAX_SPEED)) \
                  + time_in_each_ws[3] * get_consumption(min(speed + data.SPEED_IMPACTS[3], data.MAX_SPEED))

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
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_DEPOT * data.FUEL_PRICE
    return cost


def calculate_charter_cost(vessel, start_time, end_time):
    return data.SPOT_RATE * disc_to_exact_hours(end_time - start_time) if vessel.is_spot_vessel() else 0.0


def get_consumption(speed):
    return 11.111 * speed * speed - 177.78 * speed + 1011.1


# TODO: This could be solved by modifing the arrival time interval instead
# TODO: This must be verified for a case where return is not possible for certain arcs
def is_return_possible(end_node, arc_end_time, vessel):
    distance = end_node.get_installation().get_distance_to_installation(data.DEPOT)

    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[arc_end_time:]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]

    sailed_distance, min_sailing_duration = 0, 0
    while sailed_distance < distance:
        sailed_distance += adjusted_max_speeds[min_sailing_duration] * data.TIME_UNIT_DISC
        min_sailing_duration += 1

    earliest_arrival_time = arc_end_time + min_sailing_duration
    return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR

    return earliest_arrival_time <= return_time


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
    start_time_disc = hour_to_disc(start_hour)
    end_time_disc = hour_to_disc(end_hour)
    return [disc_time for disc_time in range(start_time_disc, end_time_disc)]


def get_time_in_each_weather_state(start_time, end_time):
    return [get_time_in_weather_state(start_time, end_time, ws) for ws in range(data.WORST_WEATHER_STATE+1)]


def get_time_in_weather_state(start_time, end_time, weather_state):
    curr_time = start_time
    time_spent_in_weather_state = 0
    while curr_time < end_time:
        if weather_state == data.WEATHER_FORECAST_DISC[curr_time]:
            time_spent_in_weather_state += 1
        curr_time += 1
    return disc_to_exact_hours(time_spent_in_weather_state)
