import math
import data
import helpers as hlp
from collections import defaultdict as dd


class ArcGenerator:

    def __init__(self):
        # nodes[vessel][time][order]
        self.nodes = dd(lambda: dd(lambda: dd(lambda: False)))

        # arc_costs[][][][][]
        self.arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

    def generate_arcs(self, preparation_end_time):

        for vessel in data.VESSELS:
            self.nodes[vessel.get_index()][preparation_end_time][0] = True

        for vessel in data.VESSELS:
            discretized_return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR
            for arc_start_time in range(preparation_end_time, discretized_return_time):
                for from_order in data.ORDERS:
                    if self.nodes[vessel.get_index()][arc_start_time][from_order.get_index()]:
                        self.generate_arcs_from_node(vessel, arc_start_time, from_order)

    def generate_arcs_from_node(self, vessel, arc_start_time, from_order):
        for to_order in data.ORDERS:
            if from_order.get_index() == to_order.get_index() or is_illegal_arc(from_order, to_order):
                continue
            distance = from_order.get_installation().get_distance_to_installation(to_order.get_installation())

            print(f'Legal arc: {from_order} -> {to_order} ({distance})')
            print(f'\tDeparture time: {arc_start_time}')

            earliest_arrival_time, latest_arrival_time = get_arrival_time_span(distance, arc_start_time)
            print(f'\tArrival span: {earliest_arrival_time} -> {latest_arrival_time}')

            service_duration = math.ceil(to_order.get_size() * data.UNIT_SERVICE_TIME_DISC)
            print(f'\tService duration: {service_duration}')

            # Checkpoints are in the form of (arrival time, idling end time, service end time)
            all_checkpoints = get_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration, to_order)
            print(f'\tCheckpoints (A, I, S): {all_checkpoints}')

            for checkpoints in all_checkpoints:
                arc_cost = calculate_total_fuel_cost(arc_start_time, checkpoints) + calculate_charter_cost()
                arc_end_time = checkpoints[-1]

                self.nodes[vessel.get_index()][arc_end_time][to_order.get_index()] = True
                self.arc_costs[vessel.get_index()][from_order.get_index()][arc_start_time][to_order.get_index()][arc_end_time] = arc_cost

        print()


def is_illegal_arc(from_order, to_order):
    if from_order.get_installation() != to_order.get_installation():  # True if we are sailing between installations
        if to_order.get_installation().has_mandatory_order() and to_order.is_optional():
            return True
        elif to_order.get_installation().has_optional_delivery_order() and to_order.is_optional() and to_order.is_pickup():
            return True
    else:
        if from_order.is_optional() and from_order.is_delivery():
            if to_order.is_mandatory() and to_order.is_delivery():
                return True
        elif from_order.is_optional() and from_order.is_pickup():
            return True


def get_arrival_time_span(distance, departure_time):
    max_sailing_duration = math.ceil(distance / data.MIN_SPEED) * data.TIME_UNITS_PER_HOUR
    latest_arrival_time = departure_time + max_sailing_duration

    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[departure_time:latest_arrival_time]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]

    sailed_distance, min_sailing_duration = 0, 0
    while sailed_distance < distance:
        sailed_distance += adjusted_max_speeds[min_sailing_duration] * data.DISCRETIZED_TIME_UNIT
        min_sailing_duration += 1

    earliest_arrival_time = departure_time + min_sailing_duration

    return earliest_arrival_time, latest_arrival_time


# TODO: Handle that return to depot has no service time, only sailing time
def get_checkpoints(earliest_arrival_time, latest_arrival_time, service_duration, to_order):
    opening_hours = to_order.get_installation().get_opening_hours_as_list()
    checkpoints = []
    for service_start_time in range(earliest_arrival_time, latest_arrival_time + 1):
        worst_weather = max(data.WEATHER_FORECAST_DISC[service_start_time:service_start_time + service_duration])
        start_time_hour = hlp.convert_discretized_time_to_time_of_day(service_start_time)
        finish_time_hour = hlp.convert_discretized_time_to_time_of_day(service_start_time + service_duration)
        start_idx = opening_hours.index(start_time_hour) if start_time_hour in opening_hours else 100
        finish_idx = opening_hours.index(finish_time_hour) if finish_time_hour in opening_hours else -100
        installation_open = start_idx < finish_idx
        if installation_open and worst_weather < data.WORST_WEATHER_STATE:
            checkpoints.append((service_start_time, service_start_time, service_start_time + service_duration))
    return checkpoints


def calculate_total_fuel_cost(departure_time, checkpoints):
    total_cost = calculate_fuel_cost_sailing(departure_time, checkpoints[0]) \
                 + calculate_fuel_cost_idling(checkpoints[0], checkpoints[1]) \
                 + calculate_fuel_cost_servicing(checkpoints[1], checkpoints[2])
    return total_cost


# TODO: Implement the sailing fuel cost estimation by Moan & Ødeskaug
def calculate_fuel_cost_sailing(departure_time, arrival_time):
    return 0


# TODO: Update to use correct weather forecast (discretized)
def calculate_fuel_cost_idling(idling_start_time, idling_end_time):
    time_in_each_ws = hlp.get_time_in_each_weather_state(idling_start_time, idling_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SPEED_IMPACTS[ws] * data.FUEL_CONSUMPTION_IDLING * data.FUEL_PRICE
    return cost


# TODO: Update to use correct weather forecast (discretized)
def calculate_fuel_cost_servicing(servicing_start_time, servicing_end_time):
    time_in_each_ws = hlp.get_time_in_each_weather_state(servicing_start_time, servicing_end_time)
    cost = 0
    for ws in range(data.WORST_WEATHER_STATE + 1):
        cost += time_in_each_ws[ws] * data.SERVICE_IMPACTS[ws] * data.FUEL_CONSUMPTION_DEPOT * data.FUEL_PRICE
    return cost


# TODO: Find out how chartering cost is actually calculated
def calculate_charter_cost():
    return 0


ag = ArcGenerator()
ag.generate_arcs(16 * data.TIME_UNITS_PER_HOUR - 1)
