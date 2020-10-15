import math
import data
import helpers as hlp
from collections import defaultdict as dd
from pprint import pprint


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

    # noinspection PyMethodMayBeStatic
    def generate_arcs_from_node(self, vessel, arc_start_time, from_order):
        for to_order in data.ORDERS:
            if from_order.get_index() == to_order.get_index() or is_illegal_arc(from_order, to_order):
                continue
            distance = from_order.get_installation().get_distance_to_installation(to_order.get_installation())

            print(f'Legal arc: {from_order} -> {to_order} ({distance})')

            earliest_arrival_time, latest_arrival_time = get_arrival_time_span(distance, arc_start_time)

            print(f'\tDeparture time: {arc_start_time}')
            print(f'\tArrival span: {earliest_arrival_time} -> {latest_arrival_time}')



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

    speed_impacts = [data.SPEED_IMPACTS[w] for w in data.WEATHER_FORECAST_DISC[departure_time:latest_arrival_time + 1]]
    adjusted_max_speeds = [data.MAX_SPEED - speed_impact for speed_impact in speed_impacts]

    sailed_distance, min_sailing_duration = 0, 0
    while sailed_distance < distance:
        sailed_distance += adjusted_max_speeds[min_sailing_duration] * data.DISCRETIZED_TIME_UNIT
        min_sailing_duration += 1

    earliest_arrival_time = departure_time + min_sailing_duration

    return earliest_arrival_time, latest_arrival_time
