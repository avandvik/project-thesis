import os
import json
import math
import pathlib

from objects.installation import Installation
from objects.vessel import Vessel
from objects.order import Order
from objects.node import Node


INSTANCE_NAME = os.environ.get('INSTANCE_NAME')

PROJECT_DIR_PATH = f'{pathlib.Path(__file__).parent.absolute()}'  # Path of the root of the project
VERBOSE = False
TIME_LIMIT = 60 * 60  # Max run time of gurobi solver
INSTANCE_GROUP = 'mongstad'

FILE_PATH = f'{PROJECT_DIR_PATH}/input/{INSTANCE_GROUP}/{INSTANCE_NAME}.json'

with open(FILE_PATH) as file:
    input_data = json.load(file)

""" ============================ INSTALLATIONS ============================ """
INSTALLATIONS = []
for installation_name in input_data['installations']:
    INSTALLATIONS.append(Installation(index=input_data['installations'][installation_name]['id'],
                                      name=installation_name,
                                      opening_hour=input_data['installations'][installation_name]['opening_hour'],
                                      closing_hour=input_data['installations'][installation_name]['closing_hour'],
                                      distances=input_data['installations'][installation_name][
                                          'distances_to_other_installations']))

DEPOT = INSTALLATIONS[0]
UNIT_SERVICE_TIME_HOUR = input_data['real_service_time_per_unit']

""" ============================ VESSEL ============================ """
VESSELS = []
index = 0
for vessel_name in input_data['vessels']:
    is_spot_vessel = True if input_data['vessels'][vessel_name]['is_spot_vessel'] == 'True' else False
    return_day = input_data['vessels'][vessel_name]['return_day']
    if return_day != 0:
        VESSELS.append(Vessel(index=index,
                              name=vessel_name,
                              return_day=return_day,
                              capacity=input_data['vessels'][vessel_name]['capacity'],
                              is_spot_vessel=is_spot_vessel))
        index += 1

FUEL_PRICE = input_data['fuel_price']
SPOT_RATE = input_data['spot_hour_rate']
MIN_SPEED = input_data['min_speed']
MAX_SPEED = input_data['max_speed']
DESIGN_SPEED = input_data['design_speed']
FUEL_CONSUMPTION_DESIGN_SPEED = input_data['fuel_consumption_design_speed']
FUEL_CONSUMPTION_DEPOT = input_data['fuel_consumption_depot']
FUEL_CONSUMPTION_IDLING = input_data['fuel_consumption_idling']
FUEL_CONSUMPTION_SERVICING = input_data['fuel_consumption_servicing']

""" ============================ ORDERS ============================ """
ALL_NODES = []
ORDER_NODES = []

start_depot = Node(index=0, is_order=False, order=None, installation=DEPOT, is_start_depot=True)
ALL_NODES.append(start_depot)

for index, order_identfifier in enumerate(input_data['orders']):
    installation_idx = input_data['orders'][order_identfifier]['installation']
    installation = INSTALLATIONS[installation_idx]

    order = Order(index=index,
                  transport_type=input_data['orders'][order_identfifier]['transport_type'],
                  mandatory=True if input_data['orders'][order_identfifier]['mandatory'] == 'True' else False,
                  size=input_data['orders'][order_identfifier]['size'])

    node = Node(index=index + 1, is_order=True, order=order, installation=installation)

    ORDER_NODES.append(order)
    ALL_NODES.append(node)
    installation.add_order(order)

end_depot = Node(index=len(ALL_NODES), is_order=False, order=None, installation=DEPOT, is_start_depot=False)
ALL_NODES.append(end_depot)

ALL_NODE_INDICES = [node.get_index() for node in ALL_NODES]
MANDATORY_NODE_INDICES = [node.get_index() for node in ALL_NODES if node.is_order() and node.get_order().is_mandatory()]
OPTIONAL_NODE_INDICES = [node.get_index() for node in ALL_NODES if node.is_order() and node.get_order().is_optional()]
DELIVERY_NODE_INDICES = [node.get_index() for node in ALL_NODES if node.is_order() and node.get_order().is_delivery()]
PICKUP_NODE_INDICES = [node.get_index() for node in ALL_NODES if node.is_order() and node.get_order().is_pickup()]

""" ============================ TIME AND DISCRETIZATION ============================ """
PERIOD_HOURS = input_data['planning_period_in_hours']
TIME_UNITS_PER_HOUR = input_data['time_units_per_hour']
TIME_UNITS_24 = TIME_UNITS_PER_HOUR * 24
PERIOD_DISC = PERIOD_HOURS * TIME_UNITS_PER_HOUR
TIME_POINTS_DISC = [tp for tp in range(PERIOD_DISC)]

TIME_UNIT_DISC = 1.0 / TIME_UNITS_PER_HOUR
UNIT_SERVICE_TIME_DISC = UNIT_SERVICE_TIME_HOUR * TIME_UNITS_PER_HOUR

MIN_SPEED_DISC = MIN_SPEED * (1 / TIME_UNITS_PER_HOUR)

MAX_DISTANCE_UNIT = MAX_SPEED * TIME_UNIT_DISC

""" ============================ WEATHER ============================ """
WEATHER_FORECAST_HOURS = input_data['weather_forecast']
WEATHER_FORECAST_DISC = [WEATHER_FORECAST_HOURS[math.floor(i / TIME_UNITS_PER_HOUR)] for i in range(PERIOD_DISC)]
BEST_WEATHER_STATE = input_data['best_possible_weather_state']
WORST_WEATHER_STATE = input_data['worst_possible_weather_state']
SPEED_IMPACTS = [input_data['weather_states'][weather_state]['speed_impact'] for weather_state in
                 input_data['weather_states']]
SERVICE_IMPACTS = [input_data['weather_states'][weather_state]['service_impact'] for weather_state in
                   input_data['weather_states']]

""" ============================ INSTALLATION INFO ============================ """
INSTALLATION_ORDERING = input_data['installation_ordering']
NUMBER_OF_INSTALLATIONS_WITH_ORDERS = input_data['number_of_installations']
WEATHER_SCENARIO = input_data['weather_scenario']
FLEET_SIZE = input_data['fleet_size']
