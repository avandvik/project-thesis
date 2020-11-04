import math
import data
import helpers as hlp
from collections import defaultdict as dd


class ArcGenerator:

    def __init__(self, preparation_end_time, verbose):
        # nodes[vessel][node][time]
        self.nodes = dd(lambda: dd(lambda: dd(lambda: False)))

        # arc_costs[vessel][from_node][start_time][to_node][end_time]
        self.arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

        self.preparation_end_time = preparation_end_time
        self.verbose = verbose
        self.number_of_arcs = 0

    def generate_arcs(self):

        # TODO: Move this to for loop below?
        for vessel in data.VESSELS:
            self.nodes[vessel.get_index()][0][self.preparation_end_time] = True

        for vessel in data.VESSELS:
            discretized_return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR
            explored_nodes = []
            for arc_start_time in range(self.preparation_end_time, discretized_return_time):
                for from_node in data.ALL_NODES[:-1]:
                    if self.is_valid_start_node(vessel, from_node, arc_start_time):
                        self.generate_arcs_from_node(vessel, from_node, arc_start_time, explored_nodes)

        print(f'Arc generation done! Number of arcs: {self.number_of_arcs}')

    def is_valid_start_node(self, vessel, from_node, arc_start_time):
        if arc_start_time != self.preparation_end_time and from_node.is_start_depot():
            return False
        if not self.nodes[vessel.get_index()][from_node.get_index()][arc_start_time]:
            return False
        return True

    def generate_arcs_from_node(self, vessel, from_node, arc_start_time, explored_nodes):
        for to_node in data.ALL_NODES[1:]:
            explored_nodes.append(from_node)
            if from_node.get_index() == to_node.get_index() or is_illegal_arc(from_node, to_node, explored_nodes):
                continue

            distance = from_node.get_installation().get_distance_to_installation(to_node.get_installation())
            earliest_arrival_time, latest_arrival_time = get_arrival_time_span(distance, arc_start_time)
            service_duration = calculate_service_time(to_node)

            # Checkpoints are in the form of (arrival time, idling end time/service start time, service end time)
            checkpoints = get_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration, to_node)

            idling_performed = False

            if not checkpoints:
                checkpoints = get_all_idling_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration,
                                                         to_node)
                idling_performed = True

            print_arc_info(from_node, to_node, distance, arc_start_time, earliest_arrival_time,
                           latest_arrival_time, service_duration, checkpoints, self.verbose)

            arc_costs, arc_end_times = calculate_arc_costs_and_end_times(arc_start_time, checkpoints, distance, vessel)

            if to_node.is_end_depot():
                self.add_end_depot_node_and_arc(from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel)
            elif idling_performed:
                self.add_best_idling_arc(from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel)
            else:
                self.add_nodes_and_arcs(from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel)

            if self.verbose:
                print()

    def add_end_depot_node_and_arc(self, from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel):
        return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR
        feasible_return_arcs = [(ac, aet) for ac, aet in zip(arc_costs, arc_end_times) if aet <= return_time]
        best_return_arc = min(feasible_return_arcs)
        arc_cost, arc_end_time = best_return_arc
        self.save_node_and_arc(from_node, to_node, arc_cost, arc_start_time, arc_end_time, vessel)

    def add_best_idling_arc(self, from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel):
        arcs = [(ac, aet) for ac, aet in zip(arc_costs, arc_end_times) if is_return_possible(to_node, aet, vessel)]
        best_arc = min(arcs)
        arc_cost, arc_end_time = best_arc
        self.save_node_and_arc(from_node, to_node, arc_cost, arc_start_time, arc_end_time, vessel)

    def add_nodes_and_arcs(self, from_node, to_node, arc_costs, arc_start_time, arc_end_times, vessel):
        for arc_cost, arc_end_time in zip(arc_costs, arc_end_times):
            if is_return_possible(to_node, arc_end_time, vessel):
                self.save_node_and_arc(from_node, to_node, arc_cost, arc_start_time, arc_end_time, vessel)

    def save_node_and_arc(self, fn, tn, ac, ast, aet, v):
        if self.verbose:
            print(f'\tAdding arc: {ast} -> {aet} ({ac}) ')
        self.nodes[v.get_index()][tn.get_index()][aet] = True
        self.arc_costs[v.get_index()][fn.get_index()][ast][tn.get_index()][aet] = ac
        self.number_of_arcs += 1

    def get_nodes(self):
        return self.nodes

    def get_arc_costs(self):
        return self.arc_costs


# TODO: This could be solved by modifing the arrival time interval instead
# TODO: This must be verified for a case where return is not possible for certain arcs
def is_return_possible(to_node, arc_end_time, vessel):
    distance = to_node.get_installation().get_distance_to_installation(data.DEPOT)

    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[arc_end_time:]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]

    sailed_distance, min_sailing_duration = 0, 0
    while sailed_distance < distance:
        sailed_distance += adjusted_max_speeds[min_sailing_duration] * data.TIME_UNIT_DISC
        min_sailing_duration += 1

    earliest_arrival_time = arc_end_time + min_sailing_duration
    return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR

    return earliest_arrival_time <= return_time


