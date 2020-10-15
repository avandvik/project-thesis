import json
import math
from objects.installation import Installation
from objects.vessel import Vessel
from objects.order import Order

file_path = 'data/mongstad/3.json'

with open(file_path) as file:
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

UNIT_SERVICE_TIME_HOUR = input_data['real_service_time_per_unit']

""" ============================ VESSEL ============================ """
VESSELS = []
for index, vessel_name in enumerate(input_data['vessels']):
    is_spot_vessel = True if input_data['vessels'][vessel_name]['is_spot_vessel'] == 'True' else False
    VESSELS.append(Vessel(index=index,
                          name=vessel_name,
                          return_day=input_data['vessels'][vessel_name]['return_day'],
                          deck_capacity=input_data['vessels'][vessel_name]['deck_capacity'],
                          bulk_capacity=input_data['vessels'][vessel_name]['bulk_capacity'],
                          is_spot_vessel=is_spot_vessel))

MIN_SPEED = input_data['min_speed']
MAX_SPEED = input_data['max_speed']
FUEL_PRICE = input_data['fuel_price']
FUEL_CONSUMPTION_DEPOT = input_data['fuel_consumption_depot']
FUEL_CONSUMPTION_IDLING = input_data['fuel_consumption_idling']
SPOT_HOUR_RATE = input_data['spot_hour_rate']

""" ============================ ORDERS ============================ """
ORDERS = []
for index, order_identfifier in enumerate(input_data['orders']):
    installation_idx = input_data['orders'][order_identfifier]['installation']
    installation = INSTALLATIONS[installation_idx]
    order = Order(index=index,
                  transport_type=input_data['orders'][order_identfifier]['transport_type'],
                  cargo_type=input_data['orders'][order_identfifier]['cargo_type'],
                  mandatory=True if input_data['orders'][order_identfifier]['mandatory'] == 'True' else False,
                  size=input_data['orders'][order_identfifier]['size'],
                  deadline=input_data['orders'][order_identfifier]['deadline_day'],
                  departure_day=0,
                  installation=installation)
    ORDERS.append(order)
    installation.add_order(order)

""" ============================ TIME AND DISCRETIZATION ============================ """
PERIOD_HOURS = input_data['planning_period_in_hours']
TIME_UNITS_PER_HOUR = input_data['time_units_per_hour']
PERIOD_DISC = PERIOD_HOURS * TIME_UNITS_PER_HOUR

DISCRETIZED_TIME_UNIT = 1.0 / TIME_UNITS_PER_HOUR
UNIT_MINUTES = 60 / TIME_UNITS_PER_HOUR
UNIT_SERVICE_TIME_DISC = UNIT_SERVICE_TIME_HOUR * TIME_UNITS_PER_HOUR

""" ============================ WEATHER ============================ """
WEATHER_FORECAST_HOURS = input_data['weather_forecast']
WEATHER_FORECAST_DISC = [WEATHER_FORECAST_HOURS[math.floor(i/4)] for i in range(PERIOD_DISC)]
BEST_WEATHER_STATE = input_data['best_possible_weather_state']
WORST_WEATHER_STATE = input_data['worst_possible_weather_state']
SPEED_IMPACTS = [input_data['weather_states'][weather_state]['speed_impact'] for weather_state in
                 input_data['weather_states']]
SERVICE_IMPACTS = [input_data['weather_states'][weather_state]['service_impact'] for weather_state in
                   input_data['weather_states']]
