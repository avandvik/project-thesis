import math
import data
import helpers as hlp
from collections import defaultdict as dd


class ArcGenerator:

    def __init__(self, preparation_end_time, verbose):
        # nodes[vessel][node][time] -> True/False
        self.nodes = dd(lambda: dd(lambda: dd(lambda: False)))

        # arc_costs[vessel][start_node][start_time][end_node][end_times] -> arc cost
        self.arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

        # node_time_points[vessel][node] -> time
        self.node_time_points = [[[] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # start_nodes[vessel][end_node][end_time] -> start_node
        self.start_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # end_nodes[vessel][start_node][start_time] -> end_node
        self.end_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # start_times[vessel][start_node][end_node] -> start_time
        self.start_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # end_times[vessel][start_node][end_node] -> end_time
        self.end_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # specific_start_times[vessel][start_node][end_node][end_times] -> start_time
        self.specific_start_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                                      for _ in data.ALL_NODES] for _ in data.VESSELS]

        # specific_end_times[vessel][start_node][end_node][start_time] -> end_time
        self.specific_end_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                                    for _ in data.ALL_NODES] for _ in data.VESSELS]

        self.preparation_end_time = preparation_end_time
        self.verbose = verbose
        self.number_of_arcs = 0

    def generate_arcs(self):
        for vessel in data.VESSELS:
            self.nodes[vessel.get_index()][0][self.preparation_end_time] = True
            self.node_time_points[vessel.get_index()][0].append(self.preparation_end_time)
            for start_node in data.ALL_NODES[:-1]:
                for end_node in data.ALL_NODES[1:]:
                    if is_illegal_arc(start_node, end_node):
                        continue

                    discretized_return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR

                    for start_time in range(self.preparation_end_time, discretized_return_time):
                        if self.is_valid_start_node(vessel, start_node, start_time, end_node):
                            self.generate_arcs_from_node(vessel, start_node, start_time, end_node)

        print(f'Arc generation done!\nTotal number of arcs: {self.number_of_arcs}\n'
              f'Arcs per vessel: {int(self.number_of_arcs / len(data.VESSELS))}')

    def generate_arcs_from_node(self, vessel, start_node, start_time, end_node):
        distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
        early_arrival, late_arrival = get_arrival_time_span(distance, start_time)
        service_duration = calculate_service_time(end_node)

        # Checkpoints are in the form of (arrival time, idling end time/service start time, service end time)
        checkpoints, idling = get_checkpoints(early_arrival, late_arrival, service_duration, end_node)

        print_arc_info(start_node, end_node, distance, start_time, early_arrival,
                       late_arrival, service_duration, checkpoints, self.verbose)

        arc_costs, arc_end_times = calculate_arc_costs_and_end_times(start_time, checkpoints, distance, vessel)

        if end_node.is_end_depot():
            self.add_end_depot_node_and_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel)
        elif idling:
            self.add_best_idling_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel)
        else:
            self.add_nodes_and_arcs(start_node, end_node, arc_costs, start_time, arc_end_times, vessel)

        if self.verbose:
            print()

    def is_valid_start_node(self, vessel, start_node, start_time, end_node):
        if start_time != self.preparation_end_time and start_node.is_start_depot():
            return False
        if not self.nodes[vessel.get_index()][start_node.get_index()][start_time]:
            return False

        for time in range(self.preparation_end_time, start_time):
            if start_node.get_index() in self.end_nodes[vessel.get_index()][end_node.get_index()][time]:
                return False

        return True

    def add_end_depot_node_and_arc(self, start_node, end_node, arc_costs, start_time, end_times, vessel):
        return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR
        feasible_return_arcs = [(ac, aet) for ac, aet in zip(arc_costs, end_times) if aet <= return_time]
        if feasible_return_arcs:
            best_return_arc = min(feasible_return_arcs)
            arc_cost, arc_end_time = best_return_arc
            self.update_sets(start_node, end_node, arc_cost, start_time, arc_end_time, vessel)

    def add_best_idling_arc(self, start_node, end_node, arc_costs, start_time, end_times, vessel):
        arcs = [(ac, aet) for ac, aet in zip(arc_costs, end_times) if is_return_possible(end_node, aet, vessel)]
        if arcs:
            best_arc = min(arcs)
            arc_cost, arc_end_time = best_arc
            self.update_sets(start_node, end_node, arc_cost, start_time, arc_end_time, vessel)

    def add_nodes_and_arcs(self, start_node, end_node, arc_costs, start_time, end_time, vessel):
        for arc_cost, arc_end_time in zip(arc_costs, end_time):
            if is_return_possible(end_node, arc_end_time, vessel):
                self.update_sets(start_node, end_node, arc_cost, start_time, arc_end_time, vessel)

    def update_sets(self, sn, en, ac, ast, aet, v):
        if self.verbose:
            print(f'\tAdding arc: {ast} -> {aet} ({ac}) ')

        self.nodes[v.get_index()][en.get_index()][aet] = True
        self.arc_costs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = ac
        self.number_of_arcs += 1

        if aet not in self.node_time_points[v.get_index()][en.get_index()]:
            self.node_time_points[v.get_index()][en.get_index()].append(aet)
        if sn.get_index() not in self.start_nodes[v.get_index()][en.get_index()][aet]:
            self.start_nodes[v.get_index()][en.get_index()][aet].append(sn.get_index())
        if en.get_index() not in self.end_nodes[v.get_index()][sn.get_index()][ast]:
            self.end_nodes[v.get_index()][sn.get_index()][ast].append(en.get_index())
        if ast not in self.start_times[v.get_index()][sn.get_index()][en.get_index()]:
            self.start_times[v.get_index()][sn.get_index()][en.get_index()].append(ast)
        if aet not in self.end_times[v.get_index()][sn.get_index()][en.get_index()]:
            self.end_times[v.get_index()][sn.get_index()][en.get_index()].append(aet)
        if ast not in self.specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet]:
            self.specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet].append(ast)
        if aet not in self.specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast]:
            self.specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast].append(aet)

    def get_nodes(self):
        return self.nodes

    def get_arc_costs(self):
        return self.arc_costs

    def get_node_time_points(self):
        return self.node_time_points

    def get_start_nodes(self):
        return self.start_nodes

    def get_end_nodes(self):
        return self.end_nodes

    def get_start_times(self):
        return self.start_times

    def get_end_times(self):
        return self.end_times

    def get_specific_start_times(self):
        return self.specific_start_times

    def get_specific_end_times(self):
        return self.specific_end_times


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
    disc_opening_time, disc_closing_time = hlp.hour_to_disc(opening_hour), hlp.hour_to_disc(closing_hour)

    installation_open = True
    if disc_opening_time != 0 and disc_closing_time != data.TIME_UNITS_24:
        start_daytime = hlp.disc_to_disc_daytime(service_start_time)
        end_daytime = hlp.disc_to_disc_daytime(service_start_time + service_duration)
        if start_daytime > disc_closing_time or start_daytime < disc_opening_time or \
                end_daytime > disc_closing_time or end_daytime < disc_opening_time:
            installation_open = False

    if installation_open and worst_weather < data.WORST_WEATHER_STATE:
        return arrival_time, service_start_time, service_start_time + service_duration
    else:
        return None


def calculate_arc_costs_and_end_times(start_time, checkpoints, distance, vessel):
    arc_costs, arc_end_times = [], []
    for checkpoint in checkpoints:
        arc_cost = calculate_arc_cost(start_time, checkpoint[-1], checkpoint, distance, vessel)
        arc_costs.append(arc_cost)
        arc_end_times.append(checkpoint[-1])
    return arc_costs, arc_end_times


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
    time_in_each_ws = hlp.get_time_in_each_weather_state(start_time, arrival_time)
    speed = distance / hlp.disc_to_exact_hours(arrival_time - start_time)
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

# ag = ArcGenerator(16 * data.TIME_UNITS_PER_HOUR - 1, True)
# ag.generate_arcs()
