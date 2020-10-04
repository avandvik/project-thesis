import json
import math
from objects.installation import Installation
from objects.vessel import Vessel
from objects.order import Order

file_path = 'data/mongstad.json'

with open(file_path) as file:
    input_data = json.load(file)

""" ============================ INSTALLATIONS ============================ """
installations = []
for installation_name in input_data['installations']:
    installations.append(Installation(identifier=input_data['installations'][installation_name]['id'],
                                      name=installation_name,
                                      opening_hour=input_data['installations'][installation_name]['opening_hour'],
                                      closing_hour=input_data['installations'][installation_name]['closing_hour'],
                                      standard_order_size=input_data['installations'][installation_name][
                                          'standard_order_size'],
                                      distances=input_data['installations'][installation_name][
                                          'distances_to_other_installations']))

""" ============================ VESSEL ============================ """
vessels = []
for vessel_name in input_data['vessels']:
    vessels.append(Vessel(identifier=input_data['vessels'][vessel_name]['id'],
                          name=vessel_name,
                          return_day=input_data['vessels'][vessel_name]['return_day'],
                          deck_capacity=input_data['vessels'][vessel_name]['deck_capacity'],
                          bulk_capacity=input_data['vessels'][vessel_name]['bulk_capacity'],
                          is_spot_vessel=input_data['vessels'][vessel_name]['is_spot_vessel']))

MIN_SPEED = input_data['min_speed']
MAX_SPEED = input_data['max_speed']

FUEL_PRICE = input_data['fuel_price']
FUEL_CONSUMPTION_DP = input_data['fuel_consumption_dp']  # TODO: Find out if this is fuel consumption at DEPOT
FUEL_CONSUMPTION_IDLING = input_data['fuel_consumption_idling']

SPOT_HOUR_RATE = input_data['spot_hour_rate']

TIME_PER_UNIT_DEMAND = input_data['time_per_unit_demand']  # TODO: Find out what this is and rename

""" ============================ ORDERS ============================ """
orders = []
order_size_variations = input_data['order_size_variations']
for order_identfifier in input_data['orders']:
    variation_idx = input_data['orders'][order_identfifier]['size_variation'] - 1
    order_size_variation = order_size_variations[variation_idx]
    installation_idx = input_data['orders'][order_identfifier]['installation']
    installation = installations[installation_idx]
    orders.append(Order(identifier=order_identfifier,
                        transport_type=input_data['orders'][order_identfifier]['transport_type'],
                        cargo_type=input_data['orders'][order_identfifier]['cargo_type'],
                        mandatory=input_data['orders'][order_identfifier]['mandatory'],
                        size=math.floor(installation.get_standard_order_size() * order_size_variation),
                        deadline=input_data['orders'][order_identfifier]['deadline_day'],
                        departure_day=0,
                        installation=installation))

""" ============================ TIME AND DISCRETIZATION ============================ """
PLANNING_PERIOD_IN_HOURS = input_data['planning_period_in_hours']
TIME_UNITS_PER_HOUR = input_data['time_units_per_hour']


""" ============================ WEATHER ============================ """
WEATHER_FORECAST = input_data['weather_forecast']
SPEED_IMPACTS = [input_data['weather_states'][weather_state]['speed_impact'] for weather_state in
                 input_data['weather_states']]
SERVICE_IMPACTS = [input_data['weather_states'][weather_state]['service_impact'] for weather_state in
                   input_data['weather_states']]