def is_illegal_arc(from_node, to_node, explored_nodes):
    if to_node in explored_nodes:
        return True
    if from_node.is_start_depot():
        return False
    if from_node.get_installation() != to_node.get_installation():
        if to_node.get_installation().has_mandatory_order() and to_node.get_order().is_optional():
            return True
        elif to_node.get_installation().has_optional_delivery_order() and to_node.get_order().is_optional_pickup():
            return True
    else:
        if from_node.get_order().is_optional_delivery():
            if to_node.get_order().is_mandatory_delivery():
                return True
        elif from_node.get_order().is_optional_pickup():
            return True
    return False


def get_arrival_time_span(distance, departure_time):
    max_sailing_duration = math.ceil(distance / data.MIN_SPEED_DISC)  # TODO: Consider floor
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


def get_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration, to_node):
    opening_hours = to_node.get_installation().get_opening_hours_as_list()
    checkpoints = []
    for service_start_time in range(earliest_arrival_time, latest_arrival_time + 1):
        if to_node.is_end_depot():
            checkpoints.append((service_start_time, service_start_time, service_start_time))
        else:
            add_checkpoint(service_start_time, service_start_time, service_duration, opening_hours, checkpoints)
    return checkpoints


def get_one_idling_checkpoint(latest_arrival_time, service_duration, to_node):
    opening_hours = to_node.get_installation().get_opening_hours_as_list()
    service_start_time = latest_arrival_time
    checkpoints = []
    while not checkpoints:
        service_start_time += 1
        add_checkpoint(latest_arrival_time, service_start_time, service_duration, opening_hours, checkpoints)
    return checkpoints


def get_all_idling_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration, to_node):
    opening_hours = to_node.get_installation().get_opening_hours_as_list()
    all_checkpoints = []
    for arrival_time in range(earliest_arrival_time, latest_arrival_time + 1):
        checkpoints = []
        service_start_time = arrival_time
        while not checkpoints:
            service_start_time += 1
            add_checkpoint(arrival_time, service_start_time, service_duration, opening_hours, checkpoints)
        all_checkpoints.append(checkpoints[0])
    return all_checkpoints


def add_checkpoint(arrival_time, service_start_time, service_duration, opening_hours, checkpoints):
    worst_weather = max(data.WEATHER_FORECAST_DISC[service_start_time:service_start_time + service_duration])
    start_daytime = hlp.disc_to_daytime(service_start_time)
    end_daytime = hlp.disc_to_daytime(service_start_time + service_duration)
    start_idx = opening_hours.index(start_daytime) if start_daytime in opening_hours else 100000
    end_idx = opening_hours.index(end_daytime) if end_daytime in opening_hours else -100000
    installation_open = start_idx < end_idx
    if installation_open and worst_weather < data.WORST_WEATHER_STATE:
        checkpoints.append((arrival_time, service_start_time, service_start_time + service_duration))


def calculate_arc_costs_and_end_times(arc_start_time, checkpoints, distance, vessel):
    arc_costs, arc_end_times = [], []
    for checkpoint in checkpoints:
        arc_cost = calculate_arc_cost(arc_start_time, checkpoint[-1], checkpoint, distance, vessel)
        arc_costs.append(arc_cost)
        arc_end_times.append(checkpoint[-1])
    return arc_costs, arc_end_times


def calculate_arc_cost(arc_start_time, arc_end_time, checkpoints, distance, vessel):
    return calculate_total_fuel_cost(arc_start_time, checkpoints, distance) \
           + calculate_charter_cost(vessel, arc_start_time, arc_end_time) + 0.00001  # TODO: Find out effect of this


def calculate_total_fuel_cost(departure_time, checkpoints, distance):
    sail_cost = calculate_fuel_cost_sailing(departure_time, checkpoints[0], distance)
    idle_cost = calculate_fuel_cost_idling(checkpoints[0], checkpoints[1])
    service_cost = calculate_fuel_cost_servicing(checkpoints[1], checkpoints[2])
    total_cost = sail_cost + idle_cost + service_cost
    return total_cost


def calculate_fuel_cost_sailing(departure_time, arrival_time, distance):
    if distance == 0:
        return 0
    time_in_each_ws = hlp.get_time_in_each_weather_state(departure_time, arrival_time)
    speed = distance / hlp.disc_to_exact_hours(arrival_time - departure_time)
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
    time_in_each_ws = hlp.get_time_in_each_weather_state(idling_start_time, idling_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_IDLING * data.FUEL_PRICE
    return cost


def calculate_fuel_cost_servicing(servicing_start_time, servicing_end_time):
    time_in_each_ws = hlp.get_time_in_each_weather_state(servicing_start_time, servicing_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_DEPOT * data.FUEL_PRICE
    return cost


def calculate_charter_cost(vessel, start_time, end_time):
    return data.SPOT_RATE * hlp.disc_to_exact_hours(end_time - start_time) if vessel.is_spot_vessel() else 0.0


def get_consumption(speed):
    return 11.111 * speed * speed - 177.78 * speed + 1011.1


def print_arc_info(from_node, to_node, distance, start_time, early, late, service, checkpoints, verbose):
    if verbose:
        print(f'Legal arc: {from_node} -> {to_node} | Distance: {distance} | Departure: {start_time} | '
              f'Arrival span: {early} -> {late} | Service duration: {service} | '
              f'Checkpoints (A, I, S): {checkpoints}')


ag = ArcGenerator(16 * data.TIME_UNITS_PER_HOUR - 1, True)
ag.generate_arcs()
